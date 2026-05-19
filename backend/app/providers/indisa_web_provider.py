import httpx
from bs4 import BeautifulSoup, NavigableString
import re
from app.providers.base_provider import BaseProvider


class IndisaWebProvider(BaseProvider):
    BASE_URL = "https://www.indisa.com.br"

    def __init__(self, config):
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def buscar(self, part_id: str):
        """
        Estratégia de busca:
        1. Tenta URL direta /catalogo/{code}/ (mais rápido, sem login)
        2. Se falhar, usa endpoint de busca com cookie de autenticação
        """
        cookies = {"LgCatalogo": "d4882042e060f8cf0b26b059835aa6bd"}

        async with httpx.AsyncClient(
            verify=False, follow_redirects=True, cookies=cookies
        ) as client:
            try:
                # === MÉTODO 1: URL direta (principal) ===
                direct_url = f"{self.BASE_URL}/catalogo/{part_id}/"
                resp = await client.get(direct_url, headers=self.headers, timeout=10.0)

                if resp.status_code == 200:
                    resp.encoding = "iso-8859-1"
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Verifica se caiu na página de detalhe (tem breadcrumb nível 3)
                    # e não na página genérica de catálogo
                    breadcrumb = soup.find(
                        "a", href=lambda h: h and f"/catalogo/{part_id}/" in str(h).lower()
                    )
                    if breadcrumb:
                        return self._parse_produto(soup, part_id)

                # === MÉTODO 2: Busca via formulário (fallback) ===
                search_url = (
                    f"{self.BASE_URL}/catalogo/"
                    f"?ChaveBusca1={part_id}"
                    f"&ChaveBusca2=&CodigoMontadora=0&CodigoCategoria=0"
                )
                search_resp = await client.get(
                    search_url, headers=self.headers, timeout=10.0
                )
                if search_resp.status_code != 200:
                    return []

                search_resp.encoding = "iso-8859-1"
                search_soup = BeautifulSoup(search_resp.text, "html.parser")

                # Procura o link do produto nos resultados
                h2 = search_soup.find("h2", class_="IntTitulo")
                a_tag = None
                if h2:
                    a_tag = h2.find("a")
                if not a_tag:
                    a_tag = search_soup.find(
                        "a",
                        href=lambda h: h and f"/catalogo/" in h and part_id.lower() in h.lower(),
                    )
                if not a_tag or not a_tag.get("href"):
                    return []

                # Busca a página de detalhe
                product_url = a_tag.get("href")
                if not product_url.startswith("http"):
                    product_url = f"{self.BASE_URL}{product_url}"

                detail_resp = await client.get(
                    product_url, headers=self.headers, timeout=10.0
                )
                if detail_resp.status_code != 200:
                    return []

                detail_resp.encoding = "iso-8859-1"
                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                return self._parse_produto(detail_soup, part_id)

            except Exception as e:
                print(f"[INDISA WEB] Erro ao buscar {part_id}: {e}")
                return []

    # ─────────────────────────────────────────────────────────────
    # PARSER DA PÁGINA DE DETALHE
    # ─────────────────────────────────────────────────────────────

    def _parse_produto(self, soup, codigo_peca):
        """
        Estrutura da página de detalhe da Indisa:
        - Slider de imagens em #SlickProdutos (a.MPImagens -> href = imagem G_)
        - Blocos <div class="custom-head"><h3>TITULO</h3></div> seguidos de texto solto até <hr>
          - "Linha de Produto"
          - "Código"
          - "Informações Técnicas" (aplicações separadas por <br>)
          - "Observação"
          - "Nº de conversão" (referências: CODIGO (MARCA)<br>...)
        """
        # 1. Extrair imagens do slider
        imagem_principal = ""
        imagens = []
        slider = soup.find("div", id="SlickProdutos")
        if slider:
            for a_tag in slider.find_all("a", class_="MPImagens"):
                href = a_tag.get("href", "")
                if href:
                    full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    imagens.append(full_url)
                    if not imagem_principal:
                        imagem_principal = full_url

        # 2. Extrair seções da ficha (texto livre entre custom-head e hr)
        secoes = self._extrair_secoes(soup)

        # 3. Ficha técnica
        ficha_tecnica = {}
        linha_produto = secoes.get("linha de produto", "").strip()
        if linha_produto:
            ficha_tecnica["LINHA DE PRODUTO"] = linha_produto.upper()

        # 4. Observação
        observacao_raw = secoes.get("observação", "")
        observacao = observacao_raw.replace("<br>", " / ").replace("<br/>", " / ").strip()
        # Limpa barras duplas ou espaços excessivos
        observacao = re.sub(r"\s*/\s*/\s*", " / ", observacao)
        observacao = re.sub(r"\s+", " ", observacao).strip()

        # 5. Referências (Nº de conversão)
        referencias = []
        conversao_raw = secoes.get("nº de conversão", secoes.get("n° de conversão", ""))
        if conversao_raw:
            refs = [r.strip() for r in conversao_raw.split("<br>") if r.strip()]
            for r in refs:
                # Formato: CODIGO (MARCA) -> MARCA: CODIGO
                match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", r)
                if match:
                    code_part = match.group(1).strip()
                    brand_part = match.group(2).strip()
                    referencias.append(f"{brand_part}: {code_part}")
                else:
                    referencias.append(r)
        ref_str = " | ".join(referencias)

        # 6. Aplicações (Informações Técnicas)
        aplicacoes = []
        info_tecnica = secoes.get("informações técnicas", "")
        if info_tecnica:
            lines = [line.strip() for line in info_tecnica.split("<br>") if line.strip()]
            for line in lines:
                app = self._parse_linha_aplicacao(line)
                if app:
                    app["codigo"] = codigo_peca
                    app["observacao"] = observacao
                    app["imagem"] = imagem_principal
                    app["imagens"] = imagens
                    if ref_str:
                        app["referencias"] = ref_str
                    if ficha_tecnica:
                        app["ficha_tecnica"] = ficha_tecnica

                    aplicacoes.append(self.formatar_resultado(app))

        return aplicacoes

    def _extrair_secoes(self, soup):
        """
        Extrai todas as seções da página de detalhe.
        Cada seção é um <div class="custom-head"><h3>TÍTULO</h3></div>
        seguido de texto/html livre até o próximo <hr>.
        """
        secoes = {}
        custom_heads = soup.find_all("div", class_="custom-head")

        for head_div in custom_heads:
            h3 = head_div.find("h3")
            if not h3:
                continue

            titulo = h3.text.strip().lower()
            content_parts = []

            # Percorre os siblings após o div.custom-head
            node = head_div.next_sibling
            while node:
                if hasattr(node, "name") and node.name in ("hr", "div"):
                    # div.custom-head do próximo bloco ou <hr> separador
                    if node.name == "div" and "custom-head" in (node.get("class") or []):
                        break
                    if node.name == "hr":
                        break

                if isinstance(node, NavigableString):
                    text = str(node).strip()
                    if text:
                        content_parts.append(text)
                elif hasattr(node, "name") and node.name == "br":
                    content_parts.append("<br>")

                node = node.next_sibling

            secoes[titulo] = "".join(content_parts).strip()

        return secoes

    def _parse_linha_aplicacao(self, linha):
        """
        Formatos encontrados:
          GM: ASTRA (C/ DH) - 1.8 8V - 99/03
          GM: ASTRA/CD - 2.0 L 8V SOHC L4 - 1999/2003
          VOLKSWAGEN: FOX - 1.0 8V - 03/07
        Padrão: MARCA: MODELO/VERSAO - MOTOR - ANOS
        """
        partes = linha.split(":")
        if len(partes) < 2:
            return None

        marca = partes[0].strip()
        resto = ":".join(partes[1:]).strip()

        tracos = resto.split(" - ")

        veiculo_versao = tracos[0].strip() if len(tracos) > 0 else ""
        motor_config = tracos[1].strip() if len(tracos) > 1 else ""
        anos = tracos[2].strip() if len(tracos) > 2 else ""

        veiculo = veiculo_versao
        versao = ""
        if "/" in veiculo_versao:
            v_parts = veiculo_versao.split("/", 1)
            veiculo = v_parts[0].strip()
            versao = v_parts[1].strip()

        ano_ini = ""
        ano_fim = ""
        if anos:
            a_parts = anos.split("/")
            ano_ini = a_parts[0].strip()
            if len(a_parts) > 1:
                ano_fim = a_parts[1].strip()

            # Normaliza anos curtos ex 03 -> 2003
            if len(ano_ini) == 2:
                ano_ini = f"19{ano_ini}" if int(ano_ini) > 50 else f"20{ano_ini}"
            if ano_fim and len(ano_fim) == 2:
                ano_fim = f"19{ano_fim}" if int(ano_fim) > 50 else f"20{ano_fim}"

        return {
            "montadora": marca,
            "modelo": veiculo,
            "versao": versao,
            "motor": motor_config,
            "ano_inicio": ano_ini,
            "ano_fim": ano_fim,
        }
