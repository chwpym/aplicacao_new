import httpx
import asyncio
from app.providers.base_provider import BaseProvider
import logging

logger = logging.getLogger(__name__)


class AutoExpertsProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.api_base = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "x-region": "br",
            "origin": "https://www.autoexperts.parts",
        }

    async def buscar(self, part_id: str):
        clean_id = part_id.strip().upper().replace(" ", "")
        results = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                # 1. Busca inicial para obter IDs dos produtos
                search_payload = {"query": clean_id, "skip": 0, "take": 20}
                resp = await client.post(
                    self.api_base, json=search_payload, headers=self.headers
                )

                if resp.status_code != 200:
                    logger.error(
                        f"AutoExperts: Erro na busca inicial ({resp.status_code})"
                    )
                    return []

                search_data = resp.json().get("data", [])
                if not search_data:
                    return []

                # 2. Busca detalhada de cada produto para pegar Motores e Referências OE
                detail_tasks = [
                    self._get_product_detail(client, p.get("id")) for p in search_data
                ]
                detailed_products = await asyncio.gather(*detail_tasks)

                # Cache local para evitar queries repetitivas ao DuckDB (Performance p/ NKJ659)
                norm_cache = {}

                for prod in detailed_products:
                    if not prod:
                        continue

                    part_no = prod.get("partNumber", "")
                    
                    # Base do resultado para este produto
                    brand_data = prod.get("brand") or {}
                    image_data = prod.get("mainImage") or {}
                    
                    base_res = {
                        "marca": brand_data.get("name", "AUTOEXPERTS"),
                        "codigo": part_no,
                        "imagem": image_data.get("imageUrl", ""),
                        "posicao": "",
                        "configuracao_motor": "",
                        "referencias": "",
                    }

                    # Extrair Especificações Técnicas (Ficha)
                    specs = prod.get("specifications", [])
                    spec_list = []
                    for s in specs:
                        desc = s.get("description", "").lower()
                        val = s.get("value", "")
                        if "posi" in desc:
                            base_res["posicao"] = val
                        else:
                            spec_list.append(f"{s.get('description')}: {val}")

                    if spec_list:
                        base_res["observacao"] = " | ".join(spec_list)

                    # Extrair Referências Cruzadas
                    cross = prod.get("crossReferences") or []
                    refs = []
                    for c in cross:
                        c_brand = c.get("brand") or {}
                        refs.append(f"{c_brand.get('name', 'N/A')}: {c.get('partNumber')}")
                    
                    base_res["referencias"] = ", ".join(refs)

                    # Processar Veículos (Aplicações)
                    vehicles = prod.get("vehicles", [])
                    for v in vehicles:
                        montadora_raw = v.get("brand", "").upper()
                        modelo_raw = v.get("name", "").upper()
                        
                        # Chave única para o cache de normalização
                        cache_key = f"{montadora_raw}|{modelo_raw}"
                        
                        app = base_res.copy()
                        app.update({
                            "montadora": montadora_raw,
                            "modelo": modelo_raw,
                            "versao": v.get("model", "").upper(),
                            "motor": v.get("engineName", "").upper(),
                            "configuracao_motor": v.get("engineConfiguration", "").upper(),
                            "ano_inicio": str(v.get("startYear", "")),
                            "ano_fim": str(v.get("endYear", "")),
                        })

                        # Se já normalizamos essa combinação neste loop, usamos o cache
                        if cache_key in norm_cache:
                            m_padrao, mod_padrao = norm_cache[cache_key]
                            app["montadora"] = m_padrao
                            app["modelo"] = mod_padrao
                            # Formata o resto (referências, motorização) sem re-validar montadora
                            results.append(self.formatar_resultado(app, skip_automaker=True))
                        else:
                            # Primeira vez: Formata normalmente e salva no cache
                            res_formatado = self.formatar_resultado(app)
                            norm_cache[cache_key] = (res_formatado["veiculo"], res_formatado["modelo"])
                            results.append(res_formatado)

                return results

            except Exception as e:
                logger.error(f"AutoExperts: Erro na busca: {str(e)}")
                return []

    async def _get_product_detail(self, client, prod_id):
        if not prod_id:
            return None
        try:
            url = f"{self.api_base}/{prod_id}"
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"AutoExperts: Erro ao obter detalhe {prod_id}: {str(e)}")
        return None
