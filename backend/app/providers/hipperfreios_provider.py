import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
from .base_provider import BaseProvider

logger = logging.getLogger(__name__)

class HipperFreiosProvider(BaseProvider):
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.base_url = "https://www.hipperfreios.com.br"
        self.search_url = f"{self.base_url}/pt-br/produtos/busca"

    async def buscar(self, query: str) -> List[Dict]:
        """
        Busca por código no catálogo da Hipper Freios.
        """
        logger.info(f"[{self.config.get('nome')}] Buscando por: {query}")
        
        try:
            # Como o requests é síncrono, vamos rodar em um executor para não travar o loop
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _do_search():
                params = {"cod": query}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(self.search_url, params=params, headers=headers, timeout=15)
                response.encoding = response.apparent_encoding # Detecta encoding (provavelmente latin-1 ou cp1252)
                response.raise_for_status()
                return response.text

            html = await loop.run_in_executor(None, _do_search)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Localiza a tabela de resultados
            table = soup.find('table', class_='lista-tabela')
            if not table:
                logger.info(f"[{self.config.get('nome')}] Nenhum resultado encontrado para: {query}")
                return []
            
            rows = table.find_all('tr', class_='hover-table')
            results = []
            
            # Cache de detalhes para não baixar a mesma coisa várias vezes
            medidas_compartilhadas = {}
            imagem_high_res = None
            referencias_compartilhadas = ""
            imagens_detalhe = []

            for i, row in enumerate(rows):
                cols = row.find_all('td')
                if len(cols) < 8:
                    continue
                
                url_detalhe = row.get('data-href')
                if url_detalhe and not url_detalhe.startswith('http'):
                    url_detalhe = self.base_url + url_detalhe

                # Extração básica da linha
                montadora = cols[1].get_text(strip=True)
                veiculo = cols[2].get_text(strip=True)
                motor = cols[3].get_text(strip=True)
                ano_raw = cols[4].get_text(strip=True)
                produto = cols[5].get_text(strip=True)
                eixo = cols[6].get_text(strip=True)
                codigo = cols[7].get_text(strip=True)
                
                # Normalização de Anos
                ano_inicio, ano_fim = self._parse_anos(ano_raw)
                
                # Se for o primeiro item (ou o código mudar), enriquecemos
                if i == 0 and url_detalhe:
                    logger.info(f"[{self.config.get('nome')}] Enriquecendo detalhes via: {url_detalhe}")
                    detalhes = await self._enriquecer_detalhes(url_detalhe)
                    if detalhes:
                        medidas_compartilhadas = detalhes.get("medidas", {})
                        imagem_high_res = detalhes.get("imagem")
                        referencias_compartilhadas = detalhes.get("referencias", "")
                        imagens_detalhe = [imagem_high_res] if imagem_high_res else []
                        if detalhes.get("desenho"):
                            imagens_detalhe.append(detalhes.get("desenho"))

                app = {
                    "provedor": self.config.get("nome"),
                    "marca_peca": self.config.get("nome"),
                    "montadora": montadora,
                    "modelo": veiculo,
                    "motor": motor,
                    "ano_inicio": ano_inicio,
                    "ano_fim": ano_fim,
                    "posicao": eixo,
                    "codigo": codigo,
                    "observacao": produto,
                    "imagem": imagem_high_res or (self.base_url + cols[0].find('img')['src'] if cols[0].find('img') else None),
                    "imagens": imagens_detalhe,
                    "referencias": referencias_compartilhadas,
                    "ficha_tecnica": medidas_compartilhadas,
                    "url": url_detalhe
                }
                # Garante que passe pelo motor de normalização da BaseProvider
                results.append(self.formatar_resultado(app))
                
            return results
            
        except Exception as e:
            logger.error(f"[{self.config.get('nome')}] Erro na busca: {str(e)}")
            return []

    def _parse_anos(self, ano_raw: str):
        """
        Converte "1997 até 2004" ou "2012 em diante" para (int, int)
        """
        if not ano_raw or "não informado" in ano_raw.lower():
            return None, None
            
        anos = re.findall(r'\d{4}', ano_raw)
        inicio = int(anos[0]) if len(anos) >= 1 else None
        fim = int(anos[1]) if len(anos) >= 2 else None
        return inicio, fim

    async def _enriquecer_detalhes(self, url: str) -> Dict:
        """
        Acessa a página de detalhes para pegar medidas e referências OEM.
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _get_details():
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                res = requests.get(url, headers=headers, timeout=10)
                res.encoding = res.apparent_encoding
                res.raise_for_status()
                return res.text

            html = await loop.run_in_executor(None, _get_details)
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Imagem Alta Resolução
            box_img = soup.find('div', class_='box-img')
            img_tag = box_img.find('img') if box_img else None
            img_url = None
            if img_tag and img_tag.get('src'):
                src = img_tag['src']
                img_path = re.sub(r'^\.?\/+', '/', src)
                img_url = self.base_url + img_path

            # 2. Referências de Montadora (OEM)
            ref_span = soup.find('span', class_='montadora-codigo')
            referencias = ref_span.get_text(strip=True) if ref_span else ""
            
            # 3. Medidas Técnicas
            medidas = {}
            table_medidas = soup.find('div', class_='table-product')
            if table_medidas:
                rows = table_medidas.find_all('div', class_='row')
                for row in rows:
                    cols = row.find_all('div')
                    if len(cols) >= 3:
                        nome = cols[0].get_text(strip=True).replace("Medidas (mm):", "").strip()
                        sigla = cols[1].get_text(strip=True)
                        valor = cols[2].get_text(strip=True).replace("Tamanho:", "").strip()
                        full_name = f"{nome} ({sigla})" if sigla else nome
                        medidas[full_name] = valor
            
            # 4. Desenho Técnico
            desenho_url = None
            desenho_box = soup.find('div', class_='box-desenho')
            if not desenho_box:
                all_imgs = box_img.find_all('img') if box_img else []
                if len(all_imgs) > 1:
                    d_src = all_imgs[1].get('src')
                    if d_src:
                        d_path = re.sub(r'^\.?\/+', '/', d_src)
                        desenho_url = self.base_url + d_path

            return {
                "imagem": img_url,
                "referencias": referencias,
                "medidas": medidas,
                "desenho": desenho_url
            }
            
        except Exception as e:
            logger.error(f"[{self.config.get('nome')}] Erro ao enriquecer detalhes: {str(e)}")
            return {}
