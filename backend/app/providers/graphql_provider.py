import httpx
import json
from app.providers.base_provider import BaseProvider
from app.services.auth_service import auth_service


class GraphQLProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = config["url"]
        self.query = config["query"]
        self.headers = config.get("headers", {})
        self.login_required = config.get("login_required", False)
        self.username = config.get("username")
        self.password = config.get("password")
        self.token = None  # Cache do token JWT

    async def _get_auth_token(self):
        """Usa o auth_service para obter o token de acesso."""
        from app.models.models import Provedor

        p_simulado = Provedor(
            id=self.config["id"],
            nome=self.config["nome"],
            url=self.config["url"],
            username=self.username,
            password=self.password,
            headers=self.headers,
        )
        return await auth_service.get_token(p_simulado)

    async def search_product_id(self, client, code: str, headers: dict) -> str:
        """
        Primeira Etapa: Converte o Código de Peça em um ID Interno (UUID).
        """
        discovery_query = """
        query($query: String!, $skip: Int, $take: Int) {
          catalogSearch(query: $query, skip: $skip, take: $take) {
            nodes {
              product {
                id
                partNumber
              }
            }
          }
        }
        """
        payload = {
            "query": discovery_query,
            "variables": {"query": code, "skip": 0, "take": 1},
        }

        try:
            response = await client.post(self.url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data and str(data["errors"]).find("UAN-402") != -1:
                    print(f"[{self.config['nome']}] ALERTA CRÍTICO: API retornou Não Autorizado (UAN-402) no discovery! Verifique se o provedor exige credenciais ou se o token expirou.")
                
                nodes = data.get("data", {}).get("catalogSearch", {}).get("nodes", [])
                if nodes:
                    return nodes[0]["product"]["id"]
            elif response.status_code in [401, 403]:
                print(f"[{self.config['nome']}] ALERTA CRÍTICO: API retornou HTTP {response.status_code} no discovery! Verifique as credenciais.")
                
            return None
        except Exception as e:
            print(f"Erro na descoberta de UUID ({self.config['nome']}): {e}")
            return None

    async def buscar(self, id_peca: str):
        """
        Executa a busca inteligente em dois estágios.
        1. Discovery (Código -> UUID)
        2. Retrieval (UUID -> Aplicações)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Inicializa os headers
            request_headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                **self.headers,
            }

            if self.login_required:
                auth_data = await self._get_auth_token()
                if auth_data:
                    # Se for Authomix, o retorno contém KEYCLOAK (cookies)
                    if "KEYCLOAK" in auth_data:
                        request_headers["Cookie"] = auth_data
                        print(f"[{self.config['nome']}] Login realizado via Cookies.")
                    else:
                        request_headers["Authorization"] = f"Bearer {auth_data}"
                        print(
                            f"[{self.config['nome']}] Login realizado via Bearer Token."
                        )
                else:
                    print(
                        f"[{self.config['nome']}] ALERTA: Login Requerido, mas falhou. Tentando busca sem credenciais..."
                    )

            # Etapa 1: Discovery (Se o id_peca não for um UUID, tentamos descobrir)
            uuid_alvo = id_peca
            # Heurística simples: UUIDs do Fraga geralmente têm 20+ caracteres e hifens.
            # Se for um código curto (ex: 02525BRAGF), tentamos o Discovery.
            if len(id_peca) < 20 or "-" not in id_peca:
                print(
                    f"[{self.config['nome']}] Tentando descobrir UUID para: {id_peca}"
                )
                descoberto = await self.search_product_id(
                    client, id_peca, request_headers
                )
                if descoberto:
                    uuid_alvo = descoberto
                    print(f"[{self.config['nome']}] UUID encontrado: {uuid_alvo}")
                else:
                    return []

            # Etapa 2: Retrieval (com tentativa multi-mercado)
            market_values = ["BRA", "BRAZIL", "BR", "Brasil"]
            
            import asyncio
            async def fetch_market(market):
                payload = {
                    "query": self.query,
                    "variables": {"id": uuid_alvo, "market": market},
                }
                try:
                    response = await client.post(
                        self.url, json=payload, headers=request_headers
                    )
                    data = response.json()

                    if "errors" in data:
                        error_str = str(data["errors"])
                        if "UAN-402" in error_str or "Unauthorized" in error_str:
                            print(f"[{self.config['nome']}] ALERTA CRÍTICO: API retornou Não Autorizado (UAN-402) na busca! O provedor pode ter alterado para acesso restrito.")
                        
                        if (
                            "EnumValueNode" in error_str
                            or "MarketType" in error_str
                            or "market" in error_str.lower()
                        ):
                            return None

                    if (
                        not data
                        or "data" not in data
                        or not data["data"]
                        or not data["data"].get("product")
                    ):
                        return None

                    return data["data"].get("product")
                except Exception as e:
                    return None

            # Dispara requisições para todos os mercados possíveis ao mesmo tempo
            tasks = [fetch_market(m) for m in market_values]
            resultados_mercados = await asyncio.gather(*tasks, return_exceptions=True)
            
            product_data = None
            for res in resultados_mercados:
                if isinstance(res, dict) and res:
                    product_data = res
                    break

            if not product_data:
                print(f"[{self.config['nome']}] Produto '{uuid_alvo}' não acessível em nenhum dos mercados testados.")
                return []

            # Garantir que vehicles seja uma lista
            vehicles = product_data.get("vehicles") or []

            # Extrair referências originais e similares
            referencias_formatadas = ""
            if product_data.get("crossReferences"):
                refs = []
                for cr in product_data["crossReferences"]:
                    brand_name = cr.get("brand", {}).get("name", "").upper()
                    refs.append(f"{brand_name}: {cr.get('partNumber')}")
                referencias_formatadas = " | ".join(refs)

            # Formatar resultados
            resultados = [
                self.formatar_resultado(v, product_data) for v in vehicles if v is not None
            ]

            # Extrair lista de imagens
            imagens = []
            if product_data.get("images"):
                imagens = [
                    img.get("imageUrl")
                    for img in product_data["images"]
                    if img.get("imageUrl")
                ]

            for res in resultados:
                res["imagens"] = imagens
                res["imagem"] = imagens[0] if imagens else None
                res["codigo"] = product_data.get("partNumber", id_peca)
                res["referencias"] = referencias_formatadas

            return resultados
    def formatar_resultado(self, vehicle: dict, product_data: dict = None) -> dict:
        """
        Prepara os dados do GraphQL/Fraga para o BaseProvider.
        """
        def safe_label(field_obj):
            if field_obj is None: return ""
            if isinstance(field_obj, dict):
                val = field_obj.get("value") or field_obj.get("label") or field_obj.get("name")
                return str(val).upper().strip() if val else ""
            val = str(field_obj).strip()
            if val.upper() in ["NONE", "NULL", "AUTH_NOT_AUTHORIZED"]: return ""
            return val.upper()

        # 1. Mapeamento para o padrão BaseProvider
        # O Fraga costuma mandar Montadora em 'brand' (objeto) e Carro em 'name'.
        brand_obj = vehicle.get("brand")
        brand_name = safe_label(brand_obj)
        
        engine_name = safe_label(vehicle.get("engineName"))
        engine_code = safe_label(vehicle.get("engineTechnicalCode"))
        
        # O Cód. Técnico do Motor (ex: C20NE) ajuda na precisão, vamos adicioná-lo ao Motor ou Configuração
        motor_completo = engine_name
        if engine_code and engine_code not in engine_name:
            motor_completo = f"{engine_name} [{engine_code}]" if engine_name else engine_code

        raw_data = {
            "montadora": brand_name,
            "modelo": safe_label(vehicle.get("name")),
            "versao": safe_label(vehicle.get("model")),
            "motor": motor_completo,
            "configuracao_motor": safe_label(vehicle.get("engineConfiguration")),
            "combustivel": safe_label(vehicle.get("fuel")),
            **vehicle
        }
        raw_data["provedor"] = self.config.get("nome", "PROVEDOR").upper()
        
        if product_data:
            raw_data["specifications"] = product_data.get("specifications")
            # Descrição comercial
            if not raw_data.get("restriction") and not raw_data.get("only"):
                raw_data["observacao"] = product_data.get("applicationDescription")

            # Ficha Técnica
            parsed_specs = self.parse_specifications(product_data.get("specifications"))
            raw_data["ficha_tecnica"] = {
                "DESCRIÇÃO COMERCIAL": product_data.get("applicationDescription"),
                "CATEGORIA": product_data.get("productGroup", {}).get("name") if isinstance(product_data.get("productGroup"), dict) else "",
                **parsed_specs
            }

            # Extração de campos estruturados
            if "POSIÇÃO" in parsed_specs: raw_data["posicao"] = parsed_specs["POSIÇÃO"]
            if "LADO" in parsed_specs: raw_data["lado"] = parsed_specs["LADO"]
            if "DIREÇÃO" in parsed_specs: raw_data["direcao"] = parsed_specs["DIREÇÃO"]

        # 2. Chama o formatador base (A BASE É SAGRADA E AGORA É INTELIGENTE)
        # O BaseProvider vai usar o Master Catalog para validar se brand_name é marca ou modelo.
        return super().formatar_resultado(raw_data)
