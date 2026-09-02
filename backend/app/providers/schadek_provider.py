import httpx
from app.providers.base_provider import BaseProvider
import logging

logger = logging.getLogger(__name__)


class SchadekProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }

    async def buscar(self, part_id: str):
        # Limpar código: Schadek usa hifens/pontos/espaços às vezes.
        # Exemplo: 20089 ou 20.089
        clean_id = part_id.strip().upper().replace(" ", "").replace(".", "").replace("-", "")
        results = []

        # Vamos consultar a API da Schadek
        url = f"https://schadek.com.br/api/domain/products/code/{clean_id}"
        
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
            try:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    logger.error(f"Schadek: Erro ao consultar API ({resp.status_code})")
                    return []
                
                data = resp.json()
                if not data or not isinstance(data, list):
                    return []

                for prod in data:
                    internal_code = prod.get("code")
                    if not internal_code:
                        continue

                    # Código Schadek: preferencialmente oldCode (ex: 20.089) ou code (ex: 90000520)
                    part_no = prod.get("oldCode") or str(internal_code)
                    if not part_no:
                        part_no = clean_id
                        
                    name = prod.get("name", "BOMBA").upper()
                    observation = prod.get("observation", "")

                    # 1. Obter Imagem de Alta Resolução usando o internal_code de 8 dígitos
                    imagem_url = f"https://schadek.com.br/api/static/products-images/{internal_code}"
                    
                    # 2. Consultar as referências originais (OEM) concorrentemente via API
                    referencias_originais = ""
                    ref_url = f"https://schadek.com.br/api/domain/product/{internal_code}/automakers-references"
                    try:
                        ref_resp = await client.get(ref_url, headers=self.headers)
                        if ref_resp.status_code == 200:
                            ref_data = ref_resp.json()
                            if ref_data and isinstance(ref_data, list):
                                ref_parts = []
                                for ref_item in ref_data:
                                    aut_name = ref_item.get("automaker", "").strip()
                                    ref_code = ref_item.get("referenceCode", "").strip().replace("/", "").replace(" ", "")
                                    if aut_name and ref_code:
                                        ref_parts.append(f"{aut_name}: {ref_code}")
                                referencias_originais = " | ".join(ref_parts)
                    except Exception as e:
                        logger.warning(f"Schadek: Erro ao buscar referências para produto {internal_code}: {e}")
                    
                    apps_dict = prod.get("applications") or {}
                    apps_list = apps_dict.get("$values") or []

                    # Para evitar re-normalização pesada no mesmo loop
                    norm_cache = {}

                    for app in apps_list:
                        montadora_raw = app.get("automaker", "").upper().strip()
                        modelo_raw = app.get("model", "").upper().strip()
                        
                        if not montadora_raw or not modelo_raw:
                            continue

                        cache_key = f"{montadora_raw}|{modelo_raw}"
                        
                        # Preparar resultado no padrão unificado
                        app_data = {
                            "marca": "SCHADEK",
                            "codigo": part_no,
                            "montadora": montadora_raw,
                            "modelo": modelo_raw,
                            "versao": "",
                            "motor": app.get("engineType", "").upper().strip(),
                            "configuracao_motor": app.get("comments", "").upper().strip(),
                            "combustivel": "",
                            "ano_inicio": app.get("initialDate", "").strip(),
                            "ano_fim": app.get("endDate", "").strip(),
                            "observacao": f"{name} | {observation}".strip(" |"),
                            "imagem": imagem_url,
                            "referencias": referencias_originais,
                        }

                        # Normalização inteligente baseada no Master Catalog
                        if cache_key in norm_cache:
                            m_padrao, mod_padrao = norm_cache[cache_key]
                            app_data["montadora"] = m_padrao
                            app_data["modelo"] = mod_padrao
                            results.append(self.formatar_resultado(app_data, skip_automaker=True))
                        else:
                            res_formatado = self.formatar_resultado(app_data)
                            norm_cache[cache_key] = (res_formatado["veiculo"], res_formatado["modelo"])
                            results.append(res_formatado)

                return results

            except Exception as e:
                logger.error(f"Schadek: Erro ao buscar {part_id}: {str(e)}")
                return []
