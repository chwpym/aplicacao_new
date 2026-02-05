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

                    resultados = []
                    for item in items:
                        if map_config:
                            # For each result, mapping is relative to the item
                            # Use root: prefix to access the full JSON response
                            def resolve(path):
                                if not path:
                                    return None
                                if path.startswith("root:"):
                                    return get_val(data, path[5:])
                                return get_val(item, path)

                            res = {
                                "marca": str(resolve(map_config.get("marca")) or ""),
                                "veiculo": str(
                                    resolve(map_config.get("veiculo")) or ""
                                ),
                                "modelo": str(resolve(map_config.get("modelo")) or ""),
                                "motor": str(resolve(map_config.get("motor")) or ""),
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
                                "codigo": str(
                                    resolve(map_config.get("codigo_peca")) or ""
                                ),
                            }

                            # Suporte a padrão de imagem calculado (ex: https://site.com/{id}.jpg)
                            img_pattern = map_config.get("image_pattern")
                            if img_pattern:
                                # Prioriza o código extraído da resposta se existir
                                # Aplica canonicalização para garantir Maiúsculas e Hífen (padrão WEGA)
                                id_for_img = res["codigo"] or id_peca
                                canonical_id = self.canonicalizar_id_para_imagem(
                                    id_for_img
                                )

                                base_img = img_pattern.replace("{id}", canonical_id)
                                res["imagem"] = base_img
                                # Gera automaticamente variações B e C que são comuns em catálogos
                                res["imagens"] = [
                                    base_img,
                                    base_img.replace(".jpg", "B.jpg").replace(
                                        ".png", "B.png"
                                    ),
                                    base_img.replace(".jpg", "C.jpg").replace(
                                        ".png", "C.png"
                                    ),
                                ]

                            # Special case: if references is a list of objects, format it using configured paths
                            refs = res["referencias"]
                            if isinstance(refs, list):
                                ref_m_path = map_config.get("ref_marca")
                                ref_c_path = map_config.get("ref_codigo")

                                formatted_refs = []
                                for r in refs:
                                    if isinstance(r, dict):
                                        # Use map_config paths OR common fallbacks
                                        code = (
                                            get_val(r, ref_c_path)
                                            if ref_c_path
                                            else (
                                                r.get("code")
                                                or r.get("numero")
                                                or r.get("value")
                                            )
                                        )
                                        brand = (
                                            get_val(r, ref_m_path)
                                            if ref_m_path
                                            else (
                                                r.get("brand")
                                                or r.get("marca")
                                                or r.get("key")
                                            )
                                        )
                                        if code:
                                            formatted_refs.append(
                                                f"{brand}: {code}"
                                                if brand
                                                else str(code)
                                            )
                                    elif isinstance(r, str):
                                        formatted_refs.append(r)
                                    elif isinstance(r, (int, float)):
                                        formatted_refs.append(str(r))
                                res["referencias"] = " | ".join(formatted_refs)

                            formatted = self.formatar_resultado(res)
                            # Add raw response to the first item for debugging in Playground
                            if not resultados and data:
                                formatted["raw_response"] = json.dumps(
                                    data, indent=2, ensure_ascii=False
                                )
                            resultados.append(formatted)
                        else:
                            formatted = self.formatar_resultado(item)
                            if not resultados and data:
                                formatted["raw_response"] = json.dumps(
                                    data, indent=2, ensure_ascii=False
                                )
                            resultados.append(formatted)

                    if resultados:
                        return resultados
                except Exception as e:
                    print(
                        f"Erro no provedor REST {self.config.get('nome')} com código {cod}: {e}"
                    )
                    continue

            return []
