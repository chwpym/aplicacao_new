import httpx
import base64
import json
import logging
from app.providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

class IrbProvider(BaseProvider):
    def __init__(self, provider_config: dict):
        self.config = provider_config
        self.client = httpx.AsyncClient(timeout=30.0, verify=False)
        self.url = self.config.get("url") or "https://catalogoexpresso.com.br/ideia2001/api/v1/consulta"
        self.headers = {
            'accept': '*/*',
            'origin': 'https://irbauto.com',
            'referer': 'https://irbauto.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

    def _pad_base64(self, s: str) -> str:
        return s + "=" * ((4 - len(s) % 4) % 4)

    def _decode_ideia2001(self, raw_text: str) -> dict:
        try:
            decoded_text = base64.b64decode(self._pad_base64(raw_text)).decode('utf-8', errors='ignore')
            parts = decoded_text.split("<!1!>")
            if len(parts) > 1:
                b64_data = parts[1]
                idx = b64_data.find("eyJzdWNjZXNz")
                if idx != -1:
                    part_end = b64_data[:idx]
                    part_start = b64_data[idx:]
                    full_b64 = part_start + part_end
                    decoded_json = base64.b64decode(self._pad_base64(full_b64)).decode('utf-8', errors='ignore')
                    return json.loads(decoded_json)
        except Exception as e:
            logger.error(f"[IRB Provider] Erro ao decodificar base64 do Ideia2001: {e}")
        return {}

    async def buscar(self, part_number: str) -> list[dict]:
        params = {
            "chavePerfil": "8393bf0e-8e28-4562-b6a2-94bb5a9723a1",
            "idConsulta": "PESQUISA",
            "tabAtiva": "0",
            "idm": "pt",
            "filtros": f"PCS<!2!>{part_number}",
            "buscaExata": "",
            "ordenacao": "numero-produto",
            "limit": "10",
            "offset": "0"
        }
        
        try:
            response = await self.client.get(self.url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data_dict = self._decode_ideia2001(response.text)
            produtos = data_dict.get("data", [])
            
            resultados = []
            
            for prod in produtos:
                base_info = {
                    "marca": "IRB",
                    "codigo": prod.get("NumeroProduto", part_number),
                    "imagem": "",
                    "imagens": []
                }
                
                # Imagens (https://www.c123.com.br/CatalogoExpresso/315/FotoProdWeb/)
                for i in range(1, 4):
                    foto_key = "ArquivoFotoProduto" if i == 1 else f"ArquivoFotoProduto{i}"
                    foto = prod.get(foto_key)
                    if foto:
                        img_url = f"https://www.c123.com.br/CatalogoExpresso/315/FotoProdWeb/{foto}"
                        base_info["imagens"].append(img_url)
                        if not base_info["imagem"]:
                            base_info["imagem"] = img_url

                # Ficha Tecnica
                ficha = {"description": prod.get("DescricaoProduto") or "ROLAMENTO", "specifications": []}
                cpo3 = prod.get("CpoAuxProd3")
                if cpo3:
                    ficha["specifications"].append({"description": "Construção", "value": cpo3})
                cpo6 = prod.get("CpoAuxProd6")
                if cpo6:
                    ficha["specifications"].append({"description": "d (Interno)", "value": cpo6})
                cpo8 = prod.get("CpoAuxProd8")
                if cpo8:
                    ficha["specifications"].append({"description": "D (Externo)", "value": cpo8})
                cpo10 = prod.get("CpoAuxProd10")
                if cpo10:
                    ficha["specifications"].append({"description": "B (Largura)", "value": cpo10})
                    
                base_info["ficha_tecnica"] = ficha
                
                # Busca detalhes do produto para pegar TODAS as referencias cruzadas
                codigo_produto = prod.get("CodigoProduto")
                refs = prod.get("ReferenciasCruzada", [])
                
                if codigo_produto:
                    params_detalhes = {
                        "chavePerfil": "8393bf0e-8e28-4562-b6a2-94bb5a9723a1",
                        "idConsulta": "PESQUISA_DETALHES",
                        "idm": "pt",
                        "filtros": f"CodigoProduto<!2!>{codigo_produto}"
                    }
                    try:
                        resp_det = await self.client.get(self.url, headers=self.headers, params=params_detalhes)
                        if resp_det.status_code == 200:
                            data_det = self._decode_ideia2001(resp_det.text)
                            if data_det.get("data") and len(data_det["data"]) > 0:
                                refs = data_det["data"][0].get("ReferenciasCruzada", [])
                    except Exception as e:
                        logger.warning(f"[IRB Provider] Erro ao buscar detalhes do produto {codigo_produto}: {e}")

                # Referencias Cruzadas (Similares)
                similares = []
                for ref in refs:
                    fab = ref.get("DescricaoFabricante", "")
                    for num in ref.get("NumerosProduto", []):
                        num_prod = num.get('NumeroProduto', '')
                        if num_prod:
                            similares.append(f"{fab}: {num_prod}")
                if similares:
                    base_info["referencias"] = similares
                
                # Aplicações
                fabricantes = prod.get("FabricantesAplicacao", [])
                for fab in fabricantes:
                    montadora = fab.get("DescricaoFabricante", "")
                    for app in fab.get("Aplicacoes", []):
                        modelo = app.get("DescricaoAplicacao", "")
                        posicao = app.get("ComplementoAplicacao3_2", "")
                        complemento = app.get("ComplementoAplicacao3_3", "") # Motor/Ano
                        
                        item = base_info.copy()
                        item["montadora"] = montadora
                        item["modelo"] = modelo
                        item["posicao"] = posicao
                        item["observacao"] = complemento
                        item["motor"] = complemento
                        
                        resultados.append(self.formatar_resultado(item))
                        
            return resultados
        except Exception as e:
            logger.error(f"[IRB Provider] Erro geral na busca: {e}")
            return []
