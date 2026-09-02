import asyncio
import json
import re
import traceback
import httpx
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


def _parse_json_latin1(resp: httpx.Response) -> dict:
    """
    Decodifica a resposta JSON forçando Windows-1252 (cp1252).
    A API da Vetor devolve textos em cp1252 mas sem declarar no Content-Type,
    causando caracteres quebrados se decodificado como UTF-8.
    cp1252 é preferido ao latin-1 pois cobre bytes 0x80-0x9F (ex: ˜, €, etc.)
    que latin-1 trata como caracteres de controle inválidos.
    """
    for enc in ("cp1252", "latin-1"):
        try:
            return json.loads(resp.content.decode(enc))
        except Exception:
            continue
    return resp.json()


def _limpar_motor(valor: str) -> str:
    """
    Limpa o campo vehicle_characteristic da Vetor.
    Casos tratados:
    - None / vazio -> ""
    - "Savana - 2.5/3.2" -> versao="Savana", motor="2.5/3.2"
      (retorna só a parte numérica para o campo motor; versao é tratada no modelo)
    - "3.2/3.5 - Motor 4M41 / 6G74" -> extrai a cilindrada "3.2/3.5"
    - Duplos traços "- -" -> limpa para " - "
    """
    if not valor:
        return ""

    # Remove duplos traços
    valor = re.sub(r"-\s*-+", "-", valor).strip()

    # Se contém texto não-numérico antes de um traço (ex: "Savana - 2.5/3.2"),
    # mantém apenas a parte após o traço (a cilindrada)
    partes = re.split(r"\s+-\s+", valor, maxsplit=1)
    if len(partes) == 2:
        primeira, segunda = partes[0].strip(), partes[1].strip()
        # Se a primeira parte é predominantemente texto (não começa com dígito/ponto/barra)
        if primeira and not re.match(r"^[\d\./]", primeira):
            valor = segunda

    # Remove sufixo "- Motor XYZW" quando já temos a cilindrada
    valor = re.sub(r"\s*-\s*Motor\s+\w+.*$", "", valor, flags=re.IGNORECASE).strip()

    return valor.strip(" -")


class VetorProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Origin": "https://vetorauto.com.br",
            "Referer": "https://vetorauto.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }

    async def buscar(self, part_id: str):
        resultados = []
        codigo_busca = part_id.strip().upper()

        try:
            async with httpx.AsyncClient(verify=False, headers=self.headers, timeout=15.0) as client:

                # 1. Quick Search (Discovery)
                items = await self._quick_search(client, codigo_busca)

                if not items:
                    logger.info("VETOR", f"Nenhum resultado na busca rapida para {codigo_busca}")
                    return []

                logger.info("VETOR", f"Encontrados {len(items)} itens na busca rapida para {codigo_busca}")

                # 2. Hydration (Aplicações para cada item)
                async def fetch_applications(item):
                    slug = item.get("slug")
                    codigo_item = str(item.get("_id", "")).upper()

                    if not slug:
                        return item, codigo_item, [], [], {}, []

                    url_item = f"https://vetorauto.com.br/api/website/items/{slug}.json?attributes=id,observation,description,pictures[id,small,large,default,main],logix_item_view[ncm,pct_ipi,sku_unit[cod_barras,embalagem_venda,peso_bruto,measure_one,altura,largura,comprimento,volume_m3]]"

                    try:
                        # Passo A: Pega o ID numérico e imagens
                        resp_item = await client.get(url_item)
                        resp_item.raise_for_status()
                        item_data = _parse_json_latin1(resp_item).get("item", {})
                        numeric_id = item_data.get("id")

                        if not numeric_id:
                            return item, codigo_item, [], [], {}, []

                        # Ficha Técnica (Especificações)
                        ficha = {}
                        logix = item_data.get("logix_item_view", {})
                        if logix:
                            ncm = str(logix.get("ncm", "")).strip()
                            if ncm: ficha["NCM"] = ncm
                            ipi = str(logix.get("pct_ipi", "")).strip()
                            if ipi: ficha["IPI"] = ipi
                            
                            sku = logix.get("sku_unit", {})
                            if sku:
                                if sku.get("cod_barras"): ficha["EAN / GTIN"] = str(sku.get("cod_barras")).strip()
                                if sku.get("embalagem_venda"): ficha["QUANTIDADE EMBALAGEM"] = str(sku.get("embalagem_venda")).strip()
                                if sku.get("peso_bruto"): ficha["PESO (KG)"] = str(sku.get("peso_bruto")).strip()
                                
                                alt = str(sku.get("altura", "")).strip()
                                larg = str(sku.get("largura", "")).strip()
                                comp = str(sku.get("comprimento", "")).strip()
                                if alt and larg and comp:
                                    ficha["DIMENSÕES EMBALAGEM (AxLxC)"] = f"{alt} x {larg} x {comp} m"
                                    
                                vol = str(sku.get("volume_m3", "")).strip()
                                if vol: ficha["VOLUME (M³)"] = vol
                                
                                measure = str(sku.get("measure_one", "")).strip()
                                if measure: ficha["DIMENSÃO PRODUTO"] = f"{measure} mm"

                        # Passo B: Busca as aplicações e referências em paralelo
                        url_app = (
                            f"https://vetorauto.com.br/api/website/items/{numeric_id}/applications.json"
                            f"?attributes=id,feature,vehicle_characteristic,"
                            f"vehicle[id,name,brand[id,name],vehicle_type[id,name]],years"
                            f"&page=1&per_page=99999"
                            f"&sort_direction=asc,asc,asc,asc"
                            f"&sort_property=brand,vehicle,start_year,end_year"
                        )
                        url_sim = f"https://vetorauto.com.br/api/website/items/{numeric_id}/similar_codes.json?page=1&per_page=9999"
                        url_ori = f"https://vetorauto.com.br/api/website/items/{numeric_id}/original_codes.json?page=1&per_page=9999"

                        task_app = client.get(url_app)
                        task_sim = client.get(url_sim)
                        task_ori = client.get(url_ori)

                        resps = await asyncio.gather(task_app, task_sim, task_ori, return_exceptions=True)
                        
                        app_data, sim_data, ori_data = {}, {}, {}
                        
                        if not isinstance(resps[0], Exception):
                            resps[0].raise_for_status()
                            app_data = _parse_json_latin1(resps[0])
                            
                        if not isinstance(resps[1], Exception):
                            resps[1].raise_for_status()
                            sim_data = _parse_json_latin1(resps[1])
                            
                        if not isinstance(resps[2], Exception):
                            resps[2].raise_for_status()
                            ori_data = _parse_json_latin1(resps[2])

                        # Pegando TODAS as imagens em melhor qualidade (default)
                        pictures = item_data.get("pictures", [])
                        imagens_urls = []
                        for p in pictures:
                            img_path = p.get("default") or p.get("large") or p.get("small")
                            if img_path:
                                imagens_urls.append(f"https://vetorauto.com.br/{img_path}")

                        # observation da peça com encoding correto (já está em item_data Latin-1/cp1252)
                        item["_observation_decoded"] = item_data.get("observation") or ""
                        
                        # Extração de referências
                        referencias = []
                        for s in sim_data.get("similar_codes", []):
                            marca = s.get("similar_brand", {}).get("name", "")
                            code = s.get("code", "")
                            if marca and code:
                                referencias.append(f"{marca}: {code}")
                                
                        for o in ori_data.get("original_codes", []):
                            marca = o.get("brand", {}).get("name", "OEM")
                            code = o.get("code", "")
                            if code:
                                for p in str(code).split("/"):
                                    p = p.strip()
                                    if p:
                                        referencias.append(f"{marca}: {p}")

                        return item, codigo_item, app_data.get("applications", []), imagens_urls, ficha, referencias

                    except Exception as e:
                        logger.warning("VETOR", f"Erro ao buscar detalhes para {codigo_item}: {e}")
                        return item, codigo_item, [], [], {}, []

                # Dispara as requisições em paralelo
                tasks = [fetch_applications(it) for it in items]
                hydrated_results = await asyncio.gather(*tasks)

                for item, codigo_item, applications, imagens_urls, ficha, referencias in hydrated_results:
                    # Imagem principal: primeira da lista ou fallback do quick_search
                    imagem_principal = imagens_urls[0] if imagens_urls else ""
                    if not imagem_principal:
                        imagem_base = item.get("main_picture")
                        imagem_principal = f"https://vetorauto.com.br/{imagem_base}" if imagem_base else ""

                    # Observação com encoding correto
                    obs_item = item.get("_observation_decoded") or item.get("observation", "") or ""

                    if not applications:
                        # Sem aplicações cadastradas — emite linha de fallback com descrição
                        resultados.append({
                            "marca": "VETOR",
                            "codigo": codigo_item,
                            "montadora": "",
                            "modelo": item.get("description", ""),
                            "motor": "",
                            "observacao": obs_item,
                            "ano_inicio": "",
                            "ano_fim": "",
                            "imagem": imagem_principal,
                            "imagens": imagens_urls,
                            "ficha_tecnica": ficha,
                            "referencias": referencias
                        })
                        continue

                    for app in applications:
                        vehicle = app.get("vehicle", {})
                        brand = vehicle.get("brand", {})

                        montadora = brand.get("name", "")
                        modelo = vehicle.get("name", "")

                        # Motor — limpa None, duplos traços e "Modelo - Motor" misturado
                        motor_raw = app.get("vehicle_characteristic") or ""
                        motor = _limpar_motor(motor_raw)

                        # Anos
                        anos = app.get("years", [])
                        anos = [y for y in anos if isinstance(y, (int, float)) and y > 1900]
                        ano_inicio = min(anos) if anos else ""
                        ano_fim = max(anos) if anos else ""

                        # Observação combinada (feature da aplicação + observação geral da peça)
                        feature = (app.get("feature") or "").strip()
                        obs_parts = []
                        if feature:
                            obs_parts.append(feature)
                        if obs_item:
                            obs_parts.append(obs_item)
                        obs_final = " / ".join(obs_parts)

                        resultados.append({
                            "marca": "VETOR",
                            "codigo": codigo_item,
                            "montadora": montadora,
                            "modelo": modelo,
                            "motor": motor,
                            "observacao": obs_final,
                            "ano_inicio": ano_inicio,
                            "ano_fim": ano_fim,
                            "imagem": imagem_principal,
                            "imagens": imagens_urls,
                            "ficha_tecnica": ficha,
                            "referencias": referencias
                        })

        except Exception as e:
            logger.error("VETOR", f"Erro critico na busca: {e}\n{traceback.format_exc()}")

        # 3. Formatar resultados usando o BaseProvider
        formatted_results = []
        for r in resultados:
            try:
                fr = self.formatar_resultado(r)
                if fr:
                    formatted_results.append(fr)
            except Exception as e:
                logger.warning("VETOR", f"Erro ao formatar linha: {e}")

        return formatted_results

    async def _quick_search(self, client: httpx.AsyncClient, codigo: str) -> list:
        """
        Busca rápida no catálogo da Vetor.
        Tenta primeiro com o código original (maiúsculas).
        Se retornar vazio, tenta com o código em minúsculas (alguns códigos
        como VCA0024, VCD005 só são encontrados em lowercase no índice).
        """
        tentativas = [codigo, codigo.lower()]

        for tentativa in tentativas:
            url = (
                f"https://catalogsearch.vetorauto.com.br/api/website/quick_search.json"
                f"?count=true&page=1&per_page=30&q={tentativa}"
            )
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = _parse_json_latin1(resp)
                items = data.get("quick_search", [])
                if items:
                    return items
            except Exception as e:
                logger.warning("VETOR", f"Erro na quick_search ({tentativa}): {e}")

        return []
