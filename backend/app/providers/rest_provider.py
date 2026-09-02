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

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
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
                                "modelo": str(resolve(map_config.get("modelo")) or ""),
                                "versao": str(resolve(map_config.get("versao")) or resolve("Descriçao do Modelo") or ""),
                                "motor": str(resolve(map_config.get("motor")) or resolve("Motor_PTBR") or ""),
                                "configuracao_motor": str(
                                    resolve(map_config.get("configuracao_motor")) or ""
                                ),
                                "ano_inicio": str(resolve(map_config.get("ano_inicio")) or ""),
                                "ano_fim": str(resolve(map_config.get("ano_fim")) or ""),
                                "combustivel": str(
                                    resolve(map_config.get("combustivel")) or ""
                                ),
                                "observacao": str(
                                    resolve(map_config.get("observacao")) or ""
                                ),
                                "imagem": resolve(map_config.get("imagem")),
                                "referencias": resolve(map_config.get("referencias")),
                                "imagens": [],
                                "ficha_tecnica": resolve(map_config.get("ficha_tecnica")),
                                "codigo": str(
                                    resolve(map_config.get("codigo_peca")) or id_peca
                                ),
                                "provider_id": self.config.get("id"),
                                "provedor": self.config.get("nome", "").upper()
                            }

                            # Correção para Wega: se o ano é único e tem "-->", o fim deve ser aberto
                            if res["ano_inicio"] == res["ano_fim"] and "-->" in res["ano_inicio"]:
                                res["ano_fim"] = ""

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
        Scraper especializado para Wega Motors usando estrutura real li.tit/li.desc
        """
        if "WEGA" not in str(self.config.get("nome", "")).upper():
            return {"ficha_tecnica": {}, "imagens": []}

        import httpx
        from bs4 import BeautifulSoup
        
        # Tenta com o código original e com uma versão com hífen se necessário
        codigos_tentar = [codigo_peca.strip().upper()]
        # Se não tem hífen e parece um código Wega (ex: AKX1967), tenta injetar o hífen (AKX-1967)
        if "-" not in codigo_peca and len(codigo_peca) > 4:
            # Padrão comum: 2 a 4 letras + números
            import re
            match = re.match(r"^([A-Z]{2,4})(\d+)$", codigo_peca.strip().upper())
            if match:
                codigos_tentar.append(f"{match.group(1)}-{match.group(2)}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.wegamotors.com/"
        }

        for cod in codigos_tentar:
            url = f"https://www.wegamotors.com/produto/?cod={cod}"
            try:
                async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                    response = await client.get(url, headers=headers, follow_redirects=True)
                    if response.status_code != 200: continue

                    # Garante encoding correto para evitar caracteres quebrados ()
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    ficha_tecnica = {}
                    
                    def limpar_wega(t):
                        if not t: return ""
                        # Remove o caractere de substituição comum  e normaliza espaços
                        res = t.replace("\ufffd", "ó").replace("\ufffd", "á").replace("\ufffd", "ç").replace("\ufffd", "ã")
                        # Heurística para palavras comuns quebradas
                        res = res.replace("Cdigo", "Código").replace("Descrio", "Descrição").replace("Tcnica", "Técnica")
                        return res.strip()

                    # Estratégia 1: Estrutura real li.tit -> li.desc
                    dados_container = soup.find("div", class_="dados")
                    if dados_container:
                        tits = dados_container.find_all("li", class_="tit")
                        descs = dados_container.find_all("li", class_="desc")
                        for t, d in zip(tits, descs):
                            label = limpar_wega(t.get_text(strip=True).replace(":", ""))
                            val = limpar_wega(d.get_text(strip=True))
                            if label and val:
                                ficha_tecnica[label] = val
                    
                    # Fallback: Estratégia Omni-Search
                    if not ficha_tecnica:
                        labels_alvo = [
                            "Altura", "Comprimento", "Largura", "Espessura", "Tipo de Filtro",
                            "Descrição Técnica", "Código Wega", "Diâmetro Externo", "Rosca"
                        ]
                        all_li = soup.find_all("li")
                        for i in range(len(all_li) - 1):
                            txt = limpar_wega(all_li[i].get_text(strip=True).replace(":", ""))
                            if any(l.lower() in txt.lower() for l in labels_alvo):
                                val = limpar_wega(all_li[i+1].get_text(strip=True))
                                if val and len(val) < 100:
                                    ficha_tecnica[txt] = val

                    # Captura de Imagens
                    imagens = []
                    # 1. Galeria Principal (como no HTML enviado pelo usuário)
                    galeria = soup.find("div", class_="carousel-inner")
                    if galeria:
                        for img in galeria.find_all("img"):
                            src = img.get("src") or img.get("data-src")
                            if src:
                                if src.startswith("/"): src = "https://www.wegamotors.com" + src
                                if src not in imagens: imagens.append(src)
                    
                    # 2. Imagens soltas na div da esquerda
                    esquerda = soup.find("div", class_="esquerda")
                    if esquerda:
                        for img in esquerda.find_all("img"):
                            src = img.get("src") or img.get("data-src")
                            if src and src not in imagens:
                                if src.startswith("/"): src = "https://www.wegamotors.com" + src
                                imagens.append(src)

                    # 3. Fallback determinístico
                    if not imagens:
                        canonical_cod = self.canonicalizar_id_para_imagem(cod)
                        img_pattern = f"https://www.wegamotors.com/wp-content/uploads/pecas/{canonical_cod}.jpg"
                        imagens = [img_pattern, img_pattern.replace(".jpg", "B.jpg"), img_pattern.replace(".jpg", "C.jpg")]

                    # Se encontrou dados, retorna agora
                    if ficha_tecnica or imagens:
                        return {
                            "ficha_tecnica": ficha_tecnica,
                            "imagens": list(dict.fromkeys(imagens))[:6]
                        }
            except Exception as e:
                print(f"Erro no scraper Wega para {cod}: {e}")
                continue
        
        return {"ficha_tecnica": {}, "imagens": []}
