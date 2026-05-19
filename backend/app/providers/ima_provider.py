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

                    # Ficha Técnica e Atributos Principais
                    ficha = {
                        "DESCRIÇÃO": product.get("description", "").upper(),
                        "GRUPO": product.get("groupDescription", "").upper()
                    }
                    
                    posicao_extraida = ""
                    lado_extraido = ""

                    for attr in product.get("attributes", []):
                        label = attr.get("label", "")
                        val = attr.get("value", "")
                        if not label or not str(val).strip():
                            continue
                            
                        # Filtrar chaves de controle interno/lixo
                        if "NOME DO ARQUIVO" in label.upper() or "OCULTAR PRODUTO" in label.upper():
                            continue
                            
                        label_upper = label.upper().strip()
                        val_upper = str(val).upper().strip()
                        
                        if "POSIÇÃO" in label_upper or "POSI" in label_upper:
                            posicao_extraida = val_upper
                        elif "LADO" in label_upper:
                            lado_extraido = val_upper
                            
                        ficha[label_upper] = val_upper

                    # Capturar todas as imagens disponíveis
                    imagens = []
                    for key in ["pic01", "pic02", "pic03", "pic04"]:
                        url_img = product.get(key)
                        if url_img and isinstance(url_img, str) and url_img.strip():
                            imagens.append(url_img.strip())

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

                        # Usamos o formatador base para garantir integridade da montadora e veículo
                        res_formatado = self.formatar_resultado({
                            "marca": "IMA",
                            "provedor": "IMA",
                            "codigo": codigo,
                            "modelo": app.get("vehicleName", ""), # Veículo (Ex: COURIER)
                            "montadora": app.get("vehicleManufacturerName", ""), # Montadora (Ex: FORD)
                            "versao": app.get("vehicleDescription", ""),
                            "ano_inicio": ano_ini,
                            "ano_fim": ano_fim,
                            "motor": "", # Deixamos em branco para a base não misturar
                            "configuracao_motor": "", # Deixamos em branco para a base não misturar
                            "combustivel": "", # API não traz combustível separado
                            "posicao": posicao_extraida,
                            "lado": lado_extraido,
                            "observacao": app.get("vehicleType", ""),
                            "referencias": referencias,
                            "imagem": imagens[0] if imagens else imagem,
                            "imagens": imagens,
                            "ficha_tecnica": ficha
                        })

                        # --- OVERRIDE ESPECÍFICO IMA ---
                        # O usuário solicitou que siglas como TSI, MSI, TURBO fiquem inteiras na coluna Motor
                        # em vez de serem extraídas para Configuração.
                        motor_completo = str(app.get("vehicleDescription", "")).upper()
                        config_completa = str(product.get("description", "")).upper()
                        
                        res_formatado["motor"] = motor_completo
                        res_formatado["configuracao_motor"] = config_completa
                        
                        resultados.append(res_formatado)

                return resultados
            except Exception as e:
                print(f"[IMA] Exceção durante a busca: {e}")
                return []
