import httpx
import asyncio
import re
from typing import List, Dict, Any, Optional
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger

class SchaefflerProvider(BaseProvider):
    """
    Provedor para o catálogo Schaeffler (LUK, FAG, INA).
    Usa a API REST do portal Vehicle Lifetime Solutions.
    
    Arquitetura: Discovery → Hydration (3 níveis)
    1. Discovery: Busca produto por código -> product_id + manufacturers
    2. Hydration L1: Busca séries de modelos para cada montadora (modelSeries)
    3. Hydration L2: Busca detalhes técnicos para cada série (targets)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base = "https://vehiclelifetimesolutions.schaeffler.com.br/api/AAM-BR"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/search/results",
            "Origin": "https://vehiclelifetimesolutions.schaeffler.com.br",
            "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        self.common_params = {
            "lang": "pt_BR",
            "curr": "BRL",
            "catalogCountry": "BR"
        }

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Orquestra a busca no catálogo Schaeffler.
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                # --- FASE 1: DISCOVERY ---
                products = await self._discover_products(client, termo)
                if not products:
                    logger.warning("SCHAEFFLER", f"Produto não encontrado: {termo}")
                    return []

                all_results = []
                
                # Para cada produto encontrado (geralmente apenas 1 relevante)
                for product in products:
                    product_code = product.get("code")
                    if not product_code:
                        continue
                    
                    # --- FASE PARALELA: OE Numbers + Detalhes + Kit + Montadoras ---
                    # Dispara todas as buscas em paralelo para máxima performance
                    oe_task = self._fetch_oe_numbers(client, product_code)
                    detail_task = self._fetch_product_detail(client, product_code)
                    kit_task = self._fetch_kit_contents(client, product_code)
                    mfr_task = self._fetch_manufacturers_fallback(client, product_code)
                    
                    # Extrai montadoras do search primeiro (pode já vir)
                    manufacturers = product.get("linkages", {}).get("manufacturers", [])
                    
                    if manufacturers:
                        # Se já tem montadoras, não precisa do fallback
                        referencias, product_info, kit_contents = await asyncio.gather(oe_task, detail_task, kit_task)
                    else:
                        # Precisa do fallback de montadoras
                        logger.info("SCHAEFFLER", f"Buscando montadoras via endpoint para {product_code}")
                        referencias, product_info, kit_contents, manufacturers = await asyncio.gather(oe_task, detail_task, kit_task, mfr_task)
                    
                    # Injeta composição do kit no product_info
                    product_info["composicao"] = kit_contents

                    if not manufacturers:
                        # Se ainda não tiver aplicações, retorna o dado básico do produto
                        all_results.append(self._format_product_only(product, referencias, product_info))
                        continue

                    # --- FASE 2: HYDRATION L1 (Model Series) ---
                    series_tasks = [
                        self._fetch_model_series(client, product_code, mfr.get("uuid"))
                        for mfr in manufacturers if mfr.get("uuid")
                    ]
                    
                    series_responses = await asyncio.gather(*series_tasks)
                    
                    # --- FASE 3: HYDRATION L2 (Targets/Veículos) ---
                    target_tasks = []
                    brand_name = product.get("brand", {}).get("name", "SCHAEFFLER").upper()
                    article_code = product.get("catalogArticleNumber", "")
                    for i, series_list in enumerate(series_responses):
                        mfr_name = manufacturers[i].get("name", "")
                        for series in series_list:
                            series_code = series.get("uuid")
                            if series_code:
                                target_tasks.append(
                                    self._fetch_targets(client, product_code, series_code, mfr_name, series.get("name", ""), referencias, brand_name, article_code, product_info)
                                )

                    # Dispara busca de todos os veículos em paralelo
                    chunk_size = 15
                    for i in range(0, len(target_tasks), chunk_size):
                        chunk = target_tasks[i:i + chunk_size]
                        target_responses = await asyncio.gather(*chunk)
                        for target_list in target_responses:
                            all_results.extend(target_list)

                return all_results

            except Exception as e:
                logger.error("SCHAEFFLER", f"Erro ao buscar '{termo}': {str(e)}")
                return []

    async def _fetch_manufacturers_fallback(self, client: httpx.AsyncClient, product_code: str) -> List[Dict]:
        """Busca montadoras caso a busca inicial não retorne o campo linkages."""
        try:
            params = {
                **self.common_params,
                "targetTypeCodes": "passengerCar",
                "globalCarPark": "false"
            }
            url = f"{self.api_base}/products/{product_code}/linkages/manufacturers"
            response = await client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("manufacturers", [])
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro no fallback de montadoras: {str(e)}")
        return []

    async def _fetch_product_detail(self, client: httpx.AsyncClient, product_code: str) -> Dict:
        """Busca detalhes enriquecidos do produto: imagem, dimensões, classificações."""
        info = {"imagem": "", "imagens": [], "dimensoes": {}, "classificacoes": {}}
        try:
            params = {**self.common_params, "fields": "FULL"}
            url = f"{self.api_base}/products/{product_code}"
            response = await client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                
                # --- IMAGEM ---
                base_url = "https://vehiclelifetimesolutions.schaeffler.com.br"
                images = data.get("images", [])
                for img in images:
                    fmt = img.get("format", "")
                    img_url = img.get("url", "")
                    if img_url and not img_url.startswith("http"):
                        img_url = f"{base_url}{img_url}"
                    if fmt == "product" and not info["imagem"]:
                        info["imagem"] = img_url
                    elif fmt == "zoom":
                        if img_url not in info["imagens"]:
                            info["imagens"].append(img_url)
                    elif fmt == "thumbnail" and not info["imagem"]:
                        info["imagem"] = img_url
                
                # --- DIMENSÕES ---
                dims = data.get("dimensions", {})
                weight = data.get("weight", {})
                if dims:
                    info["dimensoes"] = {
                        "COMPRIMENTO (MM)": dims.get("length"),
                        "LARGURA (MM)": dims.get("width"),
                        "ALTURA (MM)": dims.get("height"),
                    }
                if weight and weight.get("value"):
                    info["dimensoes"]["PESO (KG)"] = weight.get("value")
                
                # --- CLASSIFICAÇÕES (Diâmetro, Info complementar, etc.) ---
                for cls_group in data.get("classifications", []):
                    for feat in cls_group.get("features", []):
                        name = feat.get("name", "").strip()
                        values = [v.get("value", "") for v in feat.get("featureValues", [])]
                        unit = feat.get("featureUnit", {}).get("symbol", "")
                        if name and values and "SVHC" not in name:
                            val_str = ", ".join(values)
                            if unit:
                                val_str = f"{val_str} {unit}"
                            info["classificacoes"][name.upper()] = val_str
                
                logger.info("SCHAEFFLER", f"Detalhes do produto: imagem={'sim' if info['imagem'] else 'nao'}, classificacoes={len(info['classificacoes'])}")
            else:
                logger.warning("SCHAEFFLER", f"Product detail status {response.status_code}")
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro ao buscar detalhes do produto: {str(e)}")
        return info

    async def _fetch_kit_contents(self, client: httpx.AsyncClient, product_code: str) -> List[str]:
        """Busca composição do kit (CONSISTS_OF) via endpoint /references."""
        components = []
        try:
            params = {
                **self.common_params,
                "referenceType": "CONSISTS_OF",
                "inverse": "false",
                "fields": "DEFAULT"
            }
            url = f"{self.api_base}/products/{product_code}/references"
            response = await client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                for ref in data.get("references", []):
                    target = ref.get("target", {})
                    name = target.get("fullName", "")
                    code = target.get("catalogArticleNumber", "")
                    qty = ref.get("quantity", 1)
                    if name and code:
                        entry = f"{name} ({code})"
                        if qty > 1:
                            entry = f"{qty}x {entry}"
                        components.append(entry)
                logger.info("SCHAEFFLER", f"Kit contém {len(components)} componentes")
            else:
                logger.warning("SCHAEFFLER", f"Kit contents status {response.status_code}")
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro ao buscar composição do kit: {str(e)}")
        return components

    async def _fetch_oe_numbers(self, client: httpx.AsyncClient, product_code: str) -> List[str]:
        """Busca números OE (originais/intercambiáveis) via endpoint dedicado /oenumbers."""
        refs = []
        try:
            url = f"{self.api_base}/products/{product_code}/oenumbers"
            response = await client.get(url, params=self.common_params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                for group in data.get("oenumbers", []):
                    mfr_name = group.get("manufacturer", {}).get("name", "ORIGINAL").upper()
                    for num in group.get("numbers", []):
                        code = num.get("number", "").strip()
                        exchange = num.get("exchangeability", "")
                        if code:
                            # Marca como intercambiável ou referência de peça
                            if "intercambiáveis" in exchange.lower():
                                refs.append(f"{mfr_name}: {code}")
                            else:
                                refs.append(f"{mfr_name} (REF): {code}")
                logger.info("SCHAEFFLER", f"OE Numbers encontrados: {len(refs)}")
            else:
                logger.warning("SCHAEFFLER", f"OE Numbers status {response.status_code} para {product_code}")
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro ao buscar OE numbers: {str(e)}")
        return refs

    async def _discover_products(self, client: httpx.AsyncClient, code: str) -> List[Dict]:
        """Busca o produto e retorna a lista de matches."""
        try:
            params = {
                **self.common_params,
                "fields": "products(foundBy,images(DEFAULT),productReferences(DEFAULT),classifications(DEFAULT),linkages(FULL),name,code,manufacturer,brand(DEFAULT),catalogArticleNumber,tradeNumbers,type,catalogArticleNumbers),facets,pagination(DEFAULT)",
                "query": f"{code}:relevance",
                "pageSize": 20,
                "source": "globalsearch"
            }
            url = f"{self.api_base}/products/search"
            response = await client.get(url, params=params, headers=self.headers)
            logger.info("SCHAEFFLER", f"Discovery status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                logger.info("SCHAEFFLER", f"Produtos encontrados: {len(products)}")
                for p in products:
                    mfrs = p.get("linkages", {}).get("manufacturers", [])
                    logger.info("SCHAEFFLER", f"Produto {p.get('code')} tem {len(mfrs)} montadoras.")
                return products
            elif response.status_code == 403:
                logger.error("SCHAEFFLER", "Erro 403: Bloqueio por falta de cookies/sessão.")
                # Futuro: Implementar captura automática aqui se necessário
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro no discovery: {str(e)}")
        return []

    async def _fetch_model_series(self, client: httpx.AsyncClient, product_code: str, mfr_code: str) -> List[Dict]:
        """Busca as séries de modelos para uma montadora específica."""
        try:
            params = {
                **self.common_params,
                "targetTypeCodes": "passengerCar",
                "globalCarPark": "false"
            }
            url = f"{self.api_base}/products/{product_code}/linkages/manufacturers/{mfr_code}/modelSeries"
            response = await client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("modelSeries", [])
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro ao buscar series ({mfr_code}): {str(e)}")
        return []

    async def _fetch_targets(self, client: httpx.AsyncClient, product_code: str, series_code: str, mfr_name: str, series_name: str, referencias: List[str], brand_name: str, article_code: str, product_info: Dict = None) -> List[Dict]:
        """Busca os veículos detalhados (targets) para uma série de modelos."""
        results = []
        try:
            params = {
                **self.common_params,
                "targetTypeCodes": "passengerCar",
                "globalCarPark": "false"
            }
            url = f"{self.api_base}/products/{product_code}/linkages/modelSeries/{series_code}/targets"
            response = await client.get(url, params=params, headers=self.headers)
            
            if response.status_code == 200:
                targets = response.json().get("targets", [])
                for target in targets:
                    results.append(self._build_target_result(target, mfr_name, series_name, referencias, brand_name, article_code, product_info))
        except Exception as e:
            logger.warning("SCHAEFFLER", f"Erro ao buscar targets ({series_code}): {str(e)}")
        return results

    def _build_target_result(self, target: Dict, mfr_name: str, series_name: str, referencias: List[str], brand_name: str, article_code: str, product_info: Dict = None) -> Dict:
        """Formata um veículo (target) para o padrão do BaseProvider."""
        product_info = product_info or {}
        
        # Extração de Anos (formato MM.YYYY)
        ano_ini = self._parse_schaeffler_year(target.get("constructionYearFrom", ""))
        ano_fim = self._parse_schaeffler_year(target.get("constructionYearTo", ""))
        
        # Limpeza do nome da série (Remove códigos internos entre parênteses)
        # Ex: "FOX HATCH (5Z1, 5Z3)" -> "FOX HATCH"
        series_clean = re.sub(r'\s*\([^)]*(?:\)|$)', '', series_name).strip()
        
        # Ficha Técnica Premium — Motor do veículo
        ficha = {
            "CILINDRADA (CCM)": target.get("displacementCCM"),
            "CILINDROS": target.get("cylinders"),
            "VÁLVULAS": target.get("valves"),
            "POTÊNCIA (HP)": target.get("enginePowerHP"),
            "POTÊNCIA (KW)": target.get("enginePowerKW"),
            "TRAÇÃO": target.get("driveType"),
            "TIPO MOTOR": target.get("engineType"),
            "CÓDIGOS MOTOR": " / ".join(target.get("engineCodes", [])),
            "SISTEMA COMBUSTÍVEL": target.get("fuelMixtureFormation")
        }
        
        # Enriquecimento com dados do produto (classificações, dimensões, composição)
        ficha.update(product_info.get("classificacoes", {}))
        ficha.update(product_info.get("dimensoes", {}))
        
        # Composição do kit
        composicao = product_info.get("composicao", [])
        if composicao:
            ficha["CONTÉM"] = " + ".join(composicao)

        config_motor_raw = f"{target.get('engineType', '')} {target.get('fuelType', '')}".strip().upper()
        config_motor_clean = re.sub(r'\s*\([^)]*(?:\)|$)', '', config_motor_raw).strip()

        versao_clean = re.sub(r'\s*\([^)]*(?:\)|$)', '', target.get("bodyType", "")).strip().upper()
        motor_clean = re.sub(r'\s*\([^)]*(?:\)|$)', '', target.get("name", "")).strip().upper()

        raw = {
            "marca_peca": brand_name,
            "codigo": article_code,
            "montadora": mfr_name.upper(),
            "modelo": series_clean.upper(),
            "versao": versao_clean,
            "motor": motor_clean,
            "configuracao_motor": config_motor_clean,
            "combustivel": target.get("fuelType", "").upper(),
            "ano_inicio": ano_ini,
            "ano_fim": ano_fim,
            "ficha_tecnica": ficha,
            "referencias": referencias,
            "imagem": product_info.get("imagem", ""),
            "imagens": product_info.get("imagens", [])
        }
        
        return self.formatar_resultado(raw)

    def _parse_schaeffler_year(self, date_str: str) -> str:
        """Converte MM.YYYY -> YYYY ou retorna vazio se inválido."""
        if not date_str:
            return ""
        # Padrão MM.YYYY
        match = re.search(r"(\d{2})\.(\d{4})", date_str)
        if match:
            return match.group(2)
        return date_str

    def _format_product_only(self, product: Dict, referencias: List[str], product_info: Dict = None) -> Dict:
        """Formata apenas o produto caso não haja aplicações."""
        product_info = product_info or {}
        ficha = {}
        ficha.update(product_info.get("classificacoes", {}))
        ficha.update(product_info.get("dimensoes", {}))
        composicao = product_info.get("composicao", [])
        if composicao:
            ficha["CONTÉM"] = " + ".join(composicao)
        
        return self.formatar_resultado({
            "marca_peca": product.get("brand", {}).get("name", "SCHAEFFLER").upper(),
            "codigo": product.get("catalogArticleNumber", ""),
            "modelo": product.get("fullName", "").upper(),
            "veiculo": "PRODUTO SEM APLICAÇÃO",
            "referencias": referencias,
            "imagem": product_info.get("imagem", ""),
            "imagens": product_info.get("imagens", []),
            "ficha_tecnica": ficha
        })
