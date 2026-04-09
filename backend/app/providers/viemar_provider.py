import httpx
import json
import re
from typing import List, Dict, Any
from app.providers.base_provider import BaseProvider


class ViemarProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = (
            config.get("url")
            or "https://catalogo.viemar.com.br/catalog/search/catalog/code"
        )
        self.image_base_url = (
            "https://catalogo.viemar.com.br/catalog/size/normal/image/"
        )
        self.headers = config.get(
            "headers",
            {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json;charset=UTF-8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            },
        )

    async def buscar(self, id_peca: str) -> List[Dict[str, Any]]:
        codigos_busca = self.normalizar_codigo(id_peca)
        resultados = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for cod in codigos_busca:
                try:
                    # A API da Viemar exige searchCode e cardMode (booleano)
                    payload = {"searchCode": cod, "cardMode": False}  # False = dados completos (crossRef, moreInfo, etc.)
                    print(f"[Viemar] Buscando código: {cod} com payload {payload}")

                    response = await client.post(
                        self.url, headers=self.headers, json=payload
                    )

                    if response.status_code != 200:
                        print(f"[Viemar] Erro HTTP {response.status_code} para {cod}")
                        continue

                    data = response.json()
                    if not data or "catalog" not in data:
                        continue

                    # Parser específico baseado no código legado
                    for catalog in data.get("catalog", []):
                        if not catalog:
                            continue

                        # Função auxiliar para pegar valor com segurança
                        def get_val(obj, key, default=""):
                            field = obj.get(key)
                            if field and isinstance(field, dict):
                                return field.get("value", default) or default
                            return default

                        brand = get_val(catalog, "brand")
                        model = get_val(catalog, "model")
                        year_global = get_val(catalog, "year")
                        product_line = get_val(catalog, "productLine")

                        # Posição global do catálogo (lista consolidada, ex: "Direita | Esquerda")
                        positions_list = []
                        pos_catalog_obj = catalog.get("position", {})
                        if isinstance(pos_catalog_obj, dict):
                            for pv in pos_catalog_obj.get("valueList", []):
                                val = pv.get("value", "").strip()
                                if val:
                                    positions_list.append(val)
                        catalog_positions = " | ".join(positions_list)

                        # Informações adicionais (moreInformation) → coluna Observações
                        more_info_str = ""
                        more_info_obj = catalog.get("moreInformation", {})
                        if isinstance(more_info_obj, dict):
                            for mi in more_info_obj.get("value", []):
                                if isinstance(mi, dict) and mi.get("value"):
                                    more_info_str = mi["value"]
                                    break

                        # Ficha Técnica básica do catálogo
                        ficha_tecnica = {}
                        if product_line:
                            ficha_tecnica["Linha de Produto"] = product_line
                        manuf_country = get_val(catalog, "manufacturerCountry")
                        if manuf_country:
                            ficha_tecnica["País de Fabricação"] = manuf_country

                        # Referências cruzadas
                        cross_ref_obj = catalog.get("crossReference")
                        cross_ref_list = []
                        if cross_ref_obj and isinstance(cross_ref_obj, dict):
                            cross_ref_list = cross_ref_obj.get("valueList", [])

                        cross_ref_str = " | ".join(
                            [
                                str(x.get("value", ""))
                                for x in cross_ref_list
                                if x.get("value")
                            ]
                        )

                        # Imagem (Viemar pode retornar lista ou dicionário)
                        image_data = catalog.get("image")
                        primary_image = ""
                        all_images = []

                        if isinstance(image_data, list) and image_data:
                            val = image_data[0].get("value") or ""
                            primary_image = f"{self.image_base_url}{val}" if val else ""
                            all_images = [
                                f"{self.image_base_url}{img.get('value')}"
                                for img in image_data
                                if img.get("value")
                            ]
                        elif isinstance(image_data, dict):
                            val = image_data.get("value") or ""
                            primary_image = f"{self.image_base_url}{val}" if val else ""
                            if primary_image:
                                all_images = [primary_image]

                        # Aplicações (aninhadas dentro de cada item do catálogo)
                        applications = catalog.get("application", [])

                        if not applications:
                            # Se não tiver aplicações específicas, cria uma entrada genérica
                            res = {
                                "marca": self.config.get("nome", "VIEMAR"),  # Nome do provedor como Marca Peça
                                "montadora": brand,  # BaseProvider procura 'montadora' para coluna Montadora
                                "veiculo": model,
                                "modelo": model,
                                "motor": "",
                                "configuracao_motor": "",
                                "ano_inicio": str(
                                    self._parse_ano(year_global, True) or ""
                                ),
                                "ano_fim": str(
                                    self._parse_ano(year_global, False) or ""
                                ),
                                "posicao": catalog_positions,
                                "observacao": more_info_str,
                                "imagem": primary_image,
                                "imagens": all_images,
                                "referencias": cross_ref_str,
                                "ficha_tecnica": ficha_tecnica,
                            }
                            resultados.append(self.formatar_resultado(res))
                        else:
                            # Agrupa aplicações por faixa de ano para concatenar posições (ex: "DIREITA | ESQUERDA")
                            # em vez de gerar uma linha duplicada por posição
                            from collections import defaultdict
                            year_groups: dict = defaultdict(list)
                            for app in applications:
                                if not app:
                                    continue
                                s = app.get("ano_inicial") or year_global
                                e = app.get("ano_final") or year_global
                                year_groups[(s, e)].append(app)

                            for (start_year, end_year), apps_group in year_groups.items():
                                # Coleta posições e direções únicas do grupo
                                positions = []
                                direcao_values = []

                                for app in apps_group:
                                    # Posição (default_value em pt)
                                    pos = ""
                                    pos_obj = app.get("posicao")
                                    if pos_obj and isinstance(pos_obj, dict):
                                        pos = pos_obj.get("default_value", "")
                                    if not pos:
                                        pos_obj = app.get("position")
                                        if pos_obj and isinstance(pos_obj, dict):
                                            pos = pos_obj.get("value", "")
                                    if pos and pos not in positions:
                                        positions.append(pos)

                                    # Direção: dos qualificadores (label="Direção" em pt)
                                    for q in (app.get("qualificador") or []):
                                        for i18n in q.get("i18nValues", []):
                                            if i18n.get("cod_i18n") == "pt" and i18n.get("label") == "Direção":
                                                val = i18n.get("value", "").strip()
                                                if val and val not in direcao_values:
                                                    direcao_values.append(val)

                                posicao_str = " | ".join(positions) or catalog_positions
                                direcao = " / ".join(direcao_values)

                                res = {
                                    "marca": self.config.get("nome", "VIEMAR"),  # Nome do provedor como Marca Peça
                                    "montadora": brand,  # BaseProvider procura 'montadora' para coluna Montadora
                                    "veiculo": model,
                                    "modelo": model,
                                    "motor": "",
                                    "configuracao_motor": "",
                                    "ano_inicio": str(
                                        self._parse_ano(start_year, True) or ""
                                    ),
                                    "ano_fim": str(
                                        self._parse_ano(end_year, False) or ""
                                    ),
                                    "posicao": posicao_str,
                                    "direcao": direcao,
                                    "observacao": more_info_str,
                                    "imagem": primary_image,
                                    "imagens": all_images,
                                    "referencias": cross_ref_str,
                                    "ficha_tecnica": ficha_tecnica,
                                }
                                resultados.append(self.formatar_resultado(res))

                    # Se encontrou algo para este código, para de tentar variações
                    if resultados:
                        # Adiciona raw_response para o primeiro item (Ajuda no Playground)
                        if resultados and data:
                            resultados[0]["raw_response"] = json.dumps(
                                data, indent=2, ensure_ascii=False
                            )
                        return resultados

                except Exception as e:
                    print(f"[Viemar] Erro na requisição para {cod}: {repr(e)}")
                    continue

        return []

    def _parse_ano(self, ano_str: Any, is_inicio: bool) -> Any:
        if not ano_str:
            return None
        if isinstance(ano_str, int):
            return ano_str

        # Remove espaços e limpa a string
        val = str(ano_str).strip()

        # Tenta lidar com o formato "08 > 13" ou "08 >"
        if ">" in val:
            parts = val.split(">")
            if is_inicio:
                val = parts[0].strip()
            else:
                val = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ""
                if not val:
                    # Se for "08 >", o ano fim é indefinido ou o atual, mas deixamos vazio para o sistema lidar
                    return None

        # Tenta extrair anos de strings como "2010-2015" ou "10/15" ou "2010"
        anos = re.findall(r"\d{2,4}", val)
        if not anos:
            return None

        ano = anos[0] if is_inicio else anos[-1]

        if len(ano) == 2:
            return 2000 + int(ano) if int(ano) < 50 else 1900 + int(ano)

        try:
            return int(ano)
        except:
            return None
