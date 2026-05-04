import httpx
import re
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


class NakataProvider(BaseProvider):
    """
    Provedor para o catálogo online da Nakata (catalogonakata.com.br).
    Usa Web Scraping com BeautifulSoup para extrair dados de peças.
    Fluxo Discovery-Hydration:
      1. POST /busca → lista de produtos (links) ou redirect direto ao detalhe
      2. GET  /detalhe/{slug} → HTML com aplicações, referências e ficha técnica
    """

    BASE_URL = "https://www.catalogonakata.com.br"

    def __init__(self, config):
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Origin": "https://www.catalogonakata.com.br",
            "Referer": "https://www.catalogonakata.com.br/",
        }

    async def buscar(self, part_id: str):
        clean_id = part_id.strip().upper().replace(" ", "")
        results = []

        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True, verify=False
        ) as client:
            try:
                # ── 1. DISCOVERY: busca inicial por keyword ──
                logger.info("NAKATA", f"Buscando por: {clean_id}")

                # Precisamos de um token CSRF para o POST
                home_resp = await client.get(self.BASE_URL, headers=self.headers)
                csrf_token = self._extract_csrf_token(home_resp.text)

                search_data = {"keywords": clean_id}
                if csrf_token:
                    search_data["_token"] = csrf_token

                search_resp = await client.post(
                    f"{self.BASE_URL}/busca",
                    data=search_data,
                    headers={**self.headers, "Content-Type": "application/x-www-form-urlencoded"},
                )

                if search_resp.status_code != 200:
                    logger.error("NAKATA", f"Erro na busca ({search_resp.status_code})")
                    return []

                # Verificar se redirecionou direto para detalhe ou se é lista
                final_url = str(search_resp.url)
                html = search_resp.text

                if "/detalhe/" in final_url:
                    # Redirect direto para o detalhe de uma única peça
                    logger.info("NAKATA", f"Redirect direto para detalhe: {final_url}")
                    detail_results = self._parse_detail_page(html, final_url)
                    results.extend(detail_results)
                else:
                    # Lista de resultados — extrair links de detalhe
                    detail_links = self._extract_detail_links(html)
                    logger.info("NAKATA", f"Encontrados {len(detail_links)} produto(s) na lista")

                    if not detail_links:
                        logger.warning("NAKATA", f"Nenhum resultado encontrado para: {clean_id}")
                        return []

                    # ── 2. HYDRATION: buscar detalhes de cada produto ──
                    for link in detail_links:
                        try:
                            detail_url = link if link.startswith("http") else f"{self.BASE_URL}{link}"
                            detail_resp = await client.get(detail_url, headers=self.headers)
                            if detail_resp.status_code == 200:
                                detail_results = self._parse_detail_page(detail_resp.text, detail_url)
                                results.extend(detail_results)
                        except Exception as e:
                            logger.error("NAKATA", f"Erro ao hidratar {link}: {str(e)}")

                logger.info("NAKATA", f"Total de aplicações extraídas: {len(results)}")
                return results

            except Exception as e:
                logger.error("NAKATA", f"Erro geral na busca: {str(e)}")
                return []

    def _extract_csrf_token(self, html: str) -> str:
        """Extrai o token CSRF do HTML da página."""
        soup = BeautifulSoup(html, "html.parser")
        token_input = soup.find("input", {"id": "_token"})
        if token_input:
            return token_input.get("value", "")
        # Fallback: buscar por name="_token"
        token_input = soup.find("input", {"name": "_token"})
        if token_input:
            return token_input.get("value", "")
        return ""

    def _extract_detail_links(self, html: str) -> list[str]:
        """Extrai links de detalhe de produtos da página de resultados."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        # Procurar links que apontem para /detalhe/
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/detalhe/" in href:
                links.add(href)

        return list(links)

    def _parse_detail_page(self, html: str, url: str) -> list[dict]:
        """Parseia a página de detalhe de um produto Nakata."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # ── Código da peça ──
        codigo = ""
        h2_detail = soup.select_one("h2.detail-content")
        if h2_detail:
            codigo = h2_detail.get_text(strip=True)

        # Fallback: extrair do título
        if not codigo:
            h1 = soup.find("h1")
            if h1:
                text = h1.get_text(strip=True)
                # "Terminal de Direção - N 3072" → "N 3072"
                if " - " in text:
                    codigo = text.split(" - ", 1)[1].strip()

        # ── Imagem do produto ──
        imagem = ""
        img_detail = soup.select_one(".slider-detail img")
        if img_detail:
            imagem = img_detail.get("src", "")
            if imagem and not imagem.startswith("http"):
                imagem = f"{self.BASE_URL}{imagem}"

        # ── Segmento / Grupo / Produto ──
        segmento = ""
        grupo = ""
        produto = ""
        detail_blocks = soup.select(".detail-content")
        detail_titles = soup.select(".detail-title")
        for i, title in enumerate(detail_titles):
            label = title.get_text(strip=True).lower()
            # O valor correspondente é o próximo .detail-content
            content = detail_blocks[i] if i < len(detail_blocks) else None
            if not content:
                continue
            val = content.get_text(strip=True)
            if "segmento" in label:
                segmento = val
            elif "grupo" in label:
                grupo = val
            elif "produto" in label and "grupo" not in label:
                produto = val

        # ── Referências Cruzadas ──
        referencias = []
        ref_section = None
        for title in soup.select(".detail-title"):
            if "referência cruzada" in title.get_text(strip=True).lower():
                ref_section = title.find_parent("div", class_="block")
                break

        if ref_section:
            rows = ref_section.select(".row")
            for row in rows:
                cols = row.select("h4")
                if len(cols) >= 2:
                    marca_ref = cols[0].get_text(strip=True).upper()
                    codigo_ref = cols[1].get_text(strip=True).upper()
                    if marca_ref and codigo_ref:
                        referencias.append(f"{marca_ref}: {codigo_ref}")

        refs_str = ", ".join(referencias)

        # ── Ficha Técnica (dados dimensionais) ──
        ficha = {}
        for title in detail_titles:
            label = title.get_text(strip=True)
            label_lower = label.lower()
            # Procurar campos de ficha técnica
            sibling = title.find_next_sibling(class_="detail-content")
            if not sibling:
                # Tentar span irmão
                parent = title.parent
                if parent:
                    sibling = parent.find("span", class_="detail-content")
            if not sibling:
                continue

            val = sibling.get_text(strip=True)
            if any(k in label_lower for k in ["peso", "comprimento", "rosca", "diâmetro",
                                                "barras", "embalagem", "largura", "altura"]):
                ficha[label] = val

        # ── Produto / Linha ──
        linha = produto if produto else grupo

        # ── Aplicações (tabela de veículos) ──
        table = soup.select_one(".vehicles table")
        if table:
            rows = table.select("tbody tr")
            # Filtrar linhas mobile (badge-nakata são headers mobile, não dados)
            data_rows = [r for r in rows if "badge-nakata" not in " ".join(r.get("class", []))]

            for row in data_rows:
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                montadora = cells[0].get_text(strip=True).upper() if len(cells) > 0 else ""
                modelo = cells[1].get_text(strip=True).upper() if len(cells) > 1 else ""
                ano_raw = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                posicao = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                lado = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                direcao = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                observacao = cells[6].get_text(strip=True) if len(cells) > 6 else ""

                # Parse dos anos: "01/00 - 12/16" → ano_inicio=2000, ano_fim=2016
                ano_inicio, ano_fim = self._parse_anos(ano_raw)

                app = {
                    "marca": "NAKATA",
                    "codigo": codigo,
                    "montadora": montadora,
                    "modelo": modelo,
                    "versao": "",
                    "motor": "",
                    "configuracao_motor": "",
                    "ano_inicio": ano_inicio,
                    "ano_fim": ano_fim,
                    "posicao": posicao,
                    "lado": lado,
                    "direcao": direcao,
                    "observacao": observacao,
                    "imagem": imagem,
                    "referencias": refs_str,
                    "ficha_tecnica": ficha if ficha else None,
                }

                results.append(self.formatar_resultado(app))
        else:
            # Se não houver tabela de veículos, ainda retorna o produto com seus dados
            logger.warning("NAKATA", f"Nenhuma tabela de aplicações encontrada para {codigo}")
            app = {
                "marca": "NAKATA",
                "codigo": codigo,
                "montadora": "",
                "modelo": "",
                "versao": "",
                "motor": "",
                "ano_inicio": "",
                "ano_fim": "",
                "imagem": imagem,
                "referencias": refs_str,
                "observacao": linha,
                "ficha_tecnica": ficha if ficha else None,
            }
            results.append(self.formatar_resultado(app))

        return results

    def _parse_anos(self, ano_raw: str) -> tuple:
        """
        Converte formatos de ano Nakata para o padrão do sistema.
        Ex: "01/00 - 12/16" → ("2000", "2016")
            "01/94 - 12/02" → ("1994", "2002")
        """
        if not ano_raw:
            return ("", "")

        # Remove espaços extras
        ano_raw = ano_raw.strip()

        # Pattern: "MM/AA - MM/AA"
        match = re.match(r"(\d{2})/(\d{2})\s*-\s*(\d{2})/(\d{2})", ano_raw)
        if match:
            ano_ini = int(match.group(2))
            ano_fin = int(match.group(4))

            # Converter ano de 2 dígitos para 4
            ano_inicio = str(2000 + ano_ini) if ano_ini < 50 else str(1900 + ano_ini)
            ano_fim = str(2000 + ano_fin) if ano_fin < 50 else str(1900 + ano_fin)

            return (ano_inicio, ano_fim)

        # Pattern: "AAAA - AAAA"
        match = re.match(r"(\d{4})\s*-\s*(\d{4})", ano_raw)
        if match:
            return (match.group(1), match.group(2))

        return (ano_raw, ano_raw)
