import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
from .base_provider import BaseProvider

# Configuração do Logger
logger = logging.getLogger(__name__)

class IntermecProvider(BaseProvider):
    """
    Provedor de autopeças nativo para a Intermec Automotive.
    Realiza scraping assíncrono e direto no e-commerce baseado em WordPress + WooCommerce
    usando chamadas HTTP reais e BeautifulSoup para parsing resiliente das informações.
    """
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.base_url = "https://www.intermecautomotive.com.br"
        
    async def buscar(self, query: str) -> List[Dict]:
        """
        Realiza a busca por código no site da Intermec Automotive.
        Gera variações do código e faz requisições HTTP reais de rede.
        """
        logger.info(f"[{self.config.get('nome')}] Iniciando busca de rede para o termo: '{query}'")
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Gera variações do código buscado para aumentar as chances de acerto
            codigos_candidatos = self.normalizar_codigo(query)
            if not codigos_candidatos:
                return []
                
            # Usamos o primeiro candidato normalizado para a busca principal
            codigo_busca = codigos_candidatos[0]
            logger.info(f"[{self.config.get('nome')}] Códigos normalizados gerados: {codigos_candidatos}. Buscando por: '{codigo_busca}'")
            
            def _executar_requisicao():
                # Headers completos simulando um navegador moderno para evitar bloqueios HTTP 403/Cloudflare
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                }
                
                # O WooCommerce responde por buscas via GET através do parâmetro '?s='
                # Filtrar pelo post_type=product ajuda a restringir os resultados a produtos do catálogo
                params = {
                    "s": codigo_busca,
                    "post_type": "product"
                }
                
                # Realiza o GET com redirecionamento automático ativado (allow_redirects=True)
                # O WooCommerce redireciona automaticamente para a página de detalhes do produto se houver correspondência exata!
                response = requests.get(self.base_url, params=params, headers=headers, timeout=15)
                response.encoding = response.apparent_encoding or "utf-8"
                response.raise_for_status()
                return response.url, response.text

            final_url, html_content = await loop.run_in_executor(None, _executar_requisicao)
            
            # Processa o HTML retornado
            return await self._parse_html(html_content, final_url)
            
        except Exception as e:
            logger.error(f"[{self.config.get('nome')}] Erro durante a requisição de busca para '{query}': {str(e)}")
            return []
            
    async def _parse_html(self, html: str, url: str) -> List[Dict]:
        """
        Analisa o HTML retornado para decidir se é uma página de produto único
        ou uma listagem com múltiplos produtos (Discovery -> Hydration).
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Se contiver a classe de descrição curta de detalhes do WooCommerce, caímos direto na página de detalhes!
        is_pagina_detalhe = soup.find(class_='woocommerce-product-details__short-description') is not None
        
        if is_pagina_detalhe:
            logger.info(f"[{self.config.get('nome')}] Redirecionado diretamente para a página do produto: {url}")
            return self._extrair_detalhes_produto(soup, url)
            
        # Se for uma página de listagem, precisamos extrair os links de cada produto e hidratá-los
        logger.info(f"[{self.config.get('nome')}] Página de listagem detectada. Buscando produtos listados...")
        
        # Encontra todos os itens de produto na listagem
        itens_produto = soup.find_all(class_='product')
        if not itens_produto:
            itens_produto = soup.find_all('li', class_='product')
            
        if not itens_produto:
            logger.info(f"[{self.config.get('nome')}] Nenhum produto compatível encontrado na listagem para esta busca.")
            return []
            
        # Coleta URLs exclusivas para hidratação
        urls_produtos = []
        for item in itens_produto:
            # Tenta pegar a tag de link padrão do WooCommerce Loop ou qualquer link filho
            a_link = item.find('a', class_='woocommerce-LoopProduct-link') or item.find('a')
            if a_link and a_link.get('href'):
                href = a_link['href']
                if href not in urls_produtos:
                    urls_produtos.append(href)
                    
        if not urls_produtos:
            logger.info(f"[{self.config.get('nome')}] Nenhuma URL de detalhes extraída da listagem.")
            return []
            
        logger.info(f"[{self.config.get('nome')}] Encontradas {len(urls_produtos)} URLs de produtos. Hidratando os primeiros 5 concorrentemente...")
        
        # Hidratação assíncrona concorrente dos detalhes de cada URL encontrada
        import asyncio
        loop = asyncio.get_event_loop()
        
        async def _hidratar_url(u: str) -> List[Dict]:
            try:
                def _get_page_content():
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    res = requests.get(u, headers=headers, timeout=10)
                    res.encoding = res.apparent_encoding or "utf-8"
                    res.raise_for_status()
                    return res.text
                    
                html_detalhe = await loop.run_in_executor(None, _get_page_content)
                soup_detalhe = BeautifulSoup(html_detalhe, 'html.parser')
                return self._extrair_detalhes_produto(soup_detalhe, u)
            except Exception as e:
                logger.error(f"[{self.config.get('nome')}] Falha ao hidratar produto via URL '{u}': {str(e)}")
                return []
                
        # Limitamos a concorrência a 5 requisições de hidratação para evitar sobrecarregar o site do fabricante
        tasks = [_hidratar_url(u) for u in urls_produtos[:5]]
        resultados_hidratados = await asyncio.gather(*tasks)
        
        lista_final = []
        for res in resultados_hidratados:
            lista_final.extend(res)
            
        return lista_final

    def _extrair_detalhes_produto(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Extrai todos os dados técnicos, fotos, equivalências e aplicações da página do produto.
        """
        results = []
        
        # 1. Código do Produto (Título do Produto)
        title_h1 = soup.find('h1', class_='product_title')
        if not title_h1:
            logger.warning(f"[{self.config.get('nome')}] Não foi possível identificar o título/código da peça no HTML.")
            return []
            
        codigo_peca = title_h1.get_text(strip=True)
        
        # 2. Ficha Técnica e Códigos Originais (Tabela de Atributos do WooCommerce)
        ficha_tecnica = {}
        referencias_originais = ""
        
        attributes_table = soup.find('table', class_='shop_attributes')
        if attributes_table:
            for row in attributes_table.find_all('tr'):
                label_th = row.find('th')
                value_td = row.find('td')
                if label_th and value_td:
                    key = label_th.get_text(strip=True)
                    val = value_td.get_text(strip=True).strip().strip(",")
                    
                    # Identifica se a linha contém códigos originais/conversões
                    if any(x in key.lower() for x in ["cód", "cod", "original", "referencia", "ref"]):
                        # Processa e prefixa com "ORIGINAL: " para que a normalization e o frontend identifiquem
                        codigos_oem = []
                        val_clean = val.replace("|", ",").replace(";", ",").replace("\n", ",")
                        for pt in val_clean.split(","):
                            pt_strip = pt.strip()
                            if not pt_strip:
                                continue
                            if ":" in pt_strip:
                                codigos_oem.append(pt_strip)
                            else:
                                codigos_oem.append(f"ORIGINAL: {pt_strip}")
                        referencias_originais = " | ".join(codigos_oem)
                    else:
                        ficha_tecnica[key] = val

        # 3. Galeria de Imagens (Suporte nativo a Carrossel de Imagens)
        imagens = []
        gallery_wrapper = soup.find(class_='woocommerce-product-gallery__wrapper')
        if gallery_wrapper:
            divs_imagem = gallery_wrapper.find_all(class_='woocommerce-product-gallery__image')
            for div in divs_imagem:
                # O WooCommerce envelopa a imagem original em uma tag <a> com o href apontando para o arquivo fonte em alta res
                a_tag = div.find('a')
                if a_tag and a_tag.get('href'):
                    imagens.append(a_tag['href'])
                else:
                    img_tag = div.find('img')
                    if img_tag and img_tag.get('src'):
                        imagens.append(img_tag['src'])
                        
        # Garante a URL da imagem principal e a galeria completa
        imagem_principal = imagens[0] if imagens else None

        # 4. Processamento das Aplicações (Descrição Curta)
        short_desc = soup.find(class_='woocommerce-product-details__short-description')
        paragraphs = short_desc.find_all('p') if short_desc else []
        if not paragraphs and short_desc:
            paragraphs = [short_desc]
            
        aplicacoes_mapeadas = False
        
        for p in paragraphs:
            current_montadora = None
            
            # BeautifulSoup nos dá a lista de conteúdos inline (tags strong, br e NavigableStrings)
            for child in p.contents:
                if child.name == 'strong':
                    text_strong = child.get_text(strip=True)
                    # Verifica se o texto do strong representa uma montadora real ou apenas códigos OE
                    # Lógica: Não deve conter pontos (típico de OE), não deve ser muito longo, e não deve ser puramente numérico
                    if "." not in text_strong and len(text_strong) < 20 and not text_strong.replace(",", "").strip().isdigit():
                        current_montadora = text_strong.replace(":", "").strip()
                elif current_montadora and (isinstance(child, str) or getattr(child, 'name', None) != 'strong'):
                    # Pega o texto corrido que descreve os modelos daquela montadora
                    text_val = child.get_text(strip=True) if hasattr(child, 'get_text') else str(child).strip()
                    if not text_val:
                        continue
                    text_val = text_val.strip().strip(",")
                    if text_val:
                        # Processa a string de veículos separados por vírgula
                        # Exemplo: "Amarok (após 2010), Bora (2001 –2002), Gol (G5 e posterior)"
                        modelos_list = [m.strip() for m in text_val.split(',') if m.strip()]
                        
                        for carro_str in modelos_list:
                            nome_veiculo = carro_str
                            parenteses_content = ""
                            
                            # Isola informações entre parênteses
                            match_parenteses = re.search(r'\((.*?)\)', carro_str)
                            if match_parenteses:
                                parenteses_content = match_parenteses.group(1).strip()
                                # Limpa o nome do carro removendo o parênteses
                                nome_veiculo = re.sub(r'\(.*?\)', '', carro_str).strip()
                                
                            # Remove espaços duplicados se houver
                            nome_veiculo = re.sub(r'\s+', ' ', nome_veiculo).strip()
                            
                            # Extração inteligente de Anos (local)
                            ano_ini, ano_fim = self._parse_anos_intermec(parenteses_content)
                            
                            # Extração de motores ou versões dentro de parênteses
                            motor_extra = ""
                            versao_extra = ""
                            
                            if parenteses_content:
                                if "motor" in parenteses_content.lower() or re.search(r'\b\d\.\d\b', parenteses_content):
                                    motor_extra = parenteses_content.replace("motor", "").replace("Motor", "").strip()
                                elif "g5" in parenteses_content.lower() or "posterior" in parenteses_content.lower():
                                    versao_extra = parenteses_content
                                    
                            # Constrói o dicionário bruto com todos os metadados coletados
                            raw_item = {
                                "marca_peca": self.config.get("nome"),
                                "provedor": self.config.get("nome"),
                                "codigo": codigo_peca,
                                "montadora": current_montadora,
                                "modelo": nome_veiculo,
                                "motor": motor_extra,
                                "versao": versao_extra,
                                "ano_inicio": ano_ini,
                                "ano_fim": ano_fim,
                                "imagem": imagem_principal,
                                "imagens": imagens,
                                "referencias": referencias_originais,
                                "ficha_tecnica": ficha_tecnica,
                                "url": url
                            }
                            
                            # A normalização de motorização, limpeza de WeGa e verificação cruzada FIPE (DuckDB) 
                            # ocorrem de forma robusta e inteligente dentro da própria BaseProvider.formatar_resultado
                            results.append(self.formatar_resultado(raw_item))
                            aplicacoes_mapeadas = True

        # Fallback: Caso o produto não tenha aplicações listadas na descrição curta (ex: cabo industrial),
        # criamos ao menos um registro contendo a ficha técnica e a foto para garantir que a peça seja catalogada
        if not aplicacoes_mapeadas:
            logger.info(f"[{self.config.get('nome')}] Produto sem aplicações estruturadas na descrição curta. Gerando fallback básico.")
            raw_item = {
                "marca_peca": self.config.get("nome"),
                "provedor": self.config.get("nome"),
                "codigo": codigo_peca,
                "montadora": "",
                "modelo": "",
                "motor": "",
                "versao": "",
                "ano_inicio": "",
                "ano_fim": "",
                "imagem": imagem_principal,
                "imagens": imagens,
                "referencias": referencias_originais,
                "ficha_tecnica": ficha_tecnica,
                "url": url
            }
            results.append(self.formatar_resultado(raw_item))
            
        return results

    def _parse_anos_intermec(self, content: str) -> tuple[str, str]:
        """
        Converte termos textuais em strings de ano_inicio e ano_fim de forma inteligente.
        Exemplos: 
        "após 2010" -> ("2010", "")
        "2001 –2002" -> ("2001", "2002")
        "2020 e posterior" -> ("2020", "")
        """
        if not content:
            return "", ""
            
        # Busca por padrões de 4 dígitos (anos)
        anos = re.findall(r'\b\d{4}\b', content)
        if not anos:
            return "", ""
            
        texto_upper = content.upper()
        # Mapeia se o ano é aberto/ininterrupto (diante, após, posterior, etc)
        is_aberto = any(x in texto_upper for x in [
            "APÓS", "APOS", "POSTERIOR", "DIANTE", "A PARTIR", 
            "...", "ONWARDS", ">", "E POSTERIOR", "POSTERIOR"
        ])
        
        if is_aberto:
            return anos[0], ""
            
        if len(anos) >= 2:
            return anos[0], anos[1]
            
        return anos[0], ""
