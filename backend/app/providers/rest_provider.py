import httpx
from app.providers.base_provider import BaseProvider


class RESTProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = config["url"]
        self.headers = config.get("headers", {})

    async def buscar(self, id_peca: str):
        # Gera variações do ID para busca (com/sem hífens)
        codigos_busca = self.normalizar_codigo(id_peca)

        async with httpx.AsyncClient(timeout=30.0) as client:
            for cod in codigos_busca:
                try:
                    url = self.url.replace("{id}", cod).replace("{codigo}", cod)
                    print(f"[{self.config.get('nome')}] Tentando URL: {url}")
                    response = await client.get(url, headers=self.headers)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    if not data:
                        continue

                    import json

                    map_config = {}
                    if self.config.get("mapeamento"):
                        try:
                            map_config = json.loads(self.config["mapeamento"])
                        except:
                            pass

                    def get_val(obj, path):
                        if not path or obj is None:
                            return None
                        if path.startswith("."):
                            path = path[1:]  # Support .key or key
                        parts = path.split(".")
                        curr = obj
                        for p in parts:
                            if isinstance(curr, dict):
                                # Try exact match first
                                if p in curr:
                                    curr = curr[p]
                                else:
                                    # Fallback: case-insensitive
                                    found = False
                                    for k, v in curr.items():
                                        if k.lower() == p.lower():
                                            curr = v
                                            found = True
                                            break
                                    if not found:
                                        return None
                            elif isinstance(curr, list) and p.isdigit():
                                idx = int(p)
                                curr = curr[idx] if idx < len(curr) else None
                            else:
                                return None
                        return curr

                    # Determine the list of items using the container path
                    container_path = map_config.get("container")
                    if container_path:
                        items = get_val(data, container_path)
                        if not isinstance(items, list):
                            items = [items] if items else []
                    else:
                        items = data if isinstance(data, list) else [data]

                    # Pre-extract "global" references if they exist at root level (Wega pattern)
                    global_refs = ""
                    def resolve_path(obj, path):
                        return get_val(obj, path)
                    
                    raw_refs = get_val(data, "conversoes") or resolve_path(data, map_config.get("referencias_root"))
                    if isinstance(raw_refs, list):
                        formatted_global = []
                        for r in raw_refs:
                            if isinstance(r, dict):
                                m = r.get("Marca") or r.get("marca") or r.get("brand") or r.get("Brand")
                                c = r.get("Código Concorrente") or r.get("codigo") or r.get("code") or r.get("Código")
                                if c:
                                    formatted_global.append(f"{m}: {c}" if m else str(c))
                        global_refs = " | ".join(formatted_global)

                    resultados = []
                    for item in items:
                        if map_config:
                            def resolve(path):
                                if not path:
                                    return None
                                if path.startswith("root:"):
                                    return get_val(data, path[5:])
                                return get_val(item, path)

                            res = {
                                "marca": str(resolve(map_config.get("marca")) or ""),
                                "veiculo": str(resolve(map_config.get("veiculo")) or ""),
                                "modelo": str(resolve(map_config.get("modelo")) or resolve("Descrição do Modelo") or ""),
                                "motor": str(resolve(map_config.get("motor")) or resolve("Motor_PTBR") or ""),
                                "configuracao_motor": str(
                                    resolve(map_config.get("configuracao_motor")) or ""
                                ),
                                "ano_inicio": str(
                                    resolve(map_config.get("ano_inicio")) or ""
                                ),
                                "ano_fim": str(
                                    resolve(map_config.get("ano_fim")) or ""
                                ),
                                "observacao": str(
                                    resolve(map_config.get("observacao")) or ""
                                ),
                                "imagem": resolve(map_config.get("imagem")),
                                "referencias": resolve(map_config.get("referencias")),
                                "imagens": [],
                                "ficha_tecnica": resolve(map_config.get("ficha_tecnica")),
                                "codigo": str(
                                    resolve(map_config.get("codigo_peca")) or ""
                                ),
                                "provider_id": self.config.get("id"),
                                "provedor": self.config.get("nome", "").upper()
                            }

                            # Injetar referências globais se o campo local estiver vazio
                            if not res["referencias"] and global_refs:
                                res["referencias"] = global_refs

                            # Suporte a padrão de imagem calculado
                            img_pattern = map_config.get("image_pattern")
                            if img_pattern:
                                id_for_img = res["codigo"] or id_peca
                                canonical_id = self.canonicalizar_id_para_imagem(id_for_img)
                                base_img = img_pattern.replace("{id}", canonical_id)
                                res["imagem"] = base_img
                                res["imagens"] = [
                                    base_img,
                                    base_img.replace(".jpg", "B.jpg").replace(".png", "B.png"),
                                    base_img.replace(".jpg", "C.jpg").replace(".png", "C.png"),
                                ]

                            # Special case: if references is a list of objects, format it
                            refs = res["referencias"]
                            if isinstance(refs, list):
                                ref_m_path = map_config.get("ref_marca")
                                ref_c_path = map_config.get("ref_codigo")
                                formatted_refs = []
                                for r in refs:
                                    if isinstance(r, dict):
                                        code = get_val(r, ref_c_path) if ref_c_path else (r.get("code") or r.get("numero") or r.get("value") or r.get("Código Concorrente"))
                                        brand = get_val(r, ref_m_path) if ref_m_path else (r.get("brand") or r.get("marca") or r.get("key") or r.get("Marca"))
                                        if code:
                                            formatted_refs.append(f"{brand}: {code}" if brand else str(code))
                                    elif isinstance(r, str): formatted_refs.append(r)
                                    elif isinstance(r, (int, float)): formatted_refs.append(str(r))
                                res["referencias"] = " | ".join(formatted_refs)

                            # Tradução de chave interna do REST para o que a BaseProvider espera:
                            # O mapeamento do banco usa "veiculo" para guardar a Montadora (ex: HYUNDAI, KIA).
                            # A BaseProvider procura "brand" ou "montadora" para preencher a coluna Montadora.
                            # Sem essa tradução, "veiculo" cai na coluna Veículo (comportamento errado).
                            if "veiculo" in res and res["veiculo"]:
                                res["montadora"] = res.pop("veiculo")

                            formatted = self.formatar_resultado(res)
                            if not resultados and data:
                                formatted["raw_response"] = json.dumps(data, indent=2, ensure_ascii=False)
                            resultados.append(formatted)
                        else:
                            formatted = self.formatar_resultado(item)
                            if not resultados and data:
                                formatted["raw_response"] = json.dumps(data, indent=2, ensure_ascii=False)
                            resultados.append(formatted)

                    if resultados:
                        return resultados
                except Exception as e:
                    print(f"[{self.config.get('nome')}] Erro buscando código {cod}: {e}")
                    continue
        return []

    async def get_details(self, codigo_peca: str) -> dict:
        """
        Implementação específica para Wega que faz Scraping da página de produto
        para obter dados técnicos (ficha técnica) e imagens extras.
        """
        if "WEGA" not in str(self.config.get("nome", "")).upper():
            return {"ficha_tecnica": {}, "imagens": []}

        # Para Detalhes Wega, o código com hífen é crucial (ex: WO-130)
        url = f"https://www.wegamotors.com/produto/?cod={codigo_peca.strip().upper()}"
        
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                if response.status_code != 200:
                    return {"ficha_tecnica": {}, "imagens": []}

                soup = BeautifulSoup(response.text, 'html.parser')
                ficha_tecnica = {}
                
                # Lista de rótulos técnicos para capturar
                labels_alvo = [
                    "Altura", "Diâmetro Externo", "Diâmetro Interno", 
                    "Rosca", "Válvula Anti-retorno", "Válvula By-pass",
                    "Comprimento", "Largura", "Espessura", "Tipo de Filtro"
                ]
                
                # Estratégia 1: Buscar o título "Dados Técnicos" e capturar os itens seguintes
                dados_tecnicos_anchor = soup.find(string=lambda t: t and "Dados Técnicos" in t)
                if dados_tecnicos_anchor:
                    # No Elementor/Wega, os dados costumam vir em uma lista (ul/li) ou divs adjacentes
                    container = dados_tecnicos_anchor.find_parent(['div', 'section'])
                    if container:
                        # Busca todos os itens que pareçam rótulos ou valores
                        items = container.find_all(['li', 'span', 'p', 'div'], recursive=True)
                        current_label = None
                        for item in items:
                            text = item.get_text(strip=True)
                            if not text or len(text) > 50: continue
                            
                            # Se o texto for um dos nossos labels conhecidos, marcamos como label atual
                            is_label = any(l.lower() in text.lower() for l in labels_alvo)
                            if is_label:
                                # Limpa o label (remove ":" se tiver)
                                current_label = text.split(":")[0].strip()
                            elif current_label:
                                # Se temos um label e o texto atual não é label, é o valor!
                                ficha_tecnica[current_label] = text
                                current_label = None # Reseta para o próximo par

                # Estratégia 2 (Fallback): Se an an Estratégia 1 falhou, tentamos o mapeamento direto de texto
                if not ficha_tecnica:
                    all_text_nodes = [t.strip() for t in soup.find_all(string=True) if t.strip()]
                    for i in range(len(all_text_nodes) - 1):
                        txt = all_text_nodes[i]
                        # Se achou um label, o próximo costuma ser o valor
                        if any(l.lower() == txt.lower() or (l.lower() + ":") == txt.lower() for l in labels_alvo):
                            val = all_text_nodes[i+1]
                            if val and len(val) < 50:
                                label_clean = txt.replace(":", "").strip()
                                ficha_tecnica[label_clean] = val

                # Imagens: Scraper real de tags <img> e fallback para o padrão conhecido
                imagens = []
                # OG Image é sempre uma boa candidata para an an principal
                og_image = soup.find("meta", property="og:image")
                if og_image:
                    imagens.append(og_image["content"])
                
                # Scraper de imagens do produto
                for img in soup.find_all("img"):
                    src = img.get("src") or img.get("data-src")
                    if src and ("produto" in src or "uploads" in src) and ".jpg" in src:
                        if src not in imagens:
                            imagens.append(src)

                # Mantém o gerador de variantes se não achou nada no scraping
                if len(imagens) < 2:
                    canonical_cod = self.canonicalizar_id_para_imagem(codigo_peca)
                    img_pattern = f"https://www.wegamotors.com/wp-content/uploads/pecas/{canonical_cod}.jpg"
                    if img_pattern not in imagens: imagens.append(img_pattern)
                    imagens.append(img_pattern.replace(".jpg", "B.jpg"))
                    imagens.append(img_pattern.replace(".jpg", "C.jpg"))

                return {
                    "ficha_tecnica": ficha_tecnica,
                    "imagens": list(dict.fromkeys(imagens))[:6] # Limita e remove duplicatas
                }

        except Exception as e:
            print(f"Erro ao fazer scraping da Wega para {codigo_peca}: {e}")
            return {"ficha_tecnica": {}, "imagens": []}
