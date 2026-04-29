import httpx
import re
from typing import List, Dict, Any
from app.providers.base_provider import BaseProvider

class IMAProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = config.get("url", "https://search-api.wedigi.house/api/ima/filters/items/search")
        self.headers = {
            "Accept": "*/*",
            "Origin": "https://ima.ind.br",
            "Referer": "https://ima.ind.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Busca na nova API REST da IMA (WeDigi).
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # A API usa o termo purificado (sem espaços/hifens as vezes ajuda, mas vamos mandar o original)
                params = {"query": termo}
                response = await client.get(self.url, params=params, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"[IMA] Erro na busca: {response.status_code}")
                    return []
                
                data = response.json()
                if not isinstance(data, list):
                    return []

                resultados = []
                for entry in data:
                    product = entry.get("product", {})
                    applications = entry.get("productApplication", [])
                    
                    if not product or not applications:
                        continue

                    # Dados do Produto
                    codigo = product.get("code", "")
                    # Pegar imagem do pic01
                    imagem = product.get("pic01", "")
                    
                    # Referências Cruzadas
                    refs = []
                    for m_map in product.get("manufacturerMapping", []):
                        brand = m_map.get("manufacturerName", "").upper()
                        p_code = m_map.get("manufacturerProductCode", "")
                        if brand and p_code:
                            refs.append(f"{brand}: {p_code}")
                    referencias = " | ".join(refs)

                    # Ficha Técnica
                    ficha = {
                        "Descrição": product.get("description", ""),
                        "Grupo": product.get("groupDescription", "")
                    }
                    for attr in product.get("attributes", []):
                        label = attr.get("label")
                        val = attr.get("value")
                        if label and val:
                            ficha[label] = val

                    # Processar Aplicações
                    for app in applications:
                        # Extrair Anos (Ex: 1999 > 2007)
                        ano_str = app.get("vehicleYear", "")
                        ano_ini = ""
                        ano_fim = ""
                        if ">" in ano_str:
                            partes = [p.strip() for p in ano_str.split(">")]
                            ano_ini = partes[0]
                            ano_fim = partes[1] if len(partes) > 1 else ""
                        else:
                            ano_ini = ano_str

                        # Usamos o formatador base para garantir integridade e normalização
                        resultados.append(self.formatar_resultado({
                            "marca": "IMA",
                            "provedor": "IMA",
                            "codigo": codigo,
                            "modelo": app.get("vehicleName", ""), # Veículo (Ex: COURIER)
                            "montadora": app.get("vehicleManufacturerName", ""), # Montadora (Ex: FORD)
                            "versao": app.get("vehicleDescription", ""),
                            "ano_inicio": ano_ini,
                            "ano_fim": ano_fim,
                            "motor": "", # API não traz motor separado na aplicação
                            "configuracao_motor": "",
                            "combustivel": "", # API não traz combustível separado
                            "observacao": app.get("vehicleType", ""),
                            "referencias": referencias,
                            "imagem": imagem,
                            "imagens": [imagem] if imagem else [],
                            "ficha_tecnica": ficha
                        }))

                return resultados
            except Exception as e:
                print(f"[IMA] Exceção durante a busca: {e}")
                return []
