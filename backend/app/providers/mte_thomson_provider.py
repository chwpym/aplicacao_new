from app.providers.base_provider import BaseProvider
import httpx
from bs4 import BeautifulSoup
import re
import asyncio


class MteThomsonProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.base_url = "https://cate.mte-thomson.com.br"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://cate.mte-thomson.com.br/pt/br",
        }

    async def buscar(self, part_id: str):
        # Normaliza o ID para a busca (ex: 4050-1)
        # O MTE parece usar {id}-1 para busca de código MTE
        clean_id = part_id.strip().upper()

        # URL de pesquisa direta fornecida pelo usuário
        search_url = (
            f"{self.base_url}/pt/br/produto/pesquisar/{clean_id}-1/false/lp-todas"
        )

        print(f"[MTE] Buscando: {search_url}")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                resp = await client.get(search_url, headers=self.headers)
                if resp.status_code != 200:
                    print(f"[MTE] Erro na busca ({resp.status_code})")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")

                # Procura pelas linhas de resultado (grid-row)
                rows = soup.select("tr.grid-row")
                if not rows:
                    print(f"[MTE] Nenhum resultado encontrado para {clean_id}")
                    return []

                # Pega o primeiro link de detalhes que bater com o código
                detail_url = None
                for row in rows:
                    cod_cell = row.select_one("td[data-name='PARTNUMBER']")
                    if cod_cell and clean_id in cod_cell.text.strip():
                        link = cod_cell.find("a")
                        if link:
                            detail_url = self.base_url + link["href"]
                            break

                if not detail_url and rows:
                    link = rows[0].select_one("td[data-name='PARTNUMBER'] a")
                    if link:
                        detail_url = self.base_url + link["href"]

                if not detail_url:
                    return []

                print(f"[MTE] Buscando detalhes: {detail_url}")
                detail_resp = await client.get(detail_url, headers=self.headers)
                if detail_resp.status_code != 200:
                    return []

                return self._parse_details(detail_resp.text, clean_id)

            except Exception as e:
                print(f"[MTE] Erro: {str(e)}")
                return []

    def _parse_details(self, html, part_id):
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Título / Nome da Peça
        title_tag = soup.select_one("h1.font-size-custom-TituloDetalhes")
        nome_peca = title_tag.text.strip() if title_tag else "Produto MTE"

        # Imagens - Melhorando a detecção
        images = []

        # Método 1: Seletores CSS diretos (thumbnails)
        thumbnails = soup.select(".dxigItem_mtethomson img.dxig-img")
        for img in thumbnails:
            src = img.get("src")
            if src:
                # O usuário confirmou que 1000x1000 é a raiz segura
                src = src.replace("300x300", "1000x1000")
                if not src.startswith("http"):
                    src = (
                        "https:" + src if src.startswith("//") else self.base_url + src
                    )
                if src not in images:
                    images.append(src)

        # Método 2: Extrair dos Scripts (DevExpress Carousel)
        # Mais robusto se as tags img forem dinâmicas
        scripts = soup.find_all("script", id=re.compile("dxss_"))
        for script in scripts:
            if (
                script.string
                and "https://cdn.mte-thomson.com.br/catalogo/Images/" in script.string
            ):
                # Regex para pegar URLs de imagem no JSON do Carousel
                # Pega URLs bem formadas fugindo de aspas e vírgulas
                found_urls = re.findall(
                    r'(https://cdn\.mte-thomson\.com\.br/catalogo/Images/[^"\'\s,>]+)',
                    script.string,
                )
                for url in found_urls:
                    # Normaliza para 1000x1000 e limpa eventuais escapes
                    clean_url = url.replace("300x300", "1000x1000").strip()
                    if clean_url not in images:
                        images.append(clean_url)

        # Referências OE (GridOEM)
        referencias = []
        oem_table = soup.find("table", id=re.compile("GridOEM"))
        if oem_table:
            for row in oem_table.select("tr.dxgvDataRow_mtethomson"):
                cells = row.find_all("td", class_="dxgv")
                if len(cells) >= 2:
                    marca = cells[0].text.strip()
                    codigo = cells[1].text.strip()
                    if marca and codigo:
                        referencias.append(f"{marca}: {codigo}")

        ref_str = " | ".join(referencias)

        # Aplicações (GridAplicacao)
        app_table = soup.find("table", id=re.compile("GridAplicacao"))
        if app_table:
            rows = app_table.select("tr.dxgvDataRow_mtethomson")
            for row in rows:
                cells = [td.text.strip() for td in row.find_all("td")]
                # 0: Montadora, 1: Modelo, 2: Motor, 3: Desc. Motor, 4: Válvulas, 5: Comb, 6: Ini, 7: Fim, 8: Posição, 13: Obs
                if len(cells) >= 9:
                    montadora = cells[0]
                    veiculo = cells[1]
                    motor = cells[2]
                    desc_motor = cells[3]
                    valvulas = cells[4]
                    combustivel = cells[5]
                    ano_ini = cells[6]
                    ano_fim = cells[7]
                    posicao = cells[8]
                    obs = cells[13] if len(cells) > 13 else ""

                    detalhes = (
                        f"{desc_motor} {valvulas}V {combustivel} {obs}".strip().replace(
                            "  ", " "
                        )
                    )

                    raw = {
                        "brand": "MTE-THOMSON",
                        "veiculo": montadora,
                        "modelo": veiculo,
                        "motor": motor,
                        "configuracao_motor": detalhes,
                        "referencias": ref_str,
                        "imagens": images,
                        "ano_inicio": ano_ini,
                        "ano_fim": ano_fim,
                        "posicao": posicao,
                        "observacao": nome_peca,
                    }
                    results.append(self.formatar_resultado(raw))

        # Se não achou aplicações no Grid, retorna o básico
        if not results:
            results.append(
                self.formatar_resultado(
                    {
                        "brand": "MTE-THOMSON",
                        "veiculo": "PRODUTO ENCONTRADO",
                        "modelo": nome_peca,
                        "referencias": ref_str,
                        "imagens": images,
                        "observacao": "Veja detalhes no catálogo MTE",
                    }
                )
            )

        return results
