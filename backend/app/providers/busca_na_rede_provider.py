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
    Suporta múltiplas marcas (Sampel, Tuba Cabos, TC Chicotes, etc.) via brand_slug configurável.
    
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
                
                # Busca links de produtos (h2 a, h3 a são o padrão do Busca na Rede)
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
                    tasks.append(self._hydrate_product(client, url, termo, marca_peca))

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

            # 3. Extrair dados do og:description (contém aplicações + referências)
            og_desc = soup.find("meta", {"property": "og:description"})
            desc_text = og_desc.get("content", "") if og_desc else ""

            if not desc_text:
                meta_desc = soup.find("meta", {"name": "description"})
                desc_text = meta_desc.get("content", "") if meta_desc else ""

            if not desc_text:
                logger.info("BUSCA_NA_REDE", f"Sem og:description em {url}")
                return []

            # 4. Pré-processar blocos
            # Formato Tuba: "MONTADORA×3 MODELO×3 VERSÃO×3 ANOS... MOTOR" (tudo junto)
            # Formato Sampel: "MONTADORA×3 MODELO×3" + "ANOS..." (separados)
            raw_blocks = re.split(r'\s{2,}', desc_text.strip())

            items = []
            referencias = []
            
            # Pré-processamento: Limpar e classificar cada bloco
            cleaned = []
            for b in raw_blocks:
                b = b.strip()
                if not b or b == "-" or "Publicado" in b:
                    continue
                if b.startswith("-"):
                    refs = [r.strip().upper() for r in b.split("-") if r.strip()]
                    referencias.extend(refs)
                    continue
                cleaned.append(b)

            # Juntar blocos consecutivos: texto (veículo) + anos
            merged_blocks = []
            i = 0
            while i < len(cleaned):
                block = cleaned[i]
                has_year = bool(re.search(r'\b(19[5-9]\d|20[0-3]\d)\b', block))
                has_letters = bool(re.search(r'[A-Za-z]', block))

                if has_year and has_letters:
                    # Bloco completo (formato Tuba): veículo + anos juntos
                    merged_blocks.append(block)
                elif has_letters and not has_year:
                    # Bloco só com texto (formato Sampel): verifica se o próximo é de anos
                    if i + 1 < len(cleaned):
                        next_block = cleaned[i + 1]
                        next_has_year = bool(re.search(r'\b(19[5-9]\d|20[0-3]\d)\b', next_block))
                        if next_has_year:
                            merged_blocks.append(f"{block} {next_block}")
                            i += 2
                            continue
                    # Sem anos adjacentes -> é referência/metadado
                    clean_upper = block.strip().upper()
                    if len(clean_upper) > 2 and clean_upper not in ("INFERIOR", "SUPERIOR", "DIANTEIRO", "TRASEIRO"):
                        referencias.append(clean_upper)
                elif has_year and not has_letters:
                    # Bloco de anos sozinho sem veículo anterior -> ignora
                    pass
                else:
                    # Bloco sem nada útil
                    clean_upper = block.strip().upper()
                    if len(clean_upper) > 2:
                        referencias.append(clean_upper)
                i += 1

            # Parsear blocos mesclados
            for block in merged_blocks:
                parsed = self._parse_application_block(block)
                if parsed:
                    raw_data = {
                        "marca_peca": marca_peca,
                        "codigo": query.upper(),
                        "montadora": parsed["montadora"],
                        "modelo": parsed["modelo"],
                        "versao": parsed["versao"],
                        "motor": parsed["motor"],
                        "ano_inicio": parsed["ano_inicio"],
                        "ano_fim": parsed["ano_fim"],
                        "imagem": image_url,
                        "ficha_tecnica": {"PRODUTO": product_title} if product_title else {},
                    }
                    items.append(raw_data)

            # Injeta referências em todos os itens
            if referencias:
                ref_str = " | ".join(referencias)
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
        Formato típico: "FIAT FIAT FIAT SIENA SIENA SIENA ATTRACTIVE ATTRACTIVE ATTRACTIVE 1996 ... 2025 1.4, 8V MPI"
        
        Cada campo (montadora, modelo, versão) aparece repetido 3 vezes seguidas.
        """
        if not block:
            return None

        words = block.split()
        if len(words) < 4:
            return None

        # Separar palavras textuais dos anos e dados técnicos
        text_words = []
        years = []
        motor_parts = []
        
        i = 0
        while i < len(words):
            word = words[i]
            # É um ano? (4 dígitos entre 1950-2030)
            if re.match(r'^\d{4}$', word) and 1950 <= int(word) <= 2030:
                years.append(word)
            # É motor? (padrão X.X ou contém vírgula seguida de válvulas)
            elif re.match(r'^\d[\.,]\d', word) or word in ("MPI", "EFI", "MPFI", "16V", "8V"):
                motor_parts.append(word)
            # Vírgula seguida de motor (ex: "1.4,")
            elif word.endswith(",") and re.match(r'^\d[\.,]\d', word.rstrip(",")):
                motor_parts.append(word.rstrip(","))
            elif years or motor_parts:
                # Já passou para a zona de dados técnicos
                motor_parts.append(word)
            else:
                text_words.append(word)
            i += 1

        if not text_words:
            return None

        # Identificar campos repetidos 3 vezes (padrão Busca na Rede)
        # Estratégia: agrupar palavras consecutivas repetidas
        groups = self._extract_repeated_groups(text_words)
        
        montadora = groups[0] if len(groups) > 0 else ""
        modelo = groups[1] if len(groups) > 1 else ""
        versao = groups[2] if len(groups) > 2 else ""

        # Anos
        ano_inicio = years[0] if years else ""
        ano_fim = years[-1] if len(years) > 1 else ""
        # Se todos os anos são iguais, não tem fim
        if ano_inicio == ano_fim:
            ano_fim = ""

        # Motor
        motor = " ".join(motor_parts).strip()

        return {
            "montadora": montadora,
            "modelo": modelo,
            "versao": versao,
            "motor": motor,
            "ano_inicio": ano_inicio,
            "ano_fim": ano_fim,
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
