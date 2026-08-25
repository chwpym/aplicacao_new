import httpx
import re
import json
import asyncio
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


class BaseBuscaNaRedeProvider(BaseProvider):
    """
    Provedor genérico base para a plataforma Busca na Rede (buscanarede.com.br).
    Serve de fundação para múltiplas marcas (Sampel, Tuba Cabos, TC Chicotes, etc.).
    
    Estratégia: O site carrega dados via JavaScript (SPA), então extraímos as aplicações
    dos metadados OG (og:description) que contêm todas as informações de forma estática.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        mapeamento = config.get("mapeamento") or "{}"
        if isinstance(mapeamento, str):
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        self.brand_slug = mapeamento.get("brand_slug", config.get("nome", "").lower().replace(" ", ""))
        self.base_domain = "https://buscanarede.com.br"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
                
                # Extrai os cards de produto em vez de apenas os links cegamente
                cards = soup.select(".product-item, .card-produto, li.col-md-3")
                
                processed_urls = set()
                tasks = []

                if not cards:
                    # Fallback genérico se a estrutura da página for diferente
                    product_links = soup.select("h2 a, h3 a, .product-item a")
                    for link in product_links:
                        url = link.get("href")
                        if not url or "/produto/" not in url:
                            continue
                        if not url.startswith("http"):
                            url = self.base_domain + url
                        if url not in processed_urls:
                            processed_urls.add(url)
                            tasks.append(self._hydrate_product(client, url, termo, marca_peca))
                else:
                    for card in cards:
                        # Extrair o código real do produto (normalmente está em botões de ação ou no título)
                        code_el = card.select_one("[data-codigo]")
                        real_code = code_el.get("data-codigo") if code_el else None
                        
                        if not real_code:
                            h2 = card.find("h2")
                            if h2:
                                span = h2.find("span")
                                real_code = span.get_text(strip=True) if span else h2.get_text(strip=True)
                        
                        real_code = real_code.strip() if real_code else termo
                        
                        # Extrair o link
                        link = card.select_one("a[href*='/produto/']")
                        if not link:
                            link = card.find("a")
                            
                        if link:
                            url = link.get("href")
                            if url and "/produto/" in url:
                                if not url.startswith("http"):
                                    url = self.base_domain + url
                                if url not in processed_urls:
                                    processed_urls.add(url)
                                    # Passamos real_code em vez do termo de busca
                                    tasks.append(self._hydrate_product(client, url, real_code, marca_peca))

                if not tasks:
                    return []

                all_results = await asyncio.gather(*tasks)
                flattened = []
                for sublist in all_results:
                    flattened.extend(sublist)

                return flattened

            except Exception as e:
                logger.error("BUSCA_NA_REDE", f"Erro na busca ({self.brand_slug}): {str(e)}")
                return []

    async def _hydrate_product(self, client: httpx.AsyncClient, url: str, query: str, marca_peca: str) -> List[Dict[str, Any]]:
        """
        Hydration Phase: Extrai aplicações dos metadados OG da página do produto.
        O site carrega tabelas via JS, mas os dados completos estão no og:description.
        """
        try:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # 1. Título do produto (descrição da peça)
            h1 = soup.find("h1")
            product_title = h1.get_text(strip=True).upper() if h1 else ""

            # 2. Imagem
            og_img = soup.find("meta", {"property": "og:image"})
            image_url = og_img.get("content", "").strip() if og_img else ""

            # 3. Extrair dados das aplicações
            description_text = ""
            
            # Tenta primeiro a tabela de aplicações (mais estruturada e limpa que o og:description em algumas marcas como TC Chicotes)
            app_table = soup.find("table", id="aplicacoes")
            if app_table:
                tr_texts = []
                for tr in app_table.find_all("tr"):
                    classes = tr.get("class", [])
                    if "montadora" in classes:
                        continue
                        
                    t = tr.get_text(separator=" ", strip=True)
                    if not t:
                        continue
                    tr_texts.append(t)
                if tr_texts:
                    description_text = " | ".join(tr_texts)

            # SEMPRE pega o og:description para buscar referências depois
            og_desc = soup.find("meta", {"property": "og:description"})
            og_text = og_desc.get("content", "") if og_desc else ""

            if not description_text:
                description_text = og_text

            if not description_text:
                meta_desc = soup.find("meta", {"name": "description"})
                description_text = meta_desc.get("content", "") if meta_desc else ""

            # 4. Busca referências via data-remote (AJAX que o site usa para as abas OEM/Equivalências)
            remote_links = soup.select("a[data-remote*='/equivalences'], a[data-remote*='/oem']")
            referencias = []
            if remote_links:
                remote_tasks = []
                for link in remote_links:
                    remote_url = link.get("data-remote")
                    if remote_url:
                        remote_tasks.append(client.get(remote_url, headers=self.headers))
                
                if remote_tasks:
                    try:
                        remote_responses = await asyncio.gather(*remote_tasks)
                        for r_rem in remote_responses:
                            if r_rem.status_code == 200 and r_rem.text.strip():
                                rem_soup = BeautifulSoup(r_rem.text, "html.parser")
                                # O site coloca cada referência em uma div .p-2
                                p2_divs = rem_soup.select(".p-2")
                                for div in p2_divs:
                                    b = div.find("b")
                                    label = div.find(class_="label")
                                    if label:
                                        code = label.get_text(strip=True)
                                        if b:
                                            brand = b.get_text(strip=True).replace(":", "").strip()
                                            referencias.append(f"{brand}: {code}")
                                        else:
                                            referencias.append(code)
                    except Exception as e:
                        logger.error("BUSCA_NA_REDE", f"Erro ao buscar referências remotas em {url}: {str(e)}")

            items = []
            
            # 1. Tenta extrair aplicações a partir da tabela estruturada (alta precisão)
            app_table = soup.find("table", id="aplicacoes")
            table_extracted = False
            if app_table:
                for tr in app_table.find_all("tr"):
                    classes = tr.get("class", [])
                    if "montadora" in classes or not tr.get_text(strip=True):
                        continue
                        
                    mont_el = tr.find("span", style=lambda s: s and "display:none" in s)
                    modelo_el = tr.find("b")
                    anos_td = tr.find("td", class_="anos")
                    model_td = tr.find("td", class_="models")
                    
                    if mont_el and modelo_el:
                        montadora = mont_el.get_text(strip=True)
                        modelo = modelo_el.get_text(strip=True)
                        anos_text = anos_td.get_text(strip=True) if anos_td else ""
                        
                        extra_text = ""
                        if model_td:
                            full_text = model_td.get_text(separator=" ", strip=True)
                            extra_text = full_text.replace(montadora, "").replace(modelo, "").replace("-", " ").strip()
                            extra_text = re.sub(r'\s+', ' ', extra_text)
                            
                        items.append({
                            "marca_peca": marca_peca,
                            "codigo": query.upper(),
                            "montadora": montadora,
                            "modelo": modelo,
                            "versao": extra_text,
                            "motor": "",
                            "ano_inicio": anos_text,
                            "ano_fim": "",
                            "observacao": product_title,
                            "imagem": image_url,
                            "ficha_tecnica": {"PRODUTO": product_title} if product_title else {},
                        })
                        table_extracted = True
                        
            # 2. Fallback: Se não encontrou tabela, usa o texto de description
            if not table_extracted:
                if "|" in description_text:
                    raw_blocks = [b.strip() for b in description_text.split("|") if b.strip()]
                else:
                    raw_blocks = re.split(r'\s{2,}', description_text.strip())
                    
                # Adiciona blocos de referência do og_text se não estiverem no description_text
                if og_text and og_text != description_text:
                    og_blocks = re.split(r'\s{2,}', og_text.strip())
                    for ob in og_blocks:
                        if ob.strip().startswith("-"):
                            raw_blocks.append(ob.strip())
                            
                cleaned = []
                for b in raw_blocks:
                    b = b.strip()
                    if not b or b == "-" or "Publicado" in b:
                        continue
                    if b.startswith("-"):
                        refs = [r.strip().upper() for r in b.split("-") if r.strip()]
                        for ref in refs:
                            if self._is_reference_code(ref):
                                referencias.append(ref)
                        continue
                    cleaned.append(b)

                merged_blocks = []
                i = 0
                while i < len(cleaned):
                    block = cleaned[i]
                    has_year = bool(re.search(r'\b(19[5-9]\d|20[0-3]\d)\b', block)) or "TODOS" in block.upper()
                    has_letters = bool(re.search(r'[A-Za-z]', block))

                    if has_year and has_letters:
                        merged_blocks.append(block)
                    elif has_letters and not has_year:
                        if i + 1 < len(cleaned):
                            next_block = cleaned[i + 1]
                            next_has_year = bool(re.search(r'\b(19[5-9]\d|20[0-3]\d)\b', next_block)) or "TODOS" in next_block.upper()
                            if next_has_year:
                                merged_blocks.append(f"{block} {next_block}")
                                i += 2
                                continue
                        clean_upper = block.strip().upper()
                        if self._is_reference_code(clean_upper):
                            referencias.append(clean_upper)
                    elif has_year and not has_letters:
                        pass
                    else:
                        clean_upper = block.strip().upper()
                        if self._is_reference_code(clean_upper):
                            referencias.append(clean_upper)
                    i += 1

                for block in merged_blocks:
                    parsed = self._parse_application_block(block)
                    if parsed:
                        obs_parts = []
                        if parsed.get("observacao"):
                            obs_parts.append(parsed["observacao"])
                        items.append({
                            "marca_peca": marca_peca,
                            "codigo": query.upper(),
                            "montadora": parsed["montadora"],
                            "modelo": parsed["modelo"],
                            "versao": parsed["versao"],
                            "motor": parsed["motor"],
                            "ano_inicio": parsed["ano_inicio"],
                            "ano_fim": parsed["ano_fim"],
                            "observacao": " | ".join(obs_parts),
                            "imagem": image_url,
                            "ficha_tecnica": {"PRODUTO": product_title} if product_title else {},
                        })

            # Injeta referências em todos os itens (limpar e deduplicar)
            if referencias:
                clean_refs = []
                seen_refs = set()
                for ref in referencias:
                    # Limpar referências com palavras repetidas (ex: "180696 180696" -> "180696")
                    words = ref.split()
                    unique_words = []
                    for w in words:
                        if w not in unique_words:
                            unique_words.append(w)
                    ref = " ".join(unique_words)
                    
                    # Não incluir o próprio código buscado
                    if ref.replace(".", "").replace("-", "") == query.upper().replace(".", "").replace("-", ""):
                        continue
                    
                    if ref not in seen_refs and len(ref) > 1:
                        seen_refs.add(ref)
                        # Se já tiver marca (ex: CABOVEL: 123), não adicionamos ORIGINAL:
                        if ":" in ref:
                            clean_refs.append(ref)
                        else:
                            clean_refs.append(f"ORIGINAL: {ref}")
                
                if clean_refs:
                    ref_str = " | ".join(clean_refs)
                    for item in items:
                        item["referencias"] = ref_str

            # Deduplica aplicações iguais (o site repete blocos)
            seen = set()
            unique_items = []
            for item in items:
                key = (item["montadora"], item["modelo"], item["versao"], item["motor"], item["ano_inicio"], item["ano_fim"])
                if key not in seen:
                    seen.add(key)
                    unique_items.append(self.formatar_resultado(item))

            return unique_items

        except Exception as e:
            logger.error("BUSCA_NA_REDE", f"Erro no hydration ({url}): {str(e)}")
            return []

    def _parse_application_block(self, block: str) -> dict | None:
        """
        Parseia um bloco de aplicação do og:description.
        """
        if not block:
            return None

        words = block.split()
        if len(words) < 2:
            return None

        # 1. Separar palavras textuais dos anos e dados técnicos
        text_words = []
        years = []
        motor_parts = []
        
        i = 0
        while i < len(words):
            word = words[i]
            # É um ano? (4 dígitos entre 1940-2030)
            if re.match(r'^\d{4}$', word) and 1940 <= int(word) <= 2030:
                years.append(word)
            # Especial para TC Chicotes/Busca na Rede: "TODOS" representa range completo
            elif word.upper() == "TODOS":
                years.extend(["1940", "2026"])
            # É motor? (padrão X.X ou contém vírgula seguida de válvulas)
            elif re.match(r'^\d[\.,]\d', word) or word.upper() in ("MPI", "EFI", "MPFI", "16V", "8V", "TDI", "TSI", "VHC", "FLEX", "GASOLINA", "DIESEL"):
                motor_parts.append(word)
            elif word == "-":
                # Ignora hífens soltos de separação
                pass
            else:
                # Todo resto vai para text_words para ser analisado pelas triplas
                text_words.append(word)
            i += 1

        # 2. Identificar Grupos Triplos (Padrão Busca na Rede)
        triples = []
        prefix_words = []
        
        idx = 0
        found_triples = False
        while idx < len(text_words):
            word = text_words[idx]
            count = 1
            while idx + count < len(text_words) and text_words[idx + count] == word:
                count += 1
            
            if count >= 3:
                triples.append(word)
                found_triples = True
            elif not found_triples:
                prefix_words.append(word)
            else:
                # Palavras avulsas após o início das triplas podem ser parte da versão ou motor
                motor_parts.insert(0, word) # Adiciona ao início do motor/detalhes
            idx += count

        # 3. Mapear campos baseados nas triplas
        # Se não houver triplas, tentamos o método de grupos simples (fallback)
        if not triples:
            groups = self._extract_repeated_groups(text_words)
            montadora = groups[0] if len(groups) > 0 else ""
            modelo = groups[1] if len(groups) > 1 else ""
            versao = groups[2] if len(groups) > 2 else ""
            observacao = ""
        else:
            # Padrão: 1ª tripla=Montadora, 2ª=Modelo, 3ª=Versão
            montadora = triples[0]
            modelo = triples[1] if len(triples) > 1 else ""
            versao = triples[2] if len(triples) > 2 else ""
            observacao = " ".join(prefix_words).strip()
            
            # Ajuste para casos como "ALTERNADOR DIVERSOS DIVERSOS DIVERSOS"
            # Se a primeira tripla for "DIVERSOS" e tiver prefixo, o prefixo é mais importante
            if montadora.upper() == "DIVERSOS" and observacao:
                montadora = observacao
                modelo = "DIVERSOS"
                observacao = ""
            
            # Se houver mais de 3 triplas, as extras vão para a versão/motor
            if len(triples) > 3:
                versao = f"{versao} {' '.join(triples[3:])}".strip()

        # 4. Processar Anos
        ano_inicio = years[0] if years else ""
        ano_fim = years[-1] if len(years) > 1 else ""
        if ano_inicio == ano_fim:
            ano_fim = ""

        return {
            "montadora": montadora,
            "modelo": modelo,
            "versao": versao,
            "motor": " ".join(motor_parts).strip(),
            "ano_inicio": ano_inicio,
            "ano_fim": ano_fim,
            "observacao": observacao
        }

    def _extract_repeated_groups(self, words: list) -> list:
        """
        Extrai grupos de palavras que se repetem consecutivamente.
        Ex: ["FIAT", "FIAT", "FIAT", "SIENA", "SIENA", "SIENA"] -> ["FIAT", "SIENA"]
        """
        if not words:
            return []

        groups = []
        i = 0
        while i < len(words):
            word = words[i]
            # Conta quantas vezes essa palavra se repete consecutivamente
            count = 1
            while i + count < len(words) and words[i + count] == word:
                count += 1

            groups.append(word)
            i += count  # Pula todas as repetições

        return groups

    def _is_reference_code(self, text: str) -> bool:
        """
        Verifica se um texto parece ser um código de referência real.
        """
        if not text or len(text) < 3:
            return False
        if len(text) > 40:
            return False
        
        # Palavras descritivas que frequentemente aparecem em metadados mas não são códigos
        invalid_words = {
            "CHICOTE", "CHICOTES", "REPARO", "VIAS", "FEMEA", "MACHO", "QUALIDADE", 
            "ORIGINAL", "OEM", "PEÇA", "PEÇAS", "GARANTIA", "ESTOQUE", "ENVIO",
            "COMPATÍVEL", "APLICAÇÃO", "MOTOR", "VEÍCULO", "MONTADORA", "MARCA",
            "SAMPEL", "TUBA", "CHICOTES", "TC", "PECA", "FÊMEA"
        }
        
        words = text.split()
        if any(w in invalid_words for w in words):
            return False
            
        if len(words) > 3:
            return False
        
        # Palavras posicionais genéricas
        ignore = {"INFERIOR", "SUPERIOR", "DIANTEIRO", "TRASEIRO", "ESQUERDO", "DIREITO", "CENTRAL", "LADO"}
        # Se QUALQUER palavra do texto for um termo posicional, descarta (ex: "8190 INFERIOR")
        if any(w in ignore for w in words):
            return False
        
        # Um código de referência real geralmente:
        # 1. Contém dígitos (ex: 5U0615301C)
        # 2. OU é uma sigla curta de marca + código (ex: GM 9044)
        # 3. OU tem um padrão alfanumérico denso (sem muitos espaços)
        
        has_digit = any(c.isdigit() for c in text)
        if has_digit:
            # Se tem dígito, aceitamos se não for uma frase longa
            return len(words) <= 2 or (len(words) <= 3 and len(text) < 20)
        
        # Se não tem dígitos, só aceitamos se for uma sigla muito curta (provável marca técnica)
        if len(text) <= 10 and len(words) == 1:
            return True
            
        return False
