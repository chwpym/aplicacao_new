import httpx
import json
import asyncio
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider


class GenericScraperProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url_pattern = config.get("url", "")
        self.headers = config.get(
            "headers",
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        try:
            self.map = json.loads(config.get("mapeamento", "{}"))
        except:
            self.map = {}

    def parse_year(self, year_str: str):
        if not year_str:
            return None
        clean = "".join(filter(str.isdigit, year_str))
        if not clean:
            return None
        try:
            val = int(clean)
            if val < 100:
                return 2000 + val if val <= 40 else 1900 + val
            return val
        except:
            return None

    def get_text(self, soup, selector):
        if not selector or not soup:
            return ""
        # Suporte a seletores específicos como 'td:nth-child(2)'
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    async def buscar(self, id_peca: str):
        if not self.url_pattern:
            return []

        # Gera variações do ID para busca (com/sem hífens)
        codigos_busca = self.normalizar_codigo(id_peca)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for cod in codigos_busca:
                try:
                    url = self.url_pattern.replace("{id}", cod)
                    print(f"[GenericScraper] Consultando: {url}")
                    response = await client.get(url, headers=self.headers)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Verifica se caiu em uma página de "não encontrado" (comum em scrapers retornar 200)
                    if (
                        not soup
                        or "não encontrado" in response.text.lower()
                        or "not found" in response.text.lower()
                    ):
                        continue

                    # Verifica se precisamos navegar para uma página de detalhe
                    product_link_sel = self.map.get("product_link")
                    if product_link_sel:
                        link_el = soup.select_one(product_link_sel)
                        if link_el and link_el.get("href"):
                            detail_url = link_el["href"]
                            if not detail_url.startswith("http"):
                                # Tenta reconstruir a URL base
                                from urllib.parse import urljoin

                                detail_url = urljoin(url, detail_url)

                            print(
                                f"[GenericScraper] Navegando para detalhes: {detail_url}"
                            )
                            response = await client.get(
                                detail_url, headers=self.headers
                            )
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, "html.parser")

                    container_sel = self.map.get("container")
                    if not container_sel:
                        # Se não tem container, talvez os dados estejam na página de detalhes como um todo
                        container_els = [soup]
                    else:
                        container_els = soup.select(container_sel)

                    resultados = []
                    for item in container_els:
                        # Extração de Imagens
                        imagens = []
                        img_sel = self.map.get("imagem")
                        if img_sel:
                            for img in item.select(img_sel):
                                src = img.get("src") or img.get("data-src")
                                if src:
                                    if not src.startswith("http"):
                                        from urllib.parse import urljoin

                                        src = urljoin(url, src)
                                    if src not in imagens:
                                        imagens.append(src)

                        # Extração de Referências
                        referencias = []
                        ref_sel = self.map.get("referencias")
                        if ref_sel:
                            for ref_el in item.select(ref_sel):
                                txt = ref_el.get_text(strip=True, separator=" ")
                                if txt and txt not in referencias:
                                    referencias.append(txt)

                        # Extração de campos principais
                        res = {
                            "brand": self.get_text(item, self.map.get("marca")),
                            "name": self.get_text(item, self.map.get("veiculo")),
                            "model": self.get_text(item, self.map.get("modelo")),
                            "engineName": self.get_text(item, self.map.get("motor")),
                            "engineConfiguration": self.get_text(
                                item, self.map.get("configuracao_motor")
                            ),
                            "note": self.get_text(item, self.map.get("observacao")),
                            "startYear": self.parse_year(
                                self.get_text(item, self.map.get("ano_inicio"))
                            ),
                            "endYear": self.parse_year(
                                self.get_text(item, self.map.get("ano_fim"))
                            ),
                            "images": imagens,
                            "originalNumbers": " | ".join(referencias),
                            "crossReferences": " | ".join(referencias),
                        }

                        # Suporte a padrão de imagem calculado
                        img_pattern = self.map.get("image_pattern")
                        if img_pattern:
                            # Tenta descobrir o ID real na página se o mapeamento permitir
                            # Caso contrário usa o id_peca original
                            extracted_id = (
                                self.get_text(item, self.map.get("codigo_peca"))
                                or id_peca
                            )
                            canonical_id = self.canonicalizar_id_para_imagem(
                                extracted_id
                            )

                            base_img = img_pattern.replace("{id}", canonical_id)
                            res["image"] = base_img
                            res["images"] = [
                                base_img,
                                base_img.replace(".jpg", "B.jpg").replace(
                                    ".png", "B.png"
                                ),
                                base_img.replace(".jpg", "C.jpg").replace(
                                    ".png", "C.png"
                                ),
                            ]

                        if res["brand"] or res["name"] or res["model"]:
                            resultados.append(res)

                    if resultados:
                        return [self.formatar_resultado(r) for r in resultados]
                except Exception as e:
                    print(f"[GenericScraper] Erro com código {cod}: {e}")
                    continue

            return []
