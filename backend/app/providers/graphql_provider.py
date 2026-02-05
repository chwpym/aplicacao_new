import httpx
import json
from app.providers.base_provider import BaseProvider
from app.services.auth_service import auth_service

class GraphQLProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = config['url']
        self.query = config['query']
        self.headers = config.get('headers', {})
        self.login_required = config.get('login_required', False)
        self.username = config.get('username')
        self.password = config.get('password')
        self.token = None # Cache do token JWT

    async def _get_auth_token(self):
        """Usa o auth_service para obter o token de acesso."""
        from app.models.models import Provedor
        p_simulado = Provedor(
            id=self.config['id'],
            nome=self.config['nome'],
            url=self.config['url'],
            username=self.username,
            password=self.password
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
            "variables": {
                "query": code,
                "skip": 0,
                "take": 1
            }
        }
        
        try:
            response = await client.post(self.url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                nodes = data.get('data', {}).get('catalogSearch', {}).get('nodes', [])
                if nodes:
                    return nodes[0]['product']['id']
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
                **self.headers
            }
            
            if self.login_required:
                auth_data = await self._get_auth_token()
                if auth_data:
                    # Se for Authomix, o retorno contém KEYCLOAK (cookies)
                    if 'KEYCLOAK' in auth_data:
                        request_headers['Cookie'] = auth_data
                        print(f"[{self.config['nome']}] Login realizado via Cookies.")
                    else:
                        request_headers['Authorization'] = f"Bearer {auth_data}"
                        print(f"[{self.config['nome']}] Login realizado via Bearer Token.")
                else:
                    print(f"[{self.config['nome']}] ALERTA: Login Requerido, mas falhou. Tentando busca sem credenciais...")

            # Etapa 1: Discovery (Se o id_peca não for um UUID, tentamos descobrir)
            uuid_alvo = id_peca
            # Heurística simples: UUIDs do Fraga geralmente têm 20+ caracteres e hifens.
            # Se for um código curto (ex: 02525BRAGF), tentamos o Discovery.
            if len(id_peca) < 20 or "-" not in id_peca:
                print(f"[{self.config['nome']}] Tentando descobrir UUID para: {id_peca}")
                descoberto = await self.search_product_id(client, id_peca, request_headers)
                if descoberto:
                    uuid_alvo = descoberto
                    print(f"[{self.config['nome']}] UUID encontrado: {uuid_alvo}")
                else:
                    return []

            # Etapa 2: Retrieval (com tentativa multi-mercado)
            market_values = ["BRA", "BRAZIL", "BR", "Brasil"]
            ultima_excecao = None
            
            for market in market_values:
                payload = {
                    "query": self.query,
                    "variables": {
                        "id": uuid_alvo,
                        "market": market
                    }
                }
                
                try:
                    response = await client.post(self.url, json=payload, headers=request_headers)
                    data = response.json()
                    
                    if 'errors' in data:
                        error_msg = str(data['errors'])
                        # Se o erro for relacionado ao valor do enum market, tentamos o próximo
                        if 'EnumValueNode' in error_msg or 'MarketType' in error_msg or 'market' in error_msg.lower():
                            print(f"[{self.config['nome']}] Market '{market}' não aceito, tentando próximo...")
                            continue
                        print(f"Erro GraphQL ({self.config['nome']}): {data.get('errors')}")
                        
                    if not data or 'data' not in data or not data['data']:
                        continue
                        
                    product_data = data['data'].get('product')
                    if not product_data:
                        continue
                        
                    vehicles = product_data.get('vehicles', [])
                    
                    # Extrair referências originais (OEM)
                    referencias_formatadas = ""
                    if product_data.get('crossReferences'):
                        refs = []
                        for cr in product_data['crossReferences']:
                            brand_name = cr.get('brand', {}).get('name', '').upper()
                            # Se for Original, GM Original, OEM, etc.
                            if 'ORIGINAL' in brand_name or 'OEM' in brand_name:
                                refs.append(f"{brand_name}: {cr.get('partNumber')}")
                        referencias_formatadas = " | ".join(refs)

                    # Formatar resultados
                    resultados = [self.formatar_resultado(v) for v in vehicles]
                    
                    # Extrair lista de imagens
                    imagens = []
                    if product_data.get('images'):
                        imagens = [img.get('imageUrl') for img in product_data['images'] if img.get('imageUrl')]
                    
                    for res in resultados:
                        res['imagens'] = imagens
                        res['imagem'] = imagens[0] if imagens else None
                        res['codigo'] = product_data.get('partNumber', id_peca)
                        res['referencias'] = referencias_formatadas
                        
                    return resultados
                    
                except Exception as e:
                    ultima_excecao = e
                    continue
            
            if ultima_excecao:
                print(f"Erro ao buscar no provedor {self.config['nome']} após tentar todos os mercados: {ultima_excecao}")
            return []
