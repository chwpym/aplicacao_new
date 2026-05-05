import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Any, Optional
from app.providers.base_provider import BaseProvider
from app.models.models import Provedor
import logging

logger = logging.getLogger(__name__)

class BuscaNaRedeProvider(BaseProvider):
    """
    Provedor genérico para a plataforma Busca na Rede (buscanarede.com.br).
    Suporta múltiplas marcas (Tuba, Sampel, TC Chicotes, etc.) via slug configurável.
    """

    def __init__(self, provedor_id: int, nome: str, slug: str, url_base: str, mapeamento: str = None):
        super().__init__(provedor_id, nome, slug, url_base, mapeamento)
        self.config = json.loads(mapeamento) if mapeamento else {}
        # O slug da marca no Busca na Rede (ex: tubacabos, sAMPEL)
        self.brand_slug = self.config.get("brand_slug", slug)
        self.base_domain = "https://buscanarede.com.br"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Discovery Phase: Busca o código no portal da marca.
        """
        search_url = f"{self.base_domain}/{self.brand_slug}/produtos?s={query}&data=&list="
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            # Encontrar os cards de produtos
            # No Busca na Rede, os produtos costumam vir em tags h2 ou h3 dentro de links
            product_links = soup.select("h2 a, h3 a, .product-item a")
            
            processed_urls = set()
            
            for link in product_links:
                url = link.get("href")
                if not url or "/produto/" not in url:
                    continue
                
                if not url.startswith("http"):
                    url = self.base_domain + url
                
                if url in processed_urls:
                    continue
                
                processed_urls.add(url)
                
                # Extrair detalhes do produto
                product_details = self._hydrate_product_details(url, query)
                if product_details:
                    results.extend(product_details)
            
            return results

        except Exception as e:
            logger.error(f"Erro na busca BuscaNaRede ({self.brand_slug}): {str(e)}")
            return []

    def _hydrate_product_details(self, url: str, query: str) -> List[Dict[str, Any]]:
        """
        Hydration Phase: Extrai as aplicações da página do produto.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Informações Básicas do Produto
            product_title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
            
            # 2. Imagem
            img_tag = soup.select_one(".product-image img, .img-responsive, #product-zoom")
            image_url = ""
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-zoom-image")
                if image_url and not image_url.startswith("http"):
                    image_url = self.base_domain + image_url

            # 3. Referências / Código Original
            referencias = []
            ref_section = soup.find(string=re.compile("Referência|Código Original|Nº Original", re.I))
            if ref_section:
                ref_parent = ref_section.find_parent()
                if ref_parent:
                    ref_text = ref_parent.get_text(strip=True)
                    # Tenta extrair códigos após o label
                    parts = re.split(r":|-", ref_text, 1)
                    if len(parts) > 1:
                        referencias = [parts[1].strip()]

            # 4. Tabela de Aplicações (Onde a mágica acontece)
            applications = []
            
            # Busca todas as tabelas na página
            tables = soup.find_all("table")
            
            for table in tables:
                headers = [th.get_text(strip=True).upper() for th in table.find_all("th")]
                if not headers:
                    # Tenta pegar a primeira linha se não houver <th>
                    first_row = table.find("tr")
                    if first_row:
                        headers = [td.get_text(strip=True).upper() for td in first_row.find_all("td")]
                
                if not headers: continue

                # Mapeamento Dinâmico de Colunas
                col_map = {}
                for i, h in enumerate(headers):
                    if any(x in h for x in ["MONTADORA", "FABRICANTE", "MARCA"]): col_map["veiculo"] = i
                    elif any(x in h for x in ["MODELO", "VEÍCULO", "VEICULO"]): col_map["modelo"] = i
                    elif any(x in h for x in ["VERSÃO", "VERSAO"]): col_map["versao"] = i
                    elif any(x in h for x in ["MOTOR"]): col_map["motor"] = i
                    elif any(x in h for x in ["ANO"]): col_map["ano"] = i
                    elif any(x in h for x in ["COMBUSTÍVEL", "COMBUSTIVEL"]): col_map["combustivel"] = i
                    elif any(x in h for x in ["OBSERVAÇÃO", "OBSERVACAO", "INFO"]): col_map["observacao"] = i
                    elif any(x in h for x in ["POSIÇÃO", "POSICAO"]): col_map["posicao"] = i

                rows = table.find_all("tr")[1:] # Pula o cabeçalho
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < len(headers): continue
                    
                    def get_val(key):
                        idx = col_map.get(key)
                        return cells[idx].get_text(strip=True) if idx is not None else ""

                    app = {
                        "marca": self.nome,
                        "codigo": query.upper(),
                        "veiculo": get_val("veiculo"),
                        "modelo": get_val("modelo"),
                        "versao": get_val("versao"),
                        "motor": get_val("motor"),
                        "ano": get_val("ano"),
                        "combustivel": get_val("combustivel"),
                        "observacao": get_val("observacao"),
                        "posicao": get_val("posicao"),
                        "imagem": image_url,
                        "referencias": referencias,
                        "ficha_tecnica": f"Título: {product_title}"
                    }
                    
                    # Se não encontrou montadora/modelo, pula (provavelmente não é a tabela de aplicação)
                    if not app["veiculo"] and not app["modelo"]:
                        continue
                        
                    applications.append(app)

            # Fallback: Se não houver tabela, tenta extrair de listas ou texto (comum em alguns layouts antigos)
            if not applications:
                # O Busca na Rede às vezes usa divs com classes específicas
                app_items = soup.select(".application-item, .item-aplicacao")
                for item in app_items:
                    text = item.get_text(strip=True)
                    applications.append({
                        "marca": self.nome,
                        "codigo": query.upper(),
                        "modelo": text,
                        "imagem": image_url,
                        "referencias": referencias
                    })

            return applications

        except Exception as e:
            logger.error(f"Erro ao hidratar produto BuscaNaRede ({url}): {str(e)}")
            return []
