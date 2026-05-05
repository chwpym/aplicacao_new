import httpx
import re
import json
import asyncio
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


class BuscaNaRedeProvider(BaseProvider):
    """
    Provedor genérico para a plataforma Busca na Rede (buscanarede.com.br).
    Suporta múltiplas marcas (Sampel, etc.) via brand_slug configurável no mapeamento.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Extrai o brand_slug do mapeamento JSON ou usa o nome do provedor como fallback
        mapeamento = config.get("mapeamento") or "{}"
        if isinstance(mapeamento, str):
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        self.brand_slug = mapeamento.get("brand_slug", config.get("nome", "").lower().replace(" ", ""))
        self.base_domain = "https://buscanarede.com.br"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Discovery Phase: Busca o código no portal da marca.
        """
        search_url = f"{self.base_domain}/{self.brand_slug}/produtos?s={termo}&data=&list="
        marca_peca = self.config.get("nome", "BUSCA NA REDE").upper()

        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            try:
                response = await client.get(search_url, headers=self.headers)
                if response.status_code != 200:
                    logger.error("BUSCA_NA_REDE", f"Erro na busca ({self.brand_slug}): Status {response.status_code}")
                    return []

                soup = BeautifulSoup(response.text, "html.parser")
                results = []

                # Encontrar os cards de produtos
                product_links = soup.select("h2 a, h3 a, .product-item a")

                processed_urls = set()
                tasks = []

                for link in product_links:
                    url = link.get("href")
                    if not url or "/produto/" not in url:
                        continue

                    if not url.startswith("http"):
                        url = self.base_domain + url

                    if url in processed_urls:
                        continue

                    processed_urls.add(url)
                    tasks.append(self._hydrate_product_details(client, url, termo, marca_peca))

                # Hydration em paralelo
                if tasks:
                    all_results = await asyncio.gather(*tasks)
                    for sublist in all_results:
                        results.extend(sublist)

                return results

            except Exception as e:
                logger.error("BUSCA_NA_REDE", f"Erro na busca ({self.brand_slug}): {str(e)}")
                return []

    async def _hydrate_product_details(self, client: httpx.AsyncClient, url: str, query: str, marca_peca: str) -> List[Dict[str, Any]]:
        """
        Hydration Phase: Extrai as aplicações da página do produto.
        """
        try:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # 1. Informações Básicas do Produto
            product_title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

            # 2. Imagem
            img_tag = soup.select_one(".product-image img, .img-responsive, #product-zoom")
            image_url = ""
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-zoom-image") or ""
                if image_url and not image_url.startswith("http"):
                    image_url = self.base_domain + image_url

            # 3. Referências / Código Original
            referencias = []
            ref_section = soup.find(string=re.compile(r"Referência|Código Original|Nº Original", re.I))
            if ref_section:
                ref_parent = ref_section.find_parent()
                if ref_parent:
                    ref_text = ref_parent.get_text(strip=True)
                    parts = re.split(r":|-", ref_text, 1)
                    if len(parts) > 1:
                        referencias.append(parts[1].strip().upper())

            # 4. Ficha Técnica (do título)
            ficha_tecnica = {}
            if product_title:
                ficha_tecnica["PRODUTO"] = product_title.upper()

            # 5. Tabela de Aplicações
            items = []
            tables = soup.find_all("table")

            for table in tables:
                headers_raw = [th.get_text(strip=True).upper() for th in table.find_all("th")]
                if not headers_raw:
                    first_row = table.find("tr")
                    if first_row:
                        headers_raw = [td.get_text(strip=True).upper() for td in first_row.find_all("td")]

                if not headers_raw:
                    continue

                # Mapeamento Dinâmico de Colunas
                col_map = {}
                for i, h in enumerate(headers_raw):
                    if any(x in h for x in ["MONTADORA", "FABRICANTE", "MARCA"]):
                        col_map["montadora"] = i
                    elif any(x in h for x in ["MODELO", "VEÍCULO", "VEICULO"]):
                        col_map["modelo"] = i
                    elif any(x in h for x in ["VERSÃO", "VERSAO"]):
                        col_map["versao"] = i
                    elif any(x in h for x in ["MOTOR"]):
                        col_map["motor"] = i
                    elif any(x in h for x in ["ANO"]):
                        col_map["ano"] = i
                    elif any(x in h for x in ["COMBUSTÍVEL", "COMBUSTIVEL"]):
                        col_map["combustivel"] = i
                    elif any(x in h for x in ["OBSERVAÇÃO", "OBSERVACAO", "INFO"]):
                        col_map["observacao"] = i
                    elif any(x in h for x in ["POSIÇÃO", "POSICAO"]):
                        col_map["posicao"] = i

                rows = table.find_all("tr")[1:]  # Pula o cabeçalho
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < max(col_map.values(), default=0) + 1:
                        continue

                    def get_val(key):
                        idx = col_map.get(key)
                        return cells[idx].get_text(strip=True) if idx is not None and idx < len(cells) else ""

                    # Extrair ano
                    ano_texto = get_val("ano")
                    ano_ini, ano_fim = self.extrair_anos(ano_texto) if ano_texto else ("", "")

                    raw_data = {
                        "marca_peca": marca_peca,
                        "codigo": query.upper(),
                        "montadora": get_val("montadora"),
                        "modelo": get_val("modelo"),
                        "versao": get_val("versao"),
                        "motor": get_val("motor"),
                        "combustivel": get_val("combustivel"),
                        "observacao": get_val("observacao"),
                        "posicao": get_val("posicao"),
                        "ano_inicio": ano_ini,
                        "ano_fim": ano_fim,
                        "imagem": image_url,
                        "referencias": referencias,
                        "ficha_tecnica": ficha_tecnica,
                    }

                    # Pula linhas sem montadora e sem modelo (provavelmente não é tabela de aplicação)
                    if not raw_data["montadora"] and not raw_data["modelo"]:
                        continue

                    items.append(self.formatar_resultado(raw_data))

            # Fallback: Se não houver tabela, tenta extrair de listas
            if not items:
                app_items = soup.select(".application-item, .item-aplicacao")
                for item in app_items:
                    text = item.get_text(strip=True)
                    raw_data = {
                        "marca_peca": marca_peca,
                        "codigo": query.upper(),
                        "modelo": text,
                        "imagem": image_url,
                        "referencias": referencias,
                        "ficha_tecnica": ficha_tecnica,
                    }
                    items.append(self.formatar_resultado(raw_data))

            return items

        except Exception as e:
            logger.error("BUSCA_NA_REDE", f"Erro no hydration ({url}): {str(e)}")
            return []
