from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
import json
import asyncio
from .base_provider import BaseProvider


class TecfilProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://catalogo.tecfil.com.br"
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            verify=False,
            timeout=15.0,
            follow_redirects=True,
        )

    async def fechar(self):
        await self.client.aclose()

    async def _descobrir_imagens(self, fallback_cod: str) -> List[str]:
        base_url = "https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb"
        candidatos = [
            f"{base_url}/{fallback_cod}_A.jpg",
            f"{base_url}/{fallback_cod}A.jpg",
            f"{base_url}/{fallback_cod}.jpg",
            f"{base_url}/{fallback_cod}.png"
        ]
        
        async def check_url(url):
            try:
                resp = await self.client.head(url, timeout=2.0)
                if resp.status_code == 200:
                    return url
            except Exception:
                pass
            return None

        results = await asyncio.gather(*[check_url(u) for u in candidatos])
        valid_urls = [r for r in results if r]
        
        return valid_urls if valid_urls else [f"{base_url}/{fallback_cod}_A.jpg"]

    def parse_balanced_conversions(self, html: str, target_code: str) -> str:
        refs = []
        for match in re.finditer(r'\\?"ReferenciasCruzada\\?":\s*', html):
            start_pos = match.end()
            first_bracket = html.find("[", start_pos)
            if first_bracket == -1:
                continue

            brackets_count = 0
            json_str = ""
            for idx in range(first_bracket, len(html)):
                char = html[idx]
                json_str += char
                if char == '[':
                    brackets_count += 1
                elif char == ']':
                    brackets_count -= 1
                    if brackets_count == 0:
                        break

            try:
                unescaped = json_str.replace('\\"', '"').replace('\\\\', '\\')
                parsed = json.loads(unescaped)
                if isinstance(parsed, list):
                    is_target = False
                    for item in parsed:
                        if item.get("DescricaoFabricante") == "TECFIL":
                            for num_prod in item.get("NumerosProduto", []):
                                if num_prod.get("NumeroProduto") == target_code:
                                    is_target = True
                                    break
                        if is_target:
                            break
                    if is_target or not refs:
                        refs = parsed
                        if is_target:
                            break
            except:
                pass

        formatted_refs = []
        for item in refs:
            brand = item.get("DescricaoFabricante", "").upper()
            if brand == "TECFIL":
                continue
            for num_prod in item.get("NumerosProduto", []):
                ref_code = num_prod.get("NumeroProduto", "").upper()
                if brand and ref_code:
                    formatted_refs.append(f"{brand}: {ref_code}")

        return " | ".join(formatted_refs)

    def parse_specs_html(self, soup: BeautifulSoup) -> Dict[str, str]:
        specs = {}
        # Find the nearest parent container that wraps the specs
        spec_header = soup.find(string=re.compile(r"Especifica", re.I))
        if not spec_header:
            return specs
            
        container = spec_header.parent
        while container:
            text_content = container.get_text()
            if "Função" in text_content and "Elemento Filtrante" in text_content:
                break
            container = container.parent
            
        if not container:
            return specs

        for label in ["Função", "Elemento Filtrante", "Altura (mm)", "Largura (mm)", "Comprimento (mm)"]:
            el = container.find(string=lambda t: t and t.strip().upper().replace(":", "") == label.upper())
            if el:
                parent = el.parent
                all_text = [t.strip() for t in parent.stripped_strings if t.strip()]
                if len(all_text) >= 3 and label.upper() in all_text[0].upper():
                    specs[label.upper()] = all_text[2]
                else:
                    grandparent = parent.parent
                    gp_text = [t.strip() for t in grandparent.stripped_strings if t.strip()]
                    try:
                        idx = -1
                        for i, gt in enumerate(gp_text):
                            if gt.upper().replace(":", "") == label.upper():
                                idx = i
                                break
                        if idx != -1:
                            if idx + 2 < len(gp_text) and gp_text[idx+1] == ":":
                                specs[label.upper()] = gp_text[idx+2]
                            elif idx + 1 < len(gp_text):
                                specs[label.upper()] = gp_text[idx+1]
                    except:
                        pass
        return specs

    async def buscar(self, codigo: str) -> List[Dict[str, Any]]:
        resultados = []
        codigo_buscado = codigo.strip().upper()
        import urllib.parse
        codigo_encoded = urllib.parse.quote(codigo_buscado, safe="")

        try:
            # 1. Fetch search results page
            res_search = await self.client.get(f"{self.base_url}/search/{codigo_encoded}")
            if res_search.status_code != 200:
                print(f"[TECFIL] Falha na busca, status: {res_search.status_code}")
                return []

            soup = BeautifulSoup(res_search.text, "html.parser")
            tables = soup.find_all("table")

            # Table 1 contains the applications
            if len(tables) < 2:
                print("[TECFIL] Nenhuma tabela de aplicações encontrada")
                return []

            table = tables[1]
            current_brand = ""
            parsed_rows = []
            unique_product_ids = set()

            # First pass: parse the HTML table rows
            for r in table.find_all("tr"):
                if r.get("data-fabricante"):
                    current_brand = r.get("data-fabricante").strip().upper()
                    continue

                cells = r.find_all("td")
                if not cells:
                    continue

                first_cell = cells[0]

                # Extract vehicle fields from spans
                modelo_span = first_cell.find(class_=lambda c: c and "DescricaoAplicacao" in c)
                modelo = modelo_span.text.strip() if modelo_span else ""

                versao_span = first_cell.find(class_=lambda c: c and "ComplementoAplicacao3_1" in c)
                versao = versao_span.text.strip() if versao_span else ""

                motor_span = first_cell.find(class_=lambda c: c and "ComplementoAplicacao3_2" in c)
                motor = motor_span.text.strip() if motor_span else ""

                combustivel_span = first_cell.find(class_=lambda c: c and "ComplementoAplicacao3_5" in c)
                combustivel = combustivel_span.text.strip() if combustivel_span else ""

                ano_ini_span = first_cell.find(class_=lambda c: c and "ComplementoAplicacao3_3" in c)
                ano_ini = ano_ini_span.text.strip() if ano_ini_span else ""

                ano_fim_span = first_cell.find(class_=lambda c: c and "ComplementoAplicacao3_4" in c)
                ano_fim = ano_fim_span.text.strip() if ano_fim_span else ""

                # Find the matched product code (highlighted) or any product link
                destaque_a = r.find("a", {"data-rh-produto-destaque": "true"})
                codigo_peca = destaque_a.text.strip() if destaque_a else ""
                product_href = destaque_a.get("href") if destaque_a else ""

                if not codigo_peca:
                    any_a = r.find("a", href=re.compile(r"/produto/"))
                    if any_a:
                        codigo_peca = any_a.text.strip()
                        product_href = any_a.get("href")

                # Extract product ID from href (e.g. /search/acp303/produto/306?aplicacao=249767 -> 306)
                product_id = ""
                if product_href:
                    match = re.search(r"/produto/(\d+)", product_href)
                    if match:
                        product_id = match.group(1)
                        unique_product_ids.add((codigo_peca, product_id))

                parsed_rows.append({
                    "brand": current_brand,
                    "modelo": modelo,
                    "versao": versao,
                    "motor": motor,
                    "combustivel": combustivel,
                    "ano_inicio": ano_ini,
                    "ano_fim": ano_fim,
                    "codigo": codigo_peca or codigo_buscado,
                    "product_id": product_id
                })

            # 2. Fetch product details cache to minimize requests
            details_cache = {}
            for cod, pid in unique_product_ids:
                if not pid:
                    continue
                try:
                    print(f"[TECFIL] Buscando detalhes do produto ID {pid} ({cod})...")
                    res_prod = await self.client.get(f"{self.base_url}/search/{codigo_encoded}/produto/{pid}")
                    if res_prod.status_code == 200:
                        prod_soup = BeautifulSoup(res_prod.text, "html.parser")
                        
                        # Extract conversions
                        conversions = self.parse_balanced_conversions(res_prod.text, cod)
                        
                        # Extract specs
                        specs = self.parse_specs_html(prod_soup)
                        
                        # Extract all image urls
                        images = []
                        def clean_str(s: str) -> str:
                            return re.sub(r'[^A-Z0-9]', '', s.upper())

                        img_matches = re.findall(r'\\?"ArquivoFotoProduto\d*\\?":\s*\\?"([^"]*?)\\?"', res_prod.text)
                        for m in img_matches:
                            if m and m.strip() and clean_str(cod) in clean_str(m):
                                url = f"https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{m.strip()}"
                                if url not in images:
                                    images.append(url)
                                    
                        # Fallback if no images found in JSON
                        if not images:
                            fallback_cod = cod.replace("/", "-")
                            images = await self._descobrir_imagens(fallback_cod)
                                
                        details_cache[pid] = {
                            "referencias": conversions,
                            "ficha_tecnica": specs,
                            "imagem": images[0],
                            "imagens": images
                        }
                except Exception as e:
                    print(f"[TECFIL] Erro ao buscar detalhes do produto {pid}: {e}")

            # 3. Assemble and format final results
            for row in parsed_rows:
                pid = row["product_id"]
                prod_details = details_cache.get(pid, {})
                
                # Format specs correctly
                specs = prod_details.get("ficha_tecnica", {})
                ficha_tecnica = {}
                if specs:
                    ficha_tecnica = {
                        "ALTURA": specs.get("ALTURA (MM)", ""),
                        "LARGURA": specs.get("LARGURA (MM)", ""),
                        "COMPRIMENTO": specs.get("COMPRIMENTO (MM)", ""),
                        "FUNCAO": specs.get("FUNÇÃO", ""),
                        "ELEMENTO": specs.get("ELEMENTO FILTRANTE", "")
                    }
                
                raw = {
                    "veiculo": row["brand"],
                    "modelo": row["modelo"],
                    "versao": row["versao"],
                    "motor": row["motor"],
                    "configuracao_motor": row["combustivel"] or row["motor"],
                    "ano_inicio": row["ano_inicio"],
                    "ano_fim": row["ano_fim"],
                    "observacao": f"Código Original Tecfil: {row['codigo']}",
                    "imagem": prod_details.get("imagem", f"https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{row['codigo']}_A.jpg"),
                    "imagens": prod_details.get("imagens", [f"https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{row['codigo']}_A.jpg"]),
                    "codigo": row["codigo"],
                    "referencias": prod_details.get("referencias", ""),
                    "ficha_tecnica": ficha_tecnica
                }
                resultados.append(self.formatar_resultado(raw))

            # Deduplicate
            resultados_unicos = []
            vistos = set()
            for r in resultados:
                chave = f"{r['veiculo']}|{r['modelo']}|{r.get('versao', '')}|{r['motor']}|{r.get('ano_inicio', '')}|{r.get('ano_fim', '')}|{r['configuracao_motor']}|{r.get('observacao', '')}"
                if chave not in vistos:
                    vistos.add(chave)
                    resultados_unicos.append(r)

            return resultados_unicos

        except Exception as e:
            print(f"[TECFIL] Erro crítico no provider: {str(e)}")
            return []
