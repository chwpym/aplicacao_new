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
                # Usamos gather para performance
                detail_tasks = [
                    self._get_product_detail(client, p.get("id")) for p in search_data
                ]
                detailed_products = await asyncio.gather(*detail_tasks)

                for prod in detailed_products:
                    if not prod:
                        continue

                    # Normalização
                    base_res = {
                        "marca": prod.get("brand", {}).get("name", "AUTOEXPERTS"),
                        "codigo": prod.get("partNumber", ""),
                        "imagem": prod.get("mainImage", {}).get("imageUrl", ""),
                        "posicao": "",
                        "configuracao_motor": "",
                        "referencias": "",
                    }

                    # Extrair Posição e outras especificações
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

                    # Extrair Referências OE
                    cross = prod.get("crossReferences", [])
                    refs = [
                        f"{c.get('brand', {}).get('name')}: {c.get('partNumber')}"
                        for c in cross
                    ]
                    base_res["referencias"] = ", ".join(refs)

                    # Veículos (Aplicações)
                    vehicles = prod.get("vehicles", [])
                    for v in vehicles:
                        app = base_res.copy()
                        app.update(
                            {
                                "montadora": v.get("brand", ""),
                                "modelo": v.get("name", ""),
                                "versao": v.get("model", ""),
                                "motor": v.get("engineName", ""),
                                "configuracao_motor": v.get("engineConfiguration", ""),
                                "ano_inicio": str(v.get("startYear", "")),
                                "ano_fim": str(v.get("endYear", "")),
                            }
                        )
                        # CRITICAL: Always use formatar_resultado to trigger Master Catalog and Normalization
                        results.append(self.formatar_resultado(app))

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
