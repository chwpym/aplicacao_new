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
            
            # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
            # Lê o header (th) para descobrir qual índice corresponde a qual campo.
            # Isso torna o parser resiliente a tabelas com menos ou mais colunas
            # (ex: "Cilindro Mestre" não tem coluna "Eixo", ficando com 7 colunas ao invés de 8).
            header_row = table.find('tr')
            col_map = {}  # nome_normalizado -> indice
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                for idx, th in enumerate(headers):
                    nome = th.get_text(strip=True).upper()
                    # Normaliza variações conhecidas para chaves estáveis
                    if "MONTADORA" in nome:
                        col_map["montadora"] = idx
                    elif nome in ("VEÍCULO", "VEICULO"):
                        col_map["veiculo"] = idx
                    elif "DETALHE" in nome or "MOTOR" in nome:
                        col_map["motor"] = idx
                    elif "ANO" in nome:
                        col_map["ano"] = idx
                    elif "PRODUTO" in nome:
                        col_map["produto"] = idx
                    elif "EIXO" in nome:
                        col_map["eixo"] = idx
                    elif nome in ("CÓDIGO", "CODIGO", "CÓD", "COD"):
                        col_map["codigo"] = idx
                    elif "IMAGEM" in nome or "IMG" in nome:
                        col_map["imagem"] = idx
            
            logger.info(f"[{self.config.get('nome')}] Mapa de colunas detectado: {col_map} ({len(col_map)} campos)")
            
            # Precisa pelo menos saber onde está o código
            if "codigo" not in col_map:
                logger.warning(f"[{self.config.get('nome')}] Coluna 'Código' não encontrada no header. Abortando.")
                return []
            
            # Helper seguro para extrair texto de uma coluna por nome
            def _get_col(cols, field, default=""):
                idx = col_map.get(field)
                if idx is not None and idx < len(cols):
                    return cols[idx].get_text(strip=True)
                return default
            
            rows = table.find_all('tr', class_='hover-table')
            results = []
            min_cols = min(col_map.values()) + 1 if col_map else 2  # mínimo de colunas necessário
            
            # 1. Discovery (Fase de Descoberta)
            # Mapeia as URLs únicas agrupadas pelo CÓDIGO DA PEÇA
            unique_codes_map = {} # codigo -> url_detalhe
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < min_cols: continue
                codigo = _get_col(cols, "codigo")
                url_detalhe = row.get('data-href')
                if url_detalhe and codigo:
                    if not url_detalhe.startswith('http'):
                        url_detalhe = self.base_url + url_detalhe
                    if codigo not in unique_codes_map:
                        unique_codes_map[codigo] = url_detalhe
            
            url_to_codigo = {v: k for k, v in unique_codes_map.items()}
            urls_para_hidratar = list(unique_codes_map.values())[:40] # 40 códigos únicos
            
            # 2. Hydration Concorrente (Baixa as peças ao mesmo tempo)
            detalhes_por_codigo = {}
            if urls_para_hidratar:
                logger.info(f"[{self.config.get('nome')}] Hidratando concorrentemente {len(urls_para_hidratar)} códigos únicos...")
                tasks = [self._enriquecer_detalhes(u) for u in urls_para_hidratar]
                import asyncio
                res_detalhes = await asyncio.gather(*tasks, return_exceptions=True)
                
                for u, dado in zip(urls_para_hidratar, res_detalhes):
                    cod = url_to_codigo[u]
                    if isinstance(dado, dict):
                        detalhes_por_codigo[cod] = dado
                    else:
                        detalhes_por_codigo[cod] = {}
            
            # 3. Merge Final 
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < min_cols:
                    continue
                
                url_detalhe = row.get('data-href')
                if url_detalhe and not url_detalhe.startswith('http'):
                    url_detalhe = self.base_url + url_detalhe

                # Extração dinâmica — usa o mapa de colunas
                codigo = _get_col(cols, "codigo")
                montadora = _get_col(cols, "montadora")
                veiculo = _get_col(cols, "veiculo")
                motor = _get_col(cols, "motor")
                ano_raw = _get_col(cols, "ano")
                produto = _get_col(cols, "produto")
                eixo = _get_col(cols, "eixo")  # Retorna "" se coluna não existir

                # Pega os detalhes corretos através do Código
                detalhes = detalhes_por_codigo.get(codigo, {})

                # Normalização de Anos
                ano_inicio, ano_fim = self._parse_anos(ano_raw)
                
                # Definição segura das variáveis hidratadas
                medidas_compartilhadas = detalhes.get("medidas", {})
                imagem_high_res = detalhes.get("imagem")
                referencias_compartilhadas = detalhes.get("referencias", "")
                
                imagens_detalhe = [imagem_high_res] if imagem_high_res else []
                if detalhes.get("desenho"):
                    imagens_detalhe.append(detalhes.get("desenho"))

                # Imagem fallback da thumbnail da tabela
                img_idx = col_map.get("imagem", 0)
                img_fallback = None
                if img_idx < len(cols) and cols[img_idx].find('img'):
                    img_fallback = self.base_url + cols[img_idx].find('img')['src']

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
                    "imagem": imagem_high_res or img_fallback,
                    "imagens": imagens_detalhe,
                    "referencias": referencias_compartilhadas,
                    "ficha_tecnica": medidas_compartilhadas,
                    "url": url_detalhe
                }
                
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
