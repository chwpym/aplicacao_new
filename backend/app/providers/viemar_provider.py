import httpx
import json
import re
from collections import defaultdict
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

    @staticmethod
    def _get_val(obj: Dict[str, Any], key: str, default: str = "") -> str:
        """Pega valor de um campo da Viemar priorizando a tradução em português (i18nValues)."""
        if not obj or not isinstance(obj, dict):
            return default
        field = obj.get(key)
        if not field or not isinstance(field, dict):
            return default

        # Prioriza i18nValues / i18n_value em português ("pt")
        for i18n_key in ("i18nValues", "i18n_value"):
            i18n_list = field.get(i18n_key)
            if isinstance(i18n_list, list):
                for item in i18n_list:
                    if isinstance(item, dict) and item.get("cod_i18n") == "pt":
                        val_pt = str(item.get("value") or "").strip()
                        if val_pt and val_pt != "-empty-value-":
                            return val_pt

        val = str(field.get("value") or default).strip()
        if val == "-empty-value-":
            return default
        return val

    @staticmethod
    def _formatar_geracao(val_raw: str) -> List[str]:
        """
        Converte strings de geração/série como 'IV', 'I, II', 'G2' em ['GIV'], ['GI', 'GII'], ['G2'].
        """
        if not val_raw:
            return []
        partes = [p.strip().upper() for p in str(val_raw).split(",") if p.strip()]
        geracoes = []
        romanos_ou_digitos = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X|\d{1,2})$")
        for p in partes:
            p_clean = re.sub(r"^(?:GERA[ÇC][ÃA]O|S[ÉE]RIE)\s*", "", p).strip()
            if not p_clean:
                continue
            if p_clean.startswith("G") and len(p_clean) <= 6:
                geracoes.append(p_clean)
            elif romanos_ou_digitos.match(p_clean):
                geracoes.append(f"G{p_clean}")
            else:
                geracoes.append(p_clean)
        return geracoes

    @staticmethod
    def _extrair_lados(posicao_str: str) -> str:
        """Extrai DIREITO / ESQUERDO da posição quando aplicável."""
        if not posicao_str:
            return ""
        pos_upper = posicao_str.upper()
        lados = []
        if "DIREIT" in pos_upper or "RIGHT" in pos_upper:
            lados.append("DIREITO")
        if "ESQUERD" in pos_upper or "LEFT" in pos_upper:
            lados.append("ESQUERDO")
        return " / ".join(lados)

    def _classificar_detalhes(
        self,
        submodel_str: str,
        more_info_items: List[str],
        app_qualifiers: List[tuple],
    ) -> Dict[str, Any]:
        """
        Classifica todas as etiquetas de detalhes (subModel, moreInformation e qualificador)
        nas colunas corretas: versoes (MODELO), direcao, motor, restricoes e observacoes.
        """
        versoes_modelo: List[str] = []
        geracoes: List[str] = []
        direcoes: List[str] = []
        motores: List[str] = []
        restricoes: List[str] = []
        observacoes: List[str] = []

        if submodel_str and submodel_str.lower() != "-empty-value-":
            for sm in submodel_str.split(","):
                sm_clean = sm.strip()
                if sm_clean and sm_clean not in versoes_modelo:
                    versoes_modelo.append(sm_clean)

        # Unifica pares (label, val) vindos do qualificador (em PT) e do moreInformation
        pares: List[tuple] = []
        for lbl, val in app_qualifiers:
            pares.append((lbl.strip(), val.strip()))

        for item in more_info_items:
            for fragment in re.split(r"<br\s*/?>|\|", str(item), flags=re.IGNORECASE):
                frag = fragment.strip()
                if not frag:
                    continue
                if ":" in frag:
                    lbl, val = frag.split(":", 1)
                    pares.append((lbl.strip(), val.strip()))
                else:
                    pares.append(("", frag))

        for lbl, val in pares:
            if not val or val.lower() == "-empty-value-":
                continue

            lbl_norm = lbl.lower()
            val_upper = val.upper().strip()

            # 1. Restrições explícitas ("Exceto ...") ou Aplicações exclusivas
            if val_upper.startswith("EXCETO"):
                lbl_pt = "Motor" if lbl_norm == "engine" else ("Direção" if lbl_norm == "steering" else lbl)
                texto_rest = f"{lbl_pt}: {val}".strip(": ") if lbl_pt else val
                if texto_rest.upper() not in [r.upper() for r in restricoes]:
                    restricoes.append(texto_rest)
                continue

            # 2. Direção (ignora valores em inglês 'Hydraulic' quando já existe Hidráulica)
            if "dire" in lbl_norm or lbl_norm == "steering":
                mapa_dir = {
                    "HYDRAULIC": "Hidráulica",
                    "ELECTRIC": "Elétrica",
                    "MECHANICAL": "Mecânica",
                }
                val_dir = mapa_dir.get(val_upper, val.strip())
                if val_dir.upper() not in [d.upper() for d in direcoes]:
                    direcoes.append(val_dir)
                continue

            # 3. Motor / Engine
            if lbl_norm in ("motor", "engine"):
                if val.strip() not in motores:
                    motores.append(val.strip())
                continue

            # 4. Modelo -> Coluna MODELO (versao), separado por vírgula (ex: "Mille, Mille Economy")
            if lbl_norm == "modelo":
                for m_part in val.split(","):
                    m_clean = m_part.strip()
                    if m_clean and m_clean.upper() not in [v.upper() for v in versoes_modelo]:
                        versoes_modelo.append(m_clean)
                continue

            # 5. Geração / Série -> Coluna MODELO (versao) convertido para GI, GII, G2, GIV
            if "gera" in lbl_norm or "série" in lbl_norm or "serie" in lbl_norm:
                for g_fmt in self._formatar_geracao(val):
                    if g_fmt.upper() not in [g.upper() for g in geracoes]:
                        geracoes.append(g_fmt)
                continue

            # 6. Observação genérica ("Obs.") ou detalhes técnicos da peça (Produto: Kit, Bandeja: Estampada, etc.)
            if lbl_norm in ("obs", "obs.", "observação", "observacao", ""):
                texto_obs = val.strip()
            else:
                texto_obs = f"{lbl}: {val}"

            # Evita duplicar a mesma observação (ex: "Até chassi 07972" repetido em Obs e Chassi)
            if texto_obs.upper() not in [o.upper() for o in observacoes]:
                observacoes.append(texto_obs)

        # Combina versões de modelo (ex: Action, Mille) com gerações (ex: GI, GII, GIV)
        versoes_finais: List[str] = []
        if versoes_modelo and geracoes:
            for vm in versoes_modelo:
                for g in geracoes:
                    if g.upper() not in vm.upper():
                        versoes_finais.append(f"{vm} {g}".strip())
                    else:
                        versoes_finais.append(vm)
        elif versoes_modelo:
            versoes_finais = versoes_modelo
        elif geracoes:
            versoes_finais = geracoes
        else:
            versoes_finais = [""]

        return {
            "versoes": versoes_finais,
            "direcao": " / ".join(direcoes),
            "motor": " / ".join(motores),
            "restricao": " | ".join(restricoes),
            "observacao": " | ".join(observacoes),
        }

    async def buscar(self, id_peca: str) -> List[Dict[str, Any]]:
        codigos_busca = self.normalizar_codigo(id_peca)
        resultados = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx_cod, cod in enumerate(codigos_busca):
                if idx_cod > 0:
                    import asyncio
                    await asyncio.sleep(1.5)
                try:
                    payload = {"searchCode": cod, "cardMode": False}
                    print(f"[Viemar] Buscando código: {cod} com payload {payload}")

                    response = await client.post(
                        self.url, headers=self.headers, json=payload
                    )

                    if response.status_code == 403:
                        import asyncio
                        print(f"[Viemar] HTTP 403 em {cod}, aguardando 1.5s para re-tentar...")
                        await asyncio.sleep(1.5)
                        response = await client.post(
                            self.url, headers=self.headers, json=payload
                        )

                    if response.status_code != 200:
                        print(f"[Viemar] Erro HTTP {response.status_code} para {cod}")
                        continue

                    data = response.json()
                    if not data or "catalog" not in data:
                        continue

                    for catalog in data.get("catalog", []):
                        if not catalog:
                            continue

                        brand = self._get_val(catalog, "brand")
                        model = self._get_val(catalog, "model")
                        submodel = self._get_val(catalog, "subModel")
                        year_global = self._get_val(catalog, "year")
                        product_line = self._get_val(catalog, "productLine")
                        reference_code = self._get_val(catalog, "reference")
                        engine_global = self._get_val(catalog, "engine")
                        gen_global = self._get_val(catalog, "generation")

                        # Posição global do catálogo (traduzindo Left/Right se vier em inglês)
                        positions_list = []
                        pos_catalog_obj = catalog.get("position", {})
                        if isinstance(pos_catalog_obj, dict):
                            for pv in pos_catalog_obj.get("valueList", []):
                                val = str(pv.get("value", "")).strip()
                                if val.upper() == "LEFT":
                                    val = "Esquerda"
                                elif val.upper() == "RIGHT":
                                    val = "Direita"
                                if val and val not in positions_list:
                                    positions_list.append(val)
                        catalog_positions = " | ".join(positions_list)

                        # Informações adicionais (moreInformation)
                        more_info_items = []
                        more_info_obj = catalog.get("moreInformation", {})
                        if isinstance(more_info_obj, dict):
                            for mi in more_info_obj.get("value", []):
                                if isinstance(mi, dict) and mi.get("value"):
                                    more_info_items.append(str(mi["value"]))

                        # Ficha Técnica básica do catálogo (em Português)
                        ficha_tecnica = {}
                        if product_line:
                            ficha_tecnica["Linha de Produto"] = product_line
                        manuf_country = self._get_val(catalog, "manufacturerCountry")
                        if manuf_country:
                            ficha_tecnica["País de Fabricação"] = manuf_country

                        # Manual / Alertas Técnicos da Viemar
                        attachment_obj = catalog.get("attachment", {})
                        if isinstance(attachment_obj, dict):
                            for att in attachment_obj.get("subValue", []):
                                if isinstance(att, dict) and att.get("value"):
                                    att_title = ""
                                    for cat_i18n in att.get("categoryTitleI18n", []):
                                        if isinstance(cat_i18n, dict) and cat_i18n.get("cod_i18n") == "pt":
                                            att_title = str(cat_i18n.get("value") or "").replace("\ufffd", "çã")
                                            break
                                    if not att_title:
                                        att_title = att.get("categoryTitle") or att.get("title") or "Instrução"
                                    if str(att_title).isdigit():
                                        att_title = "Instrução"
                                    ficha_tecnica[att_title] = att.get("value")

                        # Referências cruzadas
                        cross_ref_obj = catalog.get("crossReference")
                        cross_ref_list = []
                        if cross_ref_obj and isinstance(cross_ref_obj, dict):
                            cross_ref_list = cross_ref_obj.get("valueList", [])

                        cross_ref_str = " | ".join(
                            [
                                str(x.get("value", "")).replace("\t", " ").strip()
                                for x in cross_ref_list
                                if x.get("value")
                            ]
                        )

                        # Rastreabilidade: se a busca foi por outro código, injeta o termo buscado
                        if cod.upper() != str(reference_code).upper():
                            label_busca = f"Buscado: {cod.upper()}"
                            if label_busca not in cross_ref_str:
                                cross_ref_str = (cross_ref_str + " | " + label_busca).strip(" | ")

                        # Imagem
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
                            app_quals = []
                            if gen_global:
                                app_quals.append(("Geração", gen_global))
                            if engine_global:
                                app_quals.append(("Motor", engine_global))

                            parsed = self._classificar_detalhes(
                                submodel, more_info_items, app_quals
                            )
                            lado_str = self._extrair_lados(catalog_positions)

                            for versao_item in parsed["versoes"]:
                                res = {
                                    "marca": self.config.get("nome", "VIEMAR"),
                                    "montadora": brand,
                                    "modelo": model,
                                    "versao": versao_item,
                                    "motor": parsed["motor"],
                                    "configuracao_motor": "",
                                    "ano_inicio": str(
                                        self._parse_ano(year_global, True) or ""
                                    ),
                                    "ano_fim": str(
                                        self._parse_ano(year_global, False) or ""
                                    ),
                                    "posicao": catalog_positions,
                                    "lado": lado_str,
                                    "direcao": parsed["direcao"],
                                    "restricao": parsed["restricao"],
                                    "descricao_produto": product_line,
                                    "observacao": parsed["observacao"],
                                    "imagem": primary_image,
                                    "imagens": all_images,
                                    "referencias": cross_ref_str,
                                    "ficha_tecnica": ficha_tecnica,
                                    "codigo": reference_code or cod,
                                }
                                resultados.append(self.formatar_resultado(res))
                        else:
                            year_groups: dict = defaultdict(list)
                            for app in applications:
                                if not app:
                                    continue
                                s = app.get("ano_inicial") or year_global
                                e = app.get("ano_final") or year_global
                                year_groups[(s, e)].append(app)

                            for (start_year, end_year), apps_group in year_groups.items():
                                positions = []
                                app_quals = []
                                if gen_global:
                                    app_quals.append(("Geração", gen_global))
                                if engine_global:
                                    app_quals.append(("Motor", engine_global))

                                for app in apps_group:
                                    pos = ""
                                    pos_obj = app.get("posicao")
                                    if pos_obj and isinstance(pos_obj, dict):
                                        # Prioriza i18n_value em pt
                                        for pv in pos_obj.get("i18n_value", []):
                                            if isinstance(pv, dict) and pv.get("cod_i18n") == "pt":
                                                pos = str(pv.get("value") or "").strip()
                                                break
                                        if not pos:
                                            pos = str(pos_obj.get("default_value") or "").strip()
                                    if not pos:
                                        pos_obj = app.get("position")
                                        if pos_obj and isinstance(pos_obj, dict):
                                            pos = str(pos_obj.get("value") or "").strip()
                                    if pos and pos not in positions:
                                        positions.append(pos)

                                    motor_app_direct = self._get_val(app, "engine")
                                    if motor_app_direct:
                                        app_quals.append(("Motor", motor_app_direct))

                                    for q in (app.get("qualificador") or []):
                                        for i18n in q.get("i18nValues", []):
                                            if i18n.get("cod_i18n") == "pt":
                                                label = str(i18n.get("label") or "").strip()
                                                val = str(i18n.get("value") or "").strip()
                                                if label and val:
                                                    app_quals.append((label, val))

                                posicao_str = " | ".join(positions) or catalog_positions
                                lado_str = self._extrair_lados(posicao_str)
                                parsed = self._classificar_detalhes(
                                    submodel, more_info_items, app_quals
                                )

                                for versao_item in parsed["versoes"]:
                                    res = {
                                        "marca": self.config.get("nome", "VIEMAR"),
                                        "montadora": brand,
                                        "modelo": model,
                                        "versao": versao_item,
                                        "motor": parsed["motor"],
                                        "configuracao_motor": "",
                                        "ano_inicio": str(
                                            self._parse_ano(start_year, True) or ""
                                        ),
                                        "ano_fim": str(
                                            self._parse_ano(end_year, False) or ""
                                        ),
                                        "posicao": posicao_str,
                                        "lado": lado_str,
                                        "direcao": parsed["direcao"],
                                        "restricao": parsed["restricao"],
                                        "descricao_produto": product_line,
                                        "observacao": parsed["observacao"],
                                        "imagem": primary_image,
                                        "imagens": all_images,
                                        "referencias": cross_ref_str,
                                        "ficha_tecnica": ficha_tecnica,
                                        "codigo": reference_code or cod,
                                    }
                                    resultados.append(self.formatar_resultado(res))

                    if resultados:
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

        val = str(ano_str).strip()

        if ">" in val:
            parts = val.split(">")
            if is_inicio:
                val = parts[0].strip()
            else:
                val = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ""
                if not val:
                    return None

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
