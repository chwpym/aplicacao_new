from typing import List, Dict, Any, Optional
import httpx
from app.providers.graphql_provider import GraphQLProvider
from app.services.auth_service import auth_service


class CofapProvider(GraphQLProvider):
    """
    Provedor especializado para o catálogo Monroe/Cofap (Fraga).
    Herda do GraphQLProvider, mas permite customizações específicas de parser ou query
    para evitar interferir nos outros catálogos (Perfect, Spicer, etc).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Forçamos headers mínimos se não existirem
        if not self.headers:
            self.headers = {
                "Origin": "https://cofap.catalogofraga.com.br",
                "Referer": "https://cofap.catalogofraga.com.br/",
            }

    async def buscar(self, id_peca: str) -> List[Dict[str, Any]]:
        """
        Sobrescreve a busca para capturar referências cruzadas e imagens detalhadas.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_headers = self.headers.copy() if self.headers else {}
            if self.config.get("login_required"):
                # Mock de provedor para o auth_service
                from app.models import models

                p_simulado = models.Provedor(
                    id=self.config.get("id", 0),
                    nome=self.config.get("nome", ""),
                    url=self.url,
                    headers=str(self.headers),
                    username=self.config.get("username"),
                    password=self.config.get("password"),
                )
                auth_data = await auth_service.get_token(p_simulado)
                if auth_data:
                    request_headers["Authorization"] = f"Bearer {auth_data}"
                    print(f"[{self.config['nome']}] Login realizado via Bearer Token.")

            # 1. Discovery
            uuid_alvo = id_peca
            if len(id_peca) < 20 or "-" not in id_peca:
                uuid_alvo = await self.search_product_id(
                    client, id_peca, request_headers
                )
                if not uuid_alvo:
                    return []

            # 2. Retrieval com suporte a múltiplos mercados (Prioridade BRA)
            market_values = ["BRA", "BR", "BRAZIL", "Brasil"]
            for market in market_values:
                payload = {
                    "query": self.query,
                    "variables": {"id": uuid_alvo, "market": market},
                }
                try:
                    response = await client.post(
                        self.url, json=payload, headers=request_headers
                    )
                    data = response.json()
                    
                    if "errors" in data and str(data["errors"]).find("UAN-402") != -1:
                        print(f"[{self.config['nome']}] ALERTA CRÍTICO: API retornou Não Autorizado (UAN-402) na busca do Cofap! Verifique as credenciais.")
                        
                    product_data = data.get("data", {}).get("product")

                    if not product_data or not product_data.get("vehicles"):
                        continue

                    # Extrair Referências Cruzadas Completas
                    referencias = []
                    if product_data.get("crossReferences"):
                        for cr in product_data["crossReferences"]:
                            brand = cr.get("brand", {}).get("name") or "OUTRO"
                            part = cr.get("partNumber") or ""
                            if part:
                                referencias.append(f"{brand}: {part}")
                    refs_str = " | ".join(referencias)

                    # Extrair Imagens
                    imagens = []
                    if product_data.get("images"):
                        imagens = [
                            img.get("imageUrl")
                            for img in product_data["images"]
                            if img.get("imageUrl")
                        ]

                    # Extrair 'Modelo' das especificações (Ex: SUPER)
                    modelo_espec = ""
                    if product_data.get("specifications"):
                        for spec in product_data["specifications"]:
                            if spec.get("description") == "Modelo":
                                modelo_espec = spec.get("value") or ""
                                break

                    resultados = []
                    for v in product_data["vehicles"]:
                        if not v:
                            continue
                        res = self.formatar_resultado(v, product_data)

                        # Injetar dados do produto
                        res["referencias"] = refs_str
                        res["imagens"] = imagens
                        res["imagem"] = imagens[0] if imagens else None
                        res["codigo"] = product_data.get("partNumber", id_peca)

                        # Se o modelo do veículo estiver vazio, tenta usar o 'Modelo' das specs (SUPER)
                        if not res.get("modelo") and modelo_espec:
                            res["modelo"] = modelo_espec
                        elif modelo_espec and modelo_espec not in res.get(
                            "observacao", ""
                        ):
                            # Senão, anexa na observação para não perder a info
                            res["observacao"] = (
                                f"{modelo_espec} | {res['observacao']}".strip(" | ")
                            )

                        resultados.append(res)

                    return resultados
                except Exception as e:
                    print(f"[{self.config['nome']}] Erro no mercado {market}: {e}")
                    continue

            return []

    def formatar_resultado(self, vehicle: Dict[str, Any], product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Sobrescreve a formatação para lidar com campos que a COFAP bloqueia (AUTH_NOT_AUTHORIZED).
        """

        def safe_label(field_obj):
            if field_obj is None:
                return ""
            # Se for dicionário (padrão Fraga/GraphQL)
            if isinstance(field_obj, dict):
                val = field_obj.get("value")
                if val is None:
                    # Tenta label se value falhar (alguns campos Fraga)
                    val = field_obj.get("label") or field_obj.get("name")
                if val is None:
                    return ""
                return str(val).upper().strip()

            # Se for valor direto (ano_inicio, etc)
            val = str(field_obj).strip()
            if val.upper() in ["NONE", "NULL", "AUTH_NOT_AUTHORIZED"]:
                return ""
            return val.upper()

        # Preparamos os dados para o formatador base
        raw_data = vehicle.copy()
        raw_data["provedor"] = self.config.get("nome", "COFAP").upper()
        
        if product_data:
            # Injetamos o que for necessário para o motor universal da BaseProvider
            raw_data["specifications"] = product_data.get("specifications")
            raw_data["ficha_tecnica"] = {
                "Descrição Comercial": product_data.get("applicationDescription"),
                "Categoria": product_data.get("productGroup", {}).get("name")
            }
            # Unifica especificações estruturadas
            parsed_specs = self.parse_specifications(product_data.get("specifications"))
            raw_data["ficha_tecnica"].update(parsed_specs)

        # Chama o formatador base para garantir an an PecaSchema e o mapeamento correto de colunas
        res = super().formatar_resultado(raw_data)

        # Combinar observações (only, restriction, note) com an an segurança da Cofap
        obs_parts = [
            safe_label(vehicle.get("only")),
            safe_label(vehicle.get("restriction")),
            safe_label(vehicle.get("note")),
            safe_label(vehicle.get("fuelType")),
            safe_label(vehicle.get("transmissionType")),
        ]
        res["observacao"] = " | ".join([p for p in obs_parts if p]).strip()

        return res

    async def search_product_id(self, client, code: str, headers: dict) -> str:
        """
        Sobrescreve o discovery para incluir o market: "BRA", obrigatório para COFAP.
        """
        discovery_query = """
        query($query: String!, $skip: Int, $take: Int, $market: MarketType!) {
          catalogSearch(query: $query, skip: $skip, take: $take, market: $market) {
            nodes {
              product {
                id
                partNumber
              }
            }
          }
        }
        """
        markets = ["BRA", "BR", "BRAZIL", "Brasil"]
        print(f"[{self.config.get('nome')}] Discovery iniciando para: {code}")
        for mkt in markets:
            payload = {
                "query": discovery_query,
                "variables": {"query": code, "skip": 0, "take": 1, "market": mkt},
            }
            try:
                response = await client.post(self.url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data and str(data["errors"]).find("UAN-402") != -1:
                        print(f"[{self.config.get('nome')}] ALERTA CRÍTICO: API retornou Não Autorizado (UAN-402) no discovery! Verifique as credenciais.")
                        
                    nodes = data.get("data", {}).get("catalogSearch", {}).get("nodes", [])
                    if nodes:
                        uuid = nodes[0]["product"]["id"]
                        print(f"[{self.config.get('nome')}] UUID descoberto no mercado {mkt}: {uuid}")
                        return uuid
                elif response.status_code in [401, 403]:
                    print(f"[{self.config.get('nome')}] ALERTA CRÍTICO: API retornou HTTP {response.status_code} no discovery! Verifique as credenciais.")
            except Exception as e:
                print(f"[{self.config.get('nome')}] Falha discovery no mercado {mkt}: {e}")
                continue
        return None

