import httpx
import re
import asyncio
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger

class AutafastarProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://www.autafastar.com.br"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.autafastar.com.br/"
        }

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Realiza a busca no catálogo Autafastar.
        """
        # O site usa a URL /busca/{termo}/
        search_url = f"{self.base_url}/busca/{termo}/"
        
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            try:
                response = await client.get(search_url, headers=self.headers)
                if response.status_code != 200:
                    logger.error("AUTAFASTAR", f"Erro na busca: Status {response.status_code}")
                    return []

                return await self._parse_search_results(response.text, client)
            except Exception as e:
                logger.error("AUTAFASTAR", f"Erro ao buscar: {str(e)}")
                return []

    async def _parse_search_results(self, html: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        product_wrappers = soup.select(".wrapper-produto")
        
        if not product_wrappers:
            return []

        tasks = []
        for wrapper in product_wrappers:
            link_elem = wrapper.select_one("a[href]")
            if not link_elem:
                continue

            product_url = link_elem["href"]
            if not product_url.startswith("http"):
                product_url = f"{self.base_url}{product_url}"

            # Dados básicos disponíveis na listagem
            sku_elem = wrapper.select_one(".codigo")
            sku = sku_elem.get_text(strip=True).upper() if sku_elem else ""
            
            aplicacao_elem = wrapper.select_one(".aplicacao")
            aplicacao_text = aplicacao_elem.get_text(strip=True) if aplicacao_elem else ""
            
            img_elem = wrapper.select_one("img.thumbnail-produto")
            img_url = ""
            if img_elem:
                img_url = img_elem.get("src", "")
                if img_url and not img_url.startswith("http"):
                    img_url = f"{self.base_url}{img_url}"

            # Extração dinâmica da marca (Autafastar vs Shockbras)
            fornecedor_img = wrapper.select_one(".fornecedor img")
            marca_peca = "AUTAFASTAR"
            if fornecedor_img:
                logo_src = fornecedor_img.get("src", "").lower()
                if "shockbras" in logo_src:
                    marca_peca = "SHOCKBRAS"
                elif "autafastar" in logo_src:
                    marca_peca = "AUTAFASTAR"

            # Agendamos o detalhamento (Hydration) para pegar refs e ficha técnica
            tasks.append(self._get_product_details(client, product_url, sku, aplicacao_text, img_url, marca_peca))

        # Executamos o hydration em paralelo para todos os resultados encontrados
        results = await asyncio.gather(*tasks)
        
        # O results é uma lista de listas (pois cada detalhamento pode gerar múltiplas aplicações)
        # Vamos achatar a lista
        flattened_results = []
        for sublist in results:
            flattened_results.extend(sublist)
            
        return flattened_results

    async def _get_product_details(self, client: httpx.AsyncClient, url: str, sku: str, aplicacao_base: str, img_url: str, marca_peca: str) -> List[Dict[str, Any]]:
        """
        Navega até a página do produto para extrair informações completas.
        """
        try:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return [self.formatar_resultado({
                    "marca_peca": marca_peca,
                    "codigo": sku,
                    "modelo": aplicacao_base,
                    "imagem": img_url
                })]

            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Referências Cruzadas (Similares)
            referencias = []
            similares_container = soup.select_one("#similares")
            if similares_container:
                ref_items = similares_container.select("p")
                for item in ref_items:
                    text = item.get_text(strip=True).strip()
                    if text:
                        # O texto já costuma vir como "MARCA: CODIGO" no HTML do Autafastar
                        # Se não tiver ':', mantemos o texto como está.
                        # Se tiver, o clipboard.ts cuidará do split e agrupamento.
                        referencias.append(text.upper())

            # 2. Especificações (Ficha Técnica)
            ficha_tecnica = {}
            especs_container = soup.select_one("#especificacoes")
            if especs_container:
                spec_items = especs_container.select("p")
                for item in spec_items:
                    # Remove apenas o marcador de lista inicial '-' mas mantém hífens internos
                    text = item.get_text(strip=True)
                    if text.startswith("-"):
                        text = text[1:].strip()
                    
                    if ":" in text:
                        k, v = text.split(":", 1)
                        ficha_tecnica[k.strip().upper()] = v.strip().upper()
                    elif text:
                        ficha_tecnica[text.upper()] = "-"

            # 3. Compatíveis (Aplicações Detalhadas)
            items = []
            compativeis_container = soup.select_one("#compativeis")
            compativeis_list = []
            if compativeis_container:
                comp_items = compativeis_container.select("p")
                for item in comp_items:
                    c_text = item.get_text(strip=True)
                    if c_text.startswith("-"):
                        c_text = c_text[1:].strip()
                    if c_text:
                        compativeis_list.append(c_text)

            if not compativeis_list:
                compativeis_list = [aplicacao_base]

            for comp in compativeis_list:
                # Regex para extrair motorização (Ex: 1.6 16V, 1.0, 2.0 Turbo)
                motor_match = re.search(r"(\d\.\d\s?(?:\d+V)?.*)", comp, re.IGNORECASE)
                motor = ""
                modelo_limpo = comp
                
                if motor_match:
                    motor = motor_match.group(1).strip()
                    # Remove o motor do modelo para não duplicar informação
                    modelo_limpo = comp.replace(motor, "").strip()
                
                res = {
                    "marca_peca": marca_peca,
                    "codigo": sku,
                    "montadora": modelo_limpo, # Passamos o modelo aqui para o AutomakerService deduzir a marca (Ex: 2008 -> PEUGEOT)
                    "modelo": modelo_limpo,
                    "motor": motor,
                    "imagem": img_url,
                    "referencias": referencias,
                    "ficha_tecnica": ficha_tecnica,
                    "observacao": aplicacao_base
                }
                
                # Extração de ano via BaseProvider (extrair_anos)
                ano_ini, ano_fim = self.extrair_anos(comp)
                res["ano_inicio"] = ano_ini
                res["ano_fim"] = ano_fim
                
                items.append(self.formatar_resultado(res))

            return items

        except Exception as e:
            logger.error("AUTAFASTAR", f"Erro no hydration ({sku}): {str(e)}")
            return [self.formatar_resultado({
                "marca_peca": marca_peca,
                "codigo": sku,
                "modelo": aplicacao_base,
                "imagem": img_url
            })]
