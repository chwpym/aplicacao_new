import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.providers.base_provider import BaseProvider


class TSAProvider(BaseProvider):
    """
    Provedor para o catálogo da TSA do Brasil (https://www.tsadobrasil.com.br).

    Fluxo em 2 etapas:
      1. GET /resultado?q={codigo}  → encontra o link exato do produto
      2. GET /produtos/{slug}/{id}  → extrai tabela de aplicações + dados técnicos
    """

    BASE_URL = "https://www.tsadobrasil.com.br"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    # ------------------------------------------------------------------
    # Helpers de código
    # ------------------------------------------------------------------

    def _formatar_codigo_tsa(self, cod: str) -> str:
        """
        Converte 'T030006' → 'T-030006' para a URL de busca.
        Se o código já contém hífen, retorna como está (ex: 'T-030006').
        """
        cod = cod.upper().strip()
        if cod.startswith("T") and "-" not in cod and len(cod) > 1:
            return f"T-{cod[1:]}"
        return cod

    def _variacoes_codigo(self, id_peca: str) -> List[str]:
        """
        Gera variações do código para aumentar a taxa de acerto:
          - Original do usuário
          - Com prefixo T- (se não tiver T)
          - Sem hífen (normalizado)
        """
        id_peca = id_peca.upper().strip()
        variacoes = []

        # Variação formatada para TSA (T-XXXXXX)
        formatted = self._formatar_codigo_tsa(id_peca)
        if formatted not in variacoes:
            variacoes.append(formatted)

        # Original limpo
        if id_peca not in variacoes:
            variacoes.append(id_peca)

        # Se o usuário não digitou T, tenta acrescentar
        clean = id_peca.replace("-", "").replace(" ", "")
        if not clean.startswith("T") and len(clean) >= 4:
            with_t = f"T-{clean}"
            if with_t not in variacoes:
                variacoes.append(with_t)

        return variacoes

    def _parse_ano_tsa(self, ano_str: str):
        """
        Converte '2001>2005' → ('2001', '2005')
        Converte '2000>'     → ('2000', '')
        Converte '2003'      → ('2003', '')
        """
        if not ano_str:
            return "", ""
        ano_str = ano_str.strip()
        if ">" in ano_str:
            parts = ano_str.split(">", 1)
            inicio = parts[0].strip()
            fim = parts[1].strip() if len(parts) > 1 else ""
            return inicio, fim
        # Sem separador → apenas ano início
        return ano_str, ""

    # ------------------------------------------------------------------
    # Etapa 1 — Busca geral
    # ------------------------------------------------------------------

    async def _buscar_link_produto(
        self, client: httpx.AsyncClient, codigo_busca: str
    ) -> str | None:
        """
        Acessa /resultado?q={codigo} e retorna a URL exata do produto
        cujo código TSA corresponde exatamente ao buscado, ou None.
        """
        url = f"{self.BASE_URL}/resultado"
        params = {"q": codigo_busca}
        print(f"[TSA] Etapa 1 - Buscando: {url}?q={codigo_busca}")

        try:
            resp = await client.get(url, params=params, headers=self.headers)
            if resp.status_code != 200:
                print(f"[TSA] Busca retornou HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[TSA] Erro na busca: {repr(e)}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # A página de resultados exibe cards com o código TSA em destaque.
        # Estrutura: <div>T-030006</div> seguido de <a href="/produtos/...">Conheça</a>
        # Normalizamos o código para comparação (sem hífen, maiúsculo)
        codigo_normalizado = codigo_busca.replace("-", "").upper()

        # Procura todos os blocos de resultado; cada bloco tem código + link
        # O layout usa listas/divs — iteramos pelos links "Conheça"
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/produtos/" not in href:
                continue

            # O texto do código TSA fica num elemento irmão anterior ao link
            # Vamos subir na árvore para encontrar o texto do código mais próximo
            parent = link.parent
            if parent:
                parent_text = parent.get_text(separator=" ", strip=True).upper()
                # Verifica se o código buscado (sem hífen) aparece no bloco
                if codigo_normalizado in parent_text.replace("-", "").replace(" ", ""):
                    full_url = (
                        href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    )
                    print(f"[TSA] Produto encontrado: {full_url}")
                    return full_url

        print(f"[TSA] Código '{codigo_busca}' não encontrado nos resultados.")
        return None

    # ------------------------------------------------------------------
    # Etapa 2 — Detalhes do produto
    # ------------------------------------------------------------------

    async def _extrair_detalhes(
        self, client: httpx.AsyncClient, produto_url: str
    ) -> List[Dict[str, Any]]:
        """
        Acessa a página de detalhes e extrai:
          - Imagem principal
          - Referências OE (p.originalCode mark)
          - Dados técnicos (span 'Dados Técnicos' + p.compatible seguinte)
          - Observações (span 'Observações' + p.compatible seguinte)
          - Tabela de aplicações (tr → Montadora, Veículo, Modelo, Motor, Ano, Combustível)
        """
        print(f"[TSA] Etapa 2 - Detalhes: {produto_url}")
        try:
            resp = await client.get(produto_url, headers=self.headers)
            if resp.status_code != 200:
                print(f"[TSA] Detalhe retornou HTTP {resp.status_code}")
                return []
        except Exception as e:
            print(f"[TSA] Erro nos detalhes: {repr(e)}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Imagem principal ------------------------------------------
        imagem = ""
        imagens = []
        big_image_div = soup.find(id="bigImage")
        if big_image_div:
            for img_tag in big_image_div.find_all("img", src=True):
                src = img_tag["src"]
                if src:
                    if not src.startswith("http"):
                        src = f"{self.BASE_URL}{src}"
                    imagens.append(src)
            if imagens:
                imagem = imagens[0]

        # --- Referências OE (código de conversão) ----------------------
        referencias_list = []
        original_code_p = soup.find("p", class_="originalCode")
        
        # Tenta pegar an an montadora principal da página (ex: VOLKSWAGEN)
        automaker_div = soup.find(class_="nameAutomaker")
        default_brand = "ORIGINAL"
        if automaker_div:
            automaker_text = automaker_div.get_text(separator=" ", strip=True).upper()
            # Se tiver '/', pega an an primeira parte (ex: CITROEN / PEUGEOT -> CITROEN)
            default_brand = automaker_text.split("/")[0].strip()

        if original_code_p:
            current_brand = default_brand
            
            for mark in original_code_p.find_all("mark"):
                txt = mark.get_text(strip=True)
                if not txt:
                    continue
                
                # Se o texto CONTÉM dígitos, assumimos que é um código
                if any(c.isdigit() for c in txt):
                    # Formata como Marca: Código para os filtros do frontend
                    referencias_list.append(f"{current_brand}: {txt}")
                else:
                    # Se NÃO contém dígitos, é um rótulo ou marca (ex: MARELLI, VOLKSWAGEN, CONJ. BOMBA)
                    # Limpeza de ruído mas preservando nomes de componentes
                    txt_clean = txt.upper().replace("Nº", "").replace("REF.", "").strip()
                    if len(txt_clean) > 2:
                        # Se for um rótulo válido, atualiza o estado para os próximos códigos
                        current_brand = txt_clean

        referencias = " | ".join(referencias_list)

        # --- Dados Técnicos e Observações (via spans + p.compatible) ---
        dados_tecnicos = ""
        observacoes = ""

        for span in soup.find_all("span"):
            span_text = span.get_text(strip=True)
            next_p = span.find_next_sibling("p", class_="compatible")
            if not next_p:
                # Tenta encontrar o próximo p.compatible de qualquer forma
                next_elem = span.find_next("p", class_="compatible")
                if next_elem:
                    next_p = next_elem

            if next_p:
                valor = next_p.get_text(separator=" ", strip=True)
                # Remove espaços extras e BR
                valor = re.sub(r"\s+", " ", valor).strip()

                if "Dados" in span_text and "cnic" in span_text:  # "Dados Técnicos"
                    dados_tecnicos = valor
                elif "Observa" in span_text:  # "Observações"
                    observacoes = valor

        # Monta a ficha técnica básica
        ficha_tecnica: Dict[str, str] = {}
        if dados_tecnicos:
            ficha_tecnica["Dados Técnicos"] = dados_tecnicos
        if observacoes:
            ficha_tecnica["Observações"] = observacoes

        # --- Tabela de aplicações --------------------------------------
        resultados = []
        app_table_div = soup.find("div", class_="applicationTable")
        if not app_table_div:
            # Retorna uma entrada genérica se não há tabela
            print(f"[TSA] Tabela de aplicações não encontrada.")
            res = {
                "marca": self.config.get("nome", "TSA"),
                "montadora": "",
                "veiculo": "",
                "modelo": "",
                "motor": "",
                "configuracao_motor": dados_tecnicos,
                "combustivel": "",
                "ano_inicio": "",
                "ano_fim": "",
                "posicao": "",
                "observacao": observacoes,
                "imagem": imagem,
                "imagens": imagens,
                "referencias": referencias,
                "ficha_tecnica": ficha_tecnica,
            }
            return [self.formatar_resultado(res)]

        tbody = app_table_div.find("tbody")
        if not tbody:
            return []

        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue

            def td_text(idx):
                if idx < len(tds):
                    val = tds[idx].get_text(strip=True)
                    return val if val != "-" else ""
                return ""

            montadora = td_text(0)
            veiculo = td_text(1)
            modelo = td_text(2)
            motor = td_text(3)
            ano_raw = td_text(4)
            combustivel = td_text(5)

            ano_inicio, ano_fim = self._parse_ano_tsa(ano_raw)

            res = {
                "marca": self.config.get("nome", "TSA"),
                "montadora": montadora,
                "veiculo": veiculo,
                "modelo": modelo,
                "motor": motor,
                "configuracao_motor": combustivel,  # Combustível vai na coluna Motor/Config
                "ano_inicio": ano_inicio,
                "ano_fim": ano_fim,
                "posicao": "",
                "observacao": observacoes,
                "imagem": imagem,
                "imagens": imagens,
                "referencias": referencias,
                "ficha_tecnica": ficha_tecnica,
            }
            resultados.append(self.formatar_resultado(res))

        print(f"[TSA] {len(resultados)} aplicações extraídas.")
        return resultados

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------

    async def buscar(self, id_peca: str) -> List[Dict[str, Any]]:
        variacoes = self._variacoes_codigo(id_peca)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for codigo in variacoes:
                produto_url = await self._buscar_link_produto(client, codigo)
                if not produto_url:
                    continue

                resultados = await self._extrair_detalhes(client, produto_url)
                if resultados:
                    return resultados

        print(f"[TSA] Nenhum resultado encontrado para '{id_peca}'.")
        return []
