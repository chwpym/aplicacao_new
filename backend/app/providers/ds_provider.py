import httpx
import json
from app.providers.base_provider import BaseProvider
from bs4 import BeautifulSoup

class DSProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = config.get("url", "https://www.ds.ind.br/pt/busca-full?q={id}")
        self.headers = config.get(
            "headers",
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )

    async def buscar(self, id_peca: str):
        """Fase 1 (Discovery): Busca o código e filtra os resultados exatos."""
        codigos_busca = self.normalizar_codigo(id_peca)
        resultados_finais = []
        links_processados = set()

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for cod in codigos_busca:
                url_busca = f"https://www.ds.ind.br/pt/busca-full?q={cod}"
                try:
                    print(f"[DS] Iniciando Discovery: {url_busca}")
                    response = await client.get(url_busca, headers=self.headers)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Caso 1: Redirecionamento direto para a página do produto
                    if "/produtos/" in str(response.url) and "busca-full" not in str(response.url):
                        full_url = str(response.url)
                        if full_url not in links_processados:
                            print(f"[DS] Redirecionamento direto: {full_url}")
                            detalhes = await self._extrair_detalhes_produto(client, full_url)
                            resultados_finais.extend(detalhes)
                            links_processados.add(full_url)
                        continue

                    # Caso 2: Listagem de resultados
                    itens_busca = soup.select(".resultado-itens li.index")
                    links_para_hidratar = []
                    
                    for item in itens_busca:
                        img_el = item.select_one("img")
                        link_el = item.select_one('a[href*="/produtos/"]')
                        
                        if not img_el or not link_el:
                            continue

                        # FILTRO MIRA LASER (padrão sugerido pelo usuário)
                        alt_text = img_el.get("alt", "").strip().upper()
                        link_text = link_el.get_text(strip=True).upper()
                        
                        # Verifica se o código de busca bate exatamente com o ALT ou está no título
                        if cod.upper() == alt_text or f"- {cod.upper()}" in link_text:
                            href = link_el["href"]
                            full_url = href if href.startswith("http") else f"https://www.ds.ind.br{href}"
                            if full_url not in links_processados:
                                print(f"[DS] Item validado: {alt_text} -> {full_url}")
                                links_para_hidratar.append(full_url)
                        else:
                            print(f"[DS] Ignorado: Buscado {cod.upper()} | Encontrado {alt_text}")

                    # Fase 2 (Hydration): Entra em cada produto validado
                    for url_prod in links_para_hidratar:
                        detalhes = await self._extrair_detalhes_produto(client, url_prod)
                        resultados_finais.extend(detalhes)
                        links_processados.add(url_prod)

                except Exception as e:
                    print(f"[DS] Erro na busca por {cod}: {e}")

        # Injeta o código da peça em todos os resultados antes de formatar
        for r in resultados_finais:
            if not r.get("codigo"):
                r["codigo"] = id_peca.strip().upper()
        return [self.formatar_resultado(r) for r in resultados_finais]

    async def _extrair_detalhes_produto(self, client, url):
        """Extrai dados técnicos profundos da página do produto."""
        try:
            print(f"[DS] Extraindo detalhes: {url}")
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Captura título e categoria para ajudar na identificação de combustível
            titulo_produto = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else ""
            categoria_produto = soup.select_one(".breadcrumbs").get_text(strip=True) if soup.select_one(".breadcrumbs") else ""
            
            # Referências OEM / Similares (Ajustado para o padrão de coluna única da DS)
            referencias = []
            for row in soup.select(".jq-codes tr, .tabela-referencias tr, .jq-refs tr"):
                tds = row.find_all("td")
                if len(tds) >= 2:
                    brand = tds[0].get_text(strip=True)
                    code = tds[1].get_text(strip=True)
                    if brand and code:
                        referencias.append(f"{brand}:{code}")
                elif len(tds) == 1:
                    # Caso da DS: <strong>Bosch</strong>:1582980142 (tudo em um TD)
                    info = tds[0].get_text(separator=":", strip=True).replace("::", ":")
                    if ":" in info:
                        referencias.append(info)
            
            # Backup: caso não seja tabela (blocos de texto)
            if not referencias:
                box_refs = soup.select_one(".box-referencias, .demais-codigos, .jq-codes")
                if box_refs:
                    texto_refs = box_refs.get_text(separator="\n", strip=True)
                    for linha in texto_refs.split("\n"):
                        if ":" in linha and len(linha) < 100: # Evita pegar parágrafos longos
                            referencias.append(linha.strip())

            ref_str = " | ".join(referencias)

            # Imagens da Galeria
            imagens = []
            for img_el in soup.select(".pgwSlider img, .img-produto, .gallery img, .thumb-produto img"):
                src = img_el.get("src") or img_el.get("data-src")
                if src:
                    full_src = src if src.startswith("http") else f"https://www.ds.ind.br{src}"
                    if full_src not in imagens:
                        imagens.append(full_src)

            # Aplicações
            resultados = []
            linhas_app = soup.select(".jq-apps tr, table.table-aplicacao tr, .table-generic tr, .table-aplicacoes tr")
            for row in linhas_app:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                val_complemento = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                
                # Inteligência para não duplicar combustível
                fuel_detected = ""
                config_motor = val_complemento
                
                # Lista de tipos conhecidos de combustível
                tipos_combustivel = ["FLEX", "GASOLINA", "ALCOOL", "DIESEL", "GNV", "TETRAFUEL"]
                
                # Se o campo for EXATAMENTE um combustível, movemos para fuel e limpamos o motor
                if val_complemento.upper() in tipos_combustivel:
                    fuel_detected = val_complemento
                    config_motor = ""
                # Se contiver o combustível mas tiver algo mais (ex: "FLEX 16V"), mantemos no motor e deixamos o motor de IA extrair
                elif any(c in val_complemento.upper() for c in tipos_combustivel):
                    fuel_detected = val_complemento

                res = {
                    "brand": cols[0].get_text(strip=True),
                    "name": cols[1].get_text(strip=True),
                    "model": cols[1].get_text(strip=True),
                    "motor": cols[2].get_text(strip=True),
                    "fuel": fuel_detected,
                    "configuracao_motor": config_motor,
                    "startYear": cols[4].get_text(strip=True) if len(cols) > 4 else "",
                    "note": cols[5].get_text(strip=True) if len(cols) > 5 else "",
                    "description": f"{titulo_produto} {categoria_produto}", 
                    "images": imagens,
                    "originalNumbers": ref_str,
                    "provedor": "DS"
                }
                
                if res["brand"] and res["brand"].upper() != "MONTADORA":
                    resultados.append(res)
            
            return resultados
        except Exception as e:
            print(f"[DS] Erro na extração de {url}: {e}")
            return []

    def formatar_resultado(self, raw_data: dict) -> dict:
        """Padronização final usando a inteligência do BaseProvider."""
        base = super().formatar_resultado(raw_data)
        base["marca"] = "DS"
        base["veiculo"] = str(raw_data.get("brand", "")).upper()
        
        modelo_bruto = str(raw_data.get("name", "")).upper()
        base["modelo"] = modelo_bruto
        
        if base.get("versao") == modelo_bruto:
            base["versao"] = ""
            
        return base
