import asyncio
import json
import re
import traceback
from typing import Any, Dict, List
from urllib.parse import quote

import httpx

from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


class ReparadorVwProvider(BaseProvider):
    """
    Provedor Nativo para o Catálogo Oficial Volkswagen Reparadores + Loja Oficial Peças VW.

    Arquitetura Técnica Híbrida (2 Fontes Oficiais VW):
    ---------------------------------------------------
    1. **Fonte Primária — Catálogo Técnico Reparador VW (Ponte GraphQL Fraga V2):**
       Endpoint: `https://www.reparadorvw.com.br/api/catalogo/gql`
       Traz ~2.650 itens mecânicos/manutenção com riqueza máxima de versões, cilindradas,
       válvulas, códigos de bloco (`EA111 VHT`, `EA211`, `EA888`, `AP`), medidas e NCM.
       Opera sem login/senha (token OAuth2 injetado server-side pela ponte da VW), respeitando
       a whitelist oficial de queries do portal.

    2. **Fonte Secundária (Fallback Duplo) — Loja Oficial Peças VW (`pecas.vw.com.br` / Algolia):**
       Índice público de leitura (`prod_main_products_v2`) com **53.800+ peças genuínas VW**
       (incluindo toda a linha de lataria, para-choques, grades, molduras, emblemas, lanternas,
       faróis, acabamentos internos e vidros que não existem na base mecânica da Fraga):
       - **Fallback A (Fotos 900x900 e Giro 360°):** Quando a peça existe na Fraga mas vem sem
         foto (~95% da base Fraga VW), resgata automaticamente até 8 fotos HD do CDN da Loja.
       - **Fallback B (Catálogo Completo de 53k Peças):** Quando o código pesquisado não existe
         no GraphQL do Reparador VW (ou falha por indisponibilidade temporária da ponte, nunca
         travando a busca), consulta instantaneamente as 53.800+ peças do `pecas.vw.com.br`,
         extraindo aplicações (`resumo_aplicacao`), Lado/Posição de montagem (`caracteristicas`),
         ficha técnica e galeria de fotos `900x900`!
    """

    GQL_URL = "https://www.reparadorvw.com.br/api/catalogo/gql"

    # Fragmento oficial de campos de produto exigido pelas queries da ponte VW
    _PROD_FIELDS = (
        "product{ id partNumber brand{name imageUrl} "
        "productGroup{name family{name} system{name}} "
        "summaryApplication applicationDescription images{thumbnailUrl} }"
    )

    # Query 1A: Busca por código exato/parcial (Part Number)
    QUERY_BY_CODE = (
        "query C($q:String!,$by:[SearchCodeType!]!,$skip:Int!,$take:Int!,"
        "$brands:[UUID!],$systems:[UUID!],$families:[UUID!],$groups:[UUID!],"
        "$specs:[SpecificationFilterInput!]){ "
        "catalogSearchByCode(query:$q,searchCodeBy:$by,exactCode:false,"
        "brands:$brands,productGroupSystems:$systems,productGroupFamilies:$families,"
        "productGroups:$groups,specifications:$specs,onlyWithCodeDistributor:false,"
        "market:BRA,skip:$skip,take:$take){ pageInfo{total} nodes{ "
        + _PROD_FIELDS
        + " } } }"
    )

    # Query 1B: Autocomplete / Busca Geral (Fallback rápido caso catalogSearchByCode não ache)
    QUERY_AUTOCOMPLETE = (
        "query($q:String!){ "
        "catalogSearch(query:$q,onlyWithCodeDistributor:false,market:BRA,skip:0,take:6){ "
        "nodes{ product{ id partNumber brand{name} productGroup{name system{name}} images{thumbnailUrl} } } "
        "} }"
    )

    # Query 2: Hidratação completa da ficha da peça (aplicações, especificações, códigos antigos e imagens)
    QUERY_PRODUCT = (
        "query($id:String!){ "
        "product(id:$id, market:BRA){ "
        "id partNumber status containsUniversalApplication "
        "brand{name imageUrl} "
        "productGroup{name family{name} system{id name}} "
        "summaryApplication applicationDescription "
        "images{thumbnailUrl imageUrl caption category} "
        "specifications{description value category important} "
        "crossReferences{brand{name} partNumber} "
        "vehicles{ brand name model engineName engineConfiguration startYear endYear only note } "
        "archives{url category caption origin} "
        "links{title category url} "
        "videos oldCodes completeCodes "
        "distributors{distributor{name} code} "
        "} }"
    )

    # Configuração pública de leitura da Loja Oficial VW (pecas.vw.com.br / Algolia - 53.800+ peças)
    ALGOLIA_APP_ID = "JPW9SFM280"
    ALGOLIA_API_KEY = "0667f793cd8c73bc8862a5315a9d889e"
    ALGOLIA_INDEX = "prod_main_products_v2"
    LOJA_CDN_IMAGES = "https://dvo56mb5swza6.cloudfront.net/"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = config.get("url") or self.GQL_URL

        # Mescla headers customizados do banco com os headers obrigatórios da ponte CloudFront/VW
        custom_headers = config.get("headers") or {}
        if isinstance(custom_headers, str):
            try:
                custom_headers = json.loads(custom_headers)
            except Exception:
                custom_headers = {}

        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://www.reparadorvw.com.br",
            "Referer": "https://www.reparadorvw.com.br/catalogo",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            **custom_headers,
        }

    @staticmethod
    def _safe_str(val: Any) -> str:
        """
        Garante que valores `None`, `null`, `''` literal ou dicionários aninhados virem strings
        limpas, evitando o bug clássico onde `None` vira a string literal `'NONE'`.
        """
        if val is None:
            return ""
        if isinstance(val, dict):
            extracted = val.get("value") or val.get("label") or val.get("name") or ""
            return str(extracted).strip()
        texto = str(val).strip()
        if texto.upper() in ("NONE", "NULL", "AUTH_NOT_AUTHORIZED", "-", "''", '""'):
            return ""
        return texto

    @staticmethod
    def _norm_pn(pn: str) -> str:
        """Normaliza o Part Number removendo espaços, pontos e hifens para comparação exata."""
        return re.sub(r"[^A-Z0-9]", "", (pn or "").upper())

    @staticmethod
    def _limpar_motor_vw(engine_name: str, engine_config: str) -> tuple[str, str]:
        """
        Higieniza redundâncias clássicas da base Volkswagen/Fraga antes do BaseProvider:
        - `AP 1600` + `1.6 L 8V` -> remove `1600` redundante de `AP 1600`, deixando `AP` limpo!
        - `1600 AR` + `BOXER 4 AR` -> remove `1600` redundante e unifica `BOXER4` -> `BOXER`
        """
        en = (engine_name or "").upper().strip()
        ec = (engine_config or "").upper().strip()

        if re.search(r"\b\d[\.,]\d\b", ec):
            en = re.sub(r"\b(1000|1300|1400|1500|1600|1800|1900|2000)\b", "", en)
            en = re.sub(r"\s+", " ", en).strip(" -/")

        ec = re.sub(r"\bBOXER\s*4\b", "BOXER", ec)
        if re.search(r"\bAR\b", en) and re.search(r"\bAR\b", ec):
            ec = re.sub(r"\bAR\b", "", ec)
            ec = re.sub(r"\s+", " ", ec).strip()

        return en, ec

    @staticmethod
    def _limpar_versao_vw(versao: str) -> str:
        """
        Corrige pequenas falhas de digitação do catálogo original da VW antes da normalização:
        - Espaço não-quebrável (`\xa0`) -> espaço normal
        - `S- TRONIC` -> `S-TRONIC`
        - `TOTAL FLEX` -> `FLEX` (evita sobrar a palavra órfã `TOTAL` na versão após extrair `FLEX`)
        """
        if not versao:
            return ""
        v = versao.replace("\xa0", " ").upper().strip()
        v = re.sub(r"\bS-\s+TRONIC\b", "S-TRONIC", v)
        v = re.sub(r"\bTOTAL\s+FLEX\b", "FLEX", v)
        v = re.sub(r"\bTOTALFLEX\b", "FLEX", v)
        return re.sub(r"\s+", " ", v).strip()

    @staticmethod
    def _padronizar_montadora_vw(brand: str) -> str:
        """
        Atalho rápido para montadoras do Grupo VW: enviar `'VW'` direto evita centenas de consultas
        repetidas ao DuckDB quando o modelo for antigo (ex: Santana, Pointer, Logus, Kombi).
        """
        b = (brand or "").upper().strip()
        if b in ("VOLKSWAGEN", "VW", "VOLKSWAGEN ORIGINAL"):
            return "VW"
        return b

    @classmethod
    def _extrair_fotos_do_hit_loja(cls, hit: Dict[str, Any]) -> List[str]:
        """
        Extrai até 8 URLs em alta definição (900x900) de um registro do Algolia (`pecas.vw.com.br`),
        combinando até 4 ângulos cardeais do giro 360° + fotos avulsas.
        """
        fotos_obj = hit.get("fotos") or {}
        if not isinstance(fotos_obj, dict):
            return []

        giro = [f for f in (fotos_obj.get("fotos_360") or []) if f]
        avulsas = [f for f in (fotos_obj.get("fotos_avulsas") or []) if f]

        caminhos: List[str] = []
        if giro:
            n = len(giro)
            for idx in (0, round(n / 4), round(n / 2), round(3 * n / 4)):
                c = giro[min(idx, n - 1)]
                if c not in caminhos:
                    caminhos.append(c)
        for c in avulsas:
            if c not in caminhos:
                caminhos.append(c)

        return [
            f"{cls.LOJA_CDN_IMAGES}900x900/{quote(str(c).lstrip('/'), safe='/')}"
            for c in caminhos[:8]
        ]

    async def _consultar_algolia_loja(
        self, client: httpx.AsyncClient, codigo: str, hits_per_page: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Consulta resiliente ao índice público Algolia do `pecas.vw.com.br` (53.800+ peças).
        Isolada com try/except e timeout curto (6s) para nunca atrasar ou quebrar o provedor
        caso o Algolia sofra qualquer alteração no futuro.
        """
        chave = self._norm_pn(codigo)
        if not chave:
            return []

        algolia_url = (
            f"https://{self.ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{self.ALGOLIA_INDEX}/query"
            f"?x-algolia-application-id={self.ALGOLIA_APP_ID}"
            f"&x-algolia-api-key={self.ALGOLIA_API_KEY}"
        )
        campos = (
            "id_produto,codigo_original,codigosoriginais,descricao,descricao_secundaria,"
            "segmento,unidade_venda,garantia_produto,fotos,resumo_aplicacao,nome_aplicacoes,"
            "ano_de,ano_ate,veiculo,modelo,caracteristicas,secao,grupo,subgrupo"
        )
        params_str = (
            f"query={quote(chave)}"
            f"&optionalWords={quote(chave)}"
            f"&hitsPerPage={hits_per_page}"
            f"&attributesToHighlight=&attributesToRetrieve={campos}"
            f"&analytics=false&clickAnalytics=false&enablePersonalization=false"
        )

        try:
            resp = await client.post(
                algolia_url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                content=json.dumps({"params": params_str}),
                timeout=6.0,
            )
            if resp.status_code == 200:
                return resp.json().get("hits") or []
        except Exception as e:
            logger.warning("REPARADOR_VW", f"Aviso ao consultar Algolia Loja Oficial ({codigo}): {e}")

        return []

    async def _fetch_loja_oficial_photos(
        self, client: httpx.AsyncClient, part_number: str
    ) -> List[str]:
        """
        Fallback A: Resgata fotos `900x900` na Loja Oficial (`pecas.vw.com.br`) para uma peça
        já encontrada na Fraga que veio sem imagem. Exige match exato do Part Number.
        """
        chave_alvo = self._norm_pn(part_number)
        if not chave_alvo:
            return []

        hits = await self._consultar_algolia_loja(client, chave_alvo, hits_per_page=5)
        for hit in hits:
            cod_orig = self._norm_pn(hit.get("codigo_original") or "")
            cods_lista = [self._norm_pn(x) for x in (hit.get("codigosoriginais") or [])]
            if cod_orig == chave_alvo or chave_alvo in cods_lista:
                fotos = self._extrair_fotos_do_hit_loja(hit)
                if fotos:
                    return fotos
        return []

    async def _buscar_fallback_loja_oficial(
        self, client: httpx.AsyncClient, codigo_busca: str, take_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fallback B (Acervo de 53.800+ Peças do `pecas.vw.com.br`):
        Acionado automaticamente quando o código pesquisado não existe no catálogo mecânico
        Reparador VW (ex: molduras, grades, para-choques, lanternas, acabamentos com sufixo
        de cor como `5U0853665S9B9` ou busca pelo código base `5U0853665`).
        """
        chave_alvo = self._norm_pn(codigo_busca)
        if len(chave_alvo) < 5:
            return []

        hits = await self._consultar_algolia_loja(client, chave_alvo, hits_per_page=take_limit)
        if not hits:
            return []

        # Filtra apenas peças cujo código original seja igual ou comece pelo código pesquisado
        # (Ex: pesquisar "5U0853665" traz "5U0853665S9B9" e "5U0853665P9B9", mas ignora falsos positivos)
        hits_exatos = []
        hits_prefixo = []
        for h in hits:
            cod_orig = self._norm_pn(h.get("codigo_original") or "")
            cods_lista = [self._norm_pn(x) for x in (h.get("codigosoriginais") or []) if x]
            todos_cods = [c for c in ([cod_orig] + cods_lista) if c]

            if any(c == chave_alvo for c in todos_cods):
                hits_exatos.append(h)
            elif len(chave_alvo) >= 7 and any(c.startswith(chave_alvo) for c in todos_cods):
                hits_prefixo.append(h)

        selecionados = hits_exatos if hits_exatos else hits_prefixo
        if not selecionados:
            return []

        logger.info(
            "REPARADOR_VW",
            f"Fallback Loja Oficial (pecas.vw.com.br): {len(selecionados)} peça(s) encontrada(s) para '{codigo_busca}'.",
        )

        resultados_loja: List[Dict[str, Any]] = []

        for hit in selecionados[:take_limit]:
            part_number = self._safe_str(hit.get("codigo_original")) or codigo_busca
            descricao = self._safe_str(hit.get("descricao"))
            desc_sec = self._safe_str(hit.get("descricao_secundaria"))

            imagens = self._extrair_fotos_do_hit_loja(hit)
            imagem_principal = imagens[0] if imagens else ""

            # Monta Ficha Técnica e extrai Lado / Posição de `caracteristicas`
            ficha: Dict[str, str] = {}
            if descricao:
                ficha["DESCRIÇÃO COMERCIAL"] = f"{descricao} VW {part_number}".upper()

            secoes = [self._safe_str(s) for s in (hit.get("secao") or []) if self._safe_str(s)]
            grupos = [self._safe_str(g) for g in (hit.get("grupo") or []) if self._safe_str(g)]
            if grupos:
                ficha["CATEGORIA"] = grupos[0].upper()
            elif descricao:
                ficha["CATEGORIA"] = descricao.upper()
            if secoes:
                ficha["LINHA / SISTEMA"] = secoes[0].upper()

            if hit.get("unidade_venda"):
                ficha["UNIDADE DE VENDA"] = self._safe_str(hit.get("unidade_venda")).upper()
            if hit.get("garantia_produto"):
                ficha["GARANTIA"] = self._safe_str(hit.get("garantia_produto")).upper()
            if hit.get("segmento"):
                ficha["SEGMENTO"] = self._safe_str(hit.get("segmento")).upper()

            lado_val = ""
            posicao_val = ""
            obs_carac: List[str] = []

            for carac in hit.get("caracteristicas") or []:
                if isinstance(carac, dict):
                    for k, v in carac.items():
                        k_clean = self._safe_str(k).upper()
                        v_clean = self._safe_str(v).upper()
                        if not k_clean or not v_clean:
                            continue
                        ficha[k_clean] = v_clean
                        if "LADO" in k_clean:
                            lado_val = v_clean
                        elif "POSIÇÃO" in k_clean or "POSICAO" in k_clean:
                            posicao_val = v_clean
                        else:
                            obs_carac.append(f"{k_clean}: {v_clean}")

            # Referências OEM (inclui código sem hífen e variações formatadas com hífen se diferentes)
            refs_list = [f"VOLKSWAGEN: {part_number}"]
            for cod_alt in hit.get("codigosoriginais") or []:
                c_alt = self._safe_str(cod_alt).upper()
                if c_alt and self._norm_pn(c_alt) != self._norm_pn(part_number):
                    refs_list.append(f"VOLKSWAGEN: {c_alt}")
            referencias_str = " | ".join(refs_list)

            obs_geral = " | ".join(obs_carac)
            if desc_sec and desc_sec.upper() != descricao.upper():
                obs_geral = f"{desc_sec.upper()} | {obs_geral}".strip(" | ")

            # Extrai lista de veículos de `resumo_aplicacao` (ex: [{"a1": 2017, "a2": 2022, "moto": "Gol", "mod": "''"}])
            resumo_apps = hit.get("resumo_aplicacao") or []
            aplicacoes_extraidas: List[Dict[str, Any]] = []

            for app in resumo_apps:
                if not isinstance(app, dict):
                    continue
                carro_raw = self._safe_str(app.get("moto")).replace("\xa0", " ")
                versao_raw = self._limpar_versao_vw(self._safe_str(app.get("mod")))
                if not carro_raw:
                    continue

                # Separa casos compostos da Loja Oficial (ex: "Polo Track" -> modelo="POLO", versao="TRACK";
                # "Tiguan Allspace" -> modelo="TIGUAN", versao="ALLSPACE"; "Tiguan R Line" -> "TIGUAN", "R-LINE")
                modelo_carro = carro_raw.upper()
                for prefixo_base in ("POLO ", "TIGUAN ", "GOL ", "SAVEIRO ", "VOYAGE ", "FOX ", "GOLF ", "JETTA ", "AMAROK ", "DELIVERY ", "CONSTELLATION "):
                    if modelo_carro.startswith(prefixo_base):
                        resto = modelo_carro[len(prefixo_base):].strip()
                        modelo_carro = prefixo_base.strip()
                        versao_raw = f"{resto} {versao_raw}".strip()
                        break

                aplicacoes_extraidas.append(
                    {
                        "modelo": modelo_carro,
                        "versao": versao_raw,
                        "ano_inicio": app.get("a1") or "",
                        "ano_fim": app.get("a2") or "",
                    }
                )

            # Fallback secundário se `resumo_aplicacao` vier vazio mas `veiculo` ou `nome_aplicacoes` estiver preenchido
            if not aplicacoes_extraidas:
                nomes_veic = [
                    v.strip()
                    for v in (self._safe_str(hit.get("nome_aplicacoes")) or self._safe_str(hit.get("veiculo"))).split(",")
                    if v.strip()
                ]
                ano_de = hit.get("ano_de") or ""
                ano_ate = hit.get("ano_ate") or ""
                if nomes_veic:
                    for nv in nomes_veic:
                        aplicacoes_extraidas.append(
                            {
                                "modelo": nv.upper(),
                                "versao": self._limpar_versao_vw(self._safe_str(hit.get("modelo"))),
                                "ano_inicio": ano_de,
                                "ano_fim": ano_ate,
                            }
                        )

            # Se mesmo assim a peça não tiver carro vinculado (ex: fluído, acessório ou peça recém-cadastrada)
            if not aplicacoes_extraidas:
                raw_sem_veic = {
                    "marca_peca": "VOLKSWAGEN ORIGINAL",
                    "provedor": self.config.get("nome", "VW REPARADOR"),
                    "codigo": part_number,
                    "montadora": "VW",
                    "modelo": descricao or "PEÇA GENUÍNA",
                    "versao": "",
                    "motor": "",
                    "configuracao_motor": "",
                    "ano_inicio": "",
                    "ano_fim": "",
                    "observacao": obs_geral,
                    "posicao": posicao_val,
                    "lado": lado_val,
                    "descricao_produto": descricao,
                    "imagem": imagem_principal,
                    "imagens": imagens,
                    "referencias": referencias_str,
                    "ficha_tecnica": ficha,
                }
                resultados_loja.append(self.formatar_resultado(raw_sem_veic))
                continue

            for ap in aplicacoes_extraidas:
                raw_loja = {
                    "marca_peca": "VOLKSWAGEN ORIGINAL",
                    "provedor": self.config.get("nome", "VW REPARADOR"),
                    "codigo": part_number,
                    "montadora": "VW",
                    "modelo": ap["modelo"],
                    "versao": ap["versao"],
                    "motor": "",
                    "configuracao_motor": "",
                    "ano_inicio": ap["ano_inicio"],
                    "ano_fim": ap["ano_fim"],
                    "observacao": obs_geral,
                    "posicao": posicao_val,
                    "lado": lado_val,
                    "descricao_produto": descricao,
                    "imagem": imagem_principal,
                    "imagens": imagens,
                    "referencias": referencias_str,
                    "ficha_tecnica": ficha,
                }
                resultados_loja.append(self.formatar_resultado(raw_loja))

        return resultados_loja

    async def _discover_uuids(
        self, client: httpx.AsyncClient, codigo_busca: str, take_limit: int = 10
    ) -> List[str]:
        """
        Etapa 1 (Discovery na Ponte GraphQL): Converte o código pesquisado (ex: '026103547A'
        ou '026.103.547.A') em uma lista de UUIDs internos da plataforma Fraga/VW.
        """
        uuids: List[str] = []

        if len(codigo_busca) >= 32 and codigo_busca.count("-") >= 4:
            return [codigo_busca]

        candidatos = []
        limpo = self._norm_pn(codigo_busca)
        for c in (limpo, codigo_busca.strip().upper()):
            if c and c not in candidatos:
                candidatos.append(c)

        for termo in candidatos:
            payload_code = {
                "query": self.QUERY_BY_CODE,
                "variables": {
                    "q": termo,
                    "by": ["PART_NUMBER"],
                    "skip": 0,
                    "take": take_limit,
                },
            }
            try:
                resp = await client.post(self.url, json=payload_code)
                if resp.status_code == 200:
                    data = resp.json()
                    nodes = (
                        data.get("data", {})
                        .get("catalogSearchByCode", {})
                        .get("nodes", [])
                        or []
                    )
                    for node in nodes:
                        pid = (node.get("product") or {}).get("id")
                        if pid and pid not in uuids:
                            uuids.append(pid)
            except Exception as e:
                logger.warning("REPARADOR_VW", f"Aviso em catalogSearchByCode ({termo}): {e}")

            if uuids:
                return uuids

            payload_ac = {
                "query": self.QUERY_AUTOCOMPLETE,
                "variables": {"q": termo},
            }
            try:
                resp_ac = await client.post(self.url, json=payload_ac)
                if resp_ac.status_code == 200:
                    data_ac = resp_ac.json()
                    nodes_ac = (
                        data_ac.get("data", {})
                        .get("catalogSearch", {})
                        .get("nodes", [])
                        or []
                    )
                    for node in nodes_ac:
                        pid = (node.get("product") or {}).get("id")
                        if pid and pid not in uuids:
                            uuids.append(pid)
            except Exception as e:
                logger.warning("REPARADOR_VW", f"Aviso em catalogSearch fallback ({termo}): {e}")

            if uuids:
                return uuids

        return uuids

    async def _fetch_product(self, client: httpx.AsyncClient, uuid_peca: str) -> Dict[str, Any]:
        """Etapa 2 (Hydration): Busca todos os detalhes de um UUID na ponte GraphQL."""
        payload = {
            "query": self.QUERY_PRODUCT,
            "variables": {"id": uuid_peca},
        }
        try:
            resp = await client.post(self.url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return (data.get("data") or {}).get("product") or {}
            else:
                logger.warning(
                    "REPARADOR_VW",
                    f"HTTP {resp.status_code} ao hidratar UUID {uuid_peca}: {resp.text[:200]}",
                )
        except Exception as e:
            logger.warning("REPARADOR_VW", f"Erro ao hidratar UUID {uuid_peca}: {e}")
        return {}

    def _montar_referencias(self, product_data: Dict[str, Any], part_number: str) -> str:
        """
        Constrói a string padronizada `MARCA: CODIGO | ...` unificando Part Number genuíno,
        códigos antigos (`oldCodes`), códigos completos (`completeCodes`) e `crossReferences`.
        """
        refs: List[str] = []
        vistos = set()

        def add_ref(marca: str, cod: str):
            m = self._safe_str(marca).upper() or "VOLKSWAGEN"
            c = self._safe_str(cod).upper()
            if not c:
                return
            chave = f"{m}: {c}"
            if chave not in vistos:
                vistos.add(chave)
                refs.append(chave)

        if part_number:
            add_ref("VOLKSWAGEN", part_number)

        for old_code in product_data.get("oldCodes") or []:
            add_ref("VOLKSWAGEN", old_code)

        for comp_code in product_data.get("completeCodes") or []:
            add_ref("VOLKSWAGEN", comp_code)

        for cr in product_data.get("crossReferences") or []:
            if isinstance(cr, dict):
                brand_name = self._safe_str((cr.get("brand") or {}).get("name")) or "OEM"
                add_ref(brand_name, cr.get("partNumber"))

        return " | ".join(refs)

    def _montar_ficha_tecnica(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extrai especificações físicas/técnicas e metadados estruturais da peça na base Fraga.
        """
        ficha: Dict[str, str] = {}

        app_desc = self._safe_str(product_data.get("applicationDescription"))
        if app_desc:
            ficha["DESCRIÇÃO COMERCIAL"] = app_desc.upper()

        pg = product_data.get("productGroup") or {}
        if isinstance(pg, dict):
            grupo = self._safe_str(pg.get("name"))
            familia = self._safe_str((pg.get("family") or {}).get("name"))
            sistema = self._safe_str((pg.get("system") or {}).get("name"))
            if grupo:
                ficha["CATEGORIA"] = grupo.upper()
            if sistema:
                ficha["LINHA / SISTEMA"] = sistema.upper()
            if familia:
                ficha["FAMÍLIA"] = familia.upper()

        status = self._safe_str(product_data.get("status"))
        if status:
            ficha["STATUS"] = status.upper()

        old_codes = [self._safe_str(c) for c in (product_data.get("oldCodes") or []) if self._safe_str(c)]
        if old_codes:
            ficha["CÓDIGOS ANTIGOS"] = ", ".join(old_codes).upper()

        complete_codes = [
            self._safe_str(c) for c in (product_data.get("completeCodes") or []) if self._safe_str(c)
        ]
        if complete_codes:
            ficha["CÓDIGOS COMPLETOS"] = ", ".join(complete_codes).upper()

        parsed_specs = self.parse_specifications(product_data.get("specifications"))
        ficha.update(parsed_specs)

        return ficha

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Fluxo Híbrido Resiliente:
        1. Tenta o Catálogo Técnico Reparador VW (GraphQL Fraga V2) + Fallback de Fotos `900x900`.
        2. Se o código não existir na base mecânica da Fraga (ou se a ponte estiver indisponível),
           aciona automaticamente o Fallback Completo nas **53.800+ peças** do `pecas.vw.com.br`!
        """
        codigo_busca = (termo or "").strip().upper()
        if not codigo_busca:
            return []

        todos_resultados: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=25.0, follow_redirects=True) as client:
                take_limit = 10
                if isinstance(self.config.get("mapeamento"), str) and self.config["mapeamento"]:
                    try:
                        mapa = json.loads(self.config["mapeamento"])
                        take_limit = int(mapa.get("take_limit", 10))
                    except Exception:
                        pass

                # 1. Tenta Discovery no Catálogo Técnico Reparador VW (GraphQL)
                uuids = await self._discover_uuids(client, codigo_busca, take_limit=take_limit)

                if uuids:
                    logger.info("REPARADOR_VW", f"Descobertos {len(uuids)} UUID(s) no GraphQL para '{codigo_busca}'.")

                    tasks = [self._fetch_product(client, uid) for uid in uuids]
                    produtos = await asyncio.gather(*tasks, return_exceptions=True)

                    for product_data in produtos:
                        if isinstance(product_data, Exception) or not product_data:
                            continue

                        part_number = self._safe_str(product_data.get("partNumber")) or codigo_busca
                        brand_peca = (
                            self._safe_str((product_data.get("brand") or {}).get("name"))
                            or "VOLKSWAGEN ORIGINAL"
                        )

                        pg = product_data.get("productGroup") or {}
                        grupo_nome = self._safe_str(pg.get("name")) if isinstance(pg, dict) else ""
                        app_desc = self._safe_str(product_data.get("applicationDescription"))
                        descricao_produto = grupo_nome or app_desc

                        # Imagens: Prioridade 1 (Fraga) -> Prioridade 2 (Fallback A: Loja Oficial 900x900)
                        imagens: List[str] = []
                        for img in product_data.get("images") or []:
                            if isinstance(img, dict):
                                url_img = self._safe_str(img.get("imageUrl") or img.get("thumbnailUrl"))
                                if url_img and url_img not in imagens:
                                    imagens.append(url_img)

                        if not imagens:
                            imagens = await self._fetch_loja_oficial_photos(client, part_number)

                        imagem_principal = imagens[0] if imagens else ""

                        ficha_tecnica = self._montar_ficha_tecnica(product_data)
                        referencias_str = self._montar_referencias(product_data, part_number)

                        posicao_spec = ficha_tecnica.get("POSIÇÃO", "")
                        lado_spec = ficha_tecnica.get("LADO", "")
                        direcao_spec = ficha_tecnica.get("DIREÇÃO", "")

                        vehicles = product_data.get("vehicles") or []

                        if not vehicles:
                            # Se a peça existe na Fraga mas veio SEM veículos (ex: faixa de luz 2G5941653),
                            # tentamos enriquecer os veículos via Loja Oficial antes de cair no genérico!
                            loja_enriquecida = await self._buscar_fallback_loja_oficial(
                                client, part_number, take_limit=1
                            )
                            if loja_enriquecida and any(
                                r.get("modelo") not in ("PEÇA GENUÍNA", descricao_produto.upper())
                                for r in loja_enriquecida
                            ):
                                todos_resultados.extend(loja_enriquecida)
                                continue

                            obs_universal = (
                                "APLICAÇÃO UNIVERSAL"
                                if product_data.get("containsUniversalApplication")
                                else self._safe_str(product_data.get("summaryApplication"))
                            )
                            raw_fallback = {
                                "marca_peca": brand_peca,
                                "provedor": self.config.get("nome", "VW REPARADOR"),
                                "codigo": part_number,
                                "montadora": "VW",
                                "modelo": descricao_produto or "PEÇA GENUÍNA",
                                "versao": "",
                                "motor": "",
                                "configuracao_motor": "",
                                "ano_inicio": "",
                                "ano_fim": "",
                                "observacao": obs_universal,
                                "posicao": posicao_spec,
                                "lado": lado_spec,
                                "direcao": direcao_spec,
                                "descricao_produto": descricao_produto,
                                "imagem": imagem_principal,
                                "imagens": imagens,
                                "referencias": referencias_str,
                                "ficha_tecnica": ficha_tecnica,
                            }
                            todos_resultados.append(self.formatar_resultado(raw_fallback))
                            continue

                        for v in vehicles:
                            if not isinstance(v, dict):
                                continue

                            montadora = self._padronizar_montadora_vw(self._safe_str(v.get("brand")))
                            modelo = self._safe_str(v.get("name")).replace("\xa0", " ")
                            versao = self._limpar_versao_vw(self._safe_str(v.get("model")))
                            engine_name_raw = self._safe_str(v.get("engineName"))
                            engine_config_raw = self._safe_str(v.get("engineConfiguration"))
                            engine_name, engine_config = self._limpar_motor_vw(engine_name_raw, engine_config_raw)

                            only_txt = self._safe_str(v.get("only"))
                            note_txt = self._safe_str(v.get("note"))
                            obs_parts = []
                            if only_txt:
                                obs_parts.append(f"APENAS: {only_txt}")
                            if note_txt:
                                obs_parts.append(note_txt)
                            obs_final = " | ".join(obs_parts)

                            raw_item = {
                                "marca_peca": brand_peca,
                                "provedor": self.config.get("nome", "VW REPARADOR"),
                                "codigo": part_number,
                                "montadora": montadora,
                                "modelo": modelo,
                                "versao": versao,
                                "motor": engine_name,
                                "configuracao_motor": engine_config,
                                "ano_inicio": v.get("startYear") or "",
                                "ano_fim": v.get("endYear") or "",
                                "observacao": obs_final,
                                "apenas": only_txt,
                                "posicao": posicao_spec,
                                "lado": lado_spec,
                                "direcao": direcao_spec,
                                "descricao_produto": descricao_produto,
                                "imagem": imagem_principal,
                                "imagens": imagens,
                                "referencias": referencias_str,
                                "ficha_tecnica": ficha_tecnica,
                            }

                            todos_resultados.append(self.formatar_resultado(raw_item))

                # 2. Fallback B (53.800+ peças do pecas.vw.com.br):
                # Acionado se o GraphQL não encontrou nada para o código pesquisado!
                if not todos_resultados:
                    todos_resultados = await self._buscar_fallback_loja_oficial(
                        client, codigo_busca, take_limit=take_limit
                    )

        except Exception as e:
            logger.error(
                "REPARADOR_VW",
                f"Erro crítico na busca do código '{codigo_busca}': {e}\n{traceback.format_exc()}",
            )

        return todos_resultados
