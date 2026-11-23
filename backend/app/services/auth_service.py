import httpx
import asyncio
from typing import Dict, Optional
import re
import json
import time
import base64
from app.models import models


class AuthService:
    def __init__(self):
        self.cache = {}  # Dict[provedor_id, token_data]

    def _get_jwt_exp(self, token: str) -> Optional[int]:
        """
        Extrai o campo 'exp' (Unix timestamp) do payload do JWT.
        Não verifica assinatura — apenas lê o payload para saber quando expira.
        """
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            # JWT usa base64url — adicionar padding se necessário
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
            return payload.get("exp")
        except Exception:
            return None

    def _is_token_expired(self, token_data: dict) -> bool:
        """
        Verifica se o token cacheado está expirado.
        Usa o campo 'exp' do JWT com margem de segurança de 60 segundos.
        Fallback: se não houver 'exp', usa o tempo de criação (5 min de validade assumida).
        """
        exp = token_data.get("exp")
        if exp is not None:
            # Considera expirado 60s antes do prazo real (margem de segurança)
            return time.time() >= (exp - 60)
        # Fallback: sem informação de expiração, assume 5 minutos (300s)
        created_at = token_data.get("created_at", 0)
        return (time.time() - created_at) >= 300

    def invalidate_cache(self, provedor_id: int):
        """
        Remove o token do cache forçando re-login na próxima chamada.
        Usado quando a API retorna 401/403 ou erro UAN-402.
        """
        if provedor_id in self.cache:
            del self.cache[provedor_id]
            print(f"[AuthService] Cache invalidado para provedor_id={provedor_id}. Novo login será feito.")

    async def get_token(self, provedor: models.Provedor) -> Optional[str]:
        """
        Retorna um token válido para o provedor. Tenta carregar do cache primeiro.
        Se o token estiver expirado, remove do cache e refaz o login automaticamente.
        """
        if provedor.id in self.cache:
            token_data = self.cache[provedor.id]
            if not self._is_token_expired(token_data):
                # Token ainda válido — retorna do cache
                return token_data.get("token")
            else:
                # Token expirado — remove cache e refaz login
                print(f"[AuthService] Token expirado para provedor_id={provedor.id}. Renovando...")
                del self.cache[provedor.id]

        # Detectar se é um catálogo gerido pela Fraga (Authomix, Perfect, Indisa, etc.)
        headers_dict = {}
        if provedor.headers:

            try:
                # headers pode vir como string JSON do banco ou como dict se já processado
                headers_dict = (
                    json.loads(provedor.headers)
                    if isinstance(provedor.headers, str)
                    else provedor.headers
                )
            except:
                headers_dict = {}

        origin = headers_dict.get("origin") or headers_dict.get("Origin", "")
        # Fallback para extrair da URL se origin faltar
        is_fraga = (
            "catalogofraga.com.br" in origin.lower()
            or "authomix.com.br" in origin.lower()
            or (provedor.url and "bff.catalogofraga.com.br" in provedor.url.lower())
        )

        if is_fraga:
            print(
                f"[{provedor.nome}] Detectado catálogo Fraga. Iniciando login Keycloak..."
            )
            return await self._login_keycloak_fraga(provedor, origin)

        return None

    async def _login_keycloak_fraga(
        self, provedor: models.Provedor, origin_url: str
    ) -> Optional[str]:
        """
        Realiza o fluxo de login no Keycloak da Fraga de forma dinâmica.
        """
        username = provedor.username.strip() if provedor.username else ""
        password = provedor.password.strip() if provedor.password else ""

        if not username or not password:
            print(f"[{provedor.nome}] Login requerido mas credenciais não fornecidas.")
            return None

        # Headers de navegador real
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Extrair a "marca" (brand/realm) da URL de Origem ou Nome
        # Padrões: https://perfect.catalogofraga.com.br
        brand = "authomix"  # Default
        if origin_url:
            match = re.search(r"https?://(?:catalogo\.)?([^.]+)\.", origin_url)
            if match:
                brand = match.group(1).lower()
        elif "cofap" in provedor.nome.lower():
            brand = "cofap"

        realm = f"cat_{brand}"
        if brand == "wahler":
            realm = "cat_whaler"
        elif brand == "bastosjuntas" or "bastos" in brand:
            realm = "cat_bastos"

        base_catalog_url = (
            origin_url.rstrip("/")
            if origin_url
            else f"https://{brand}.catalogofraga.com.br"
        )

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                # 1. Iniciar sessão para pegar state/execution
                init_url = f"{base_catalog_url}/autenticacao"
                print(
                    f"[{provedor.nome}] Login Keycloak (Brand: {brand}, Realm: {realm}) em {init_url}..."
                )

                resp = await client.get(init_url, headers={"User-Agent": user_agent})

                if "accounts.fraga.com.br" not in str(resp.url):
                    login_page_url = f"https://accounts.fraga.com.br/realms/{realm}/protocol/openid-connect/auth?client_id=catalog-user&redirect_uri={base_catalog_url}/&response_type=code&scope=openid"
                    resp = await client.get(
                        login_page_url, headers={"User-Agent": user_agent}
                    )

                if resp.status_code != 200:
                    print(
                        f"[{provedor.nome}] Erro ao carregar página de login ({resp.status_code})"
                    )
                    return None

                # Extrair action e campos

                action_match = re.search(r'action="([^"]+)"', resp.text)
                if not action_match:
                    print(f"[{provedor.nome}] Action não encontrado.")
                    return None

                auth_url = action_match.group(1).replace("&amp;", "&")
                payload = {
                    "username": username,
                    "password": password,
                    "login": "Entrar",
                }

                for field in ["execution", "session_code", "client_id", "tab_id"]:
                    match = re.search(rf'name="{field}"[^>]+value="([^"]+)"', resp.text)
                    if match:
                        payload[field] = match.group(1)

                # 3. POST Credentials
                resp_post = await client.post(
                    auth_url,
                    data=payload,
                    headers={"Referer": str(resp.url), "User-Agent": user_agent},
                    follow_redirects=False,
                )

                if resp_post.status_code == 302:
                    location = resp_post.headers.get("Location", "")
                    code_match = re.search(r"code=([^&]+)", location)
                    if not code_match:
                        return None

                    auth_code = code_match.group(1)
                    token_url = f"https://accounts.fraga.com.br/realms/{realm}/protocol/openid-connect/token"
                    token_payload = {
                        "code": auth_code,
                        "grant_type": "authorization_code",
                        "client_id": "catalog-user",
                        "redirect_uri": f"{base_catalog_url}/",
                    }

                    resp_token = await client.post(
                        token_url,
                        data=token_payload,
                        headers={"User-Agent": user_agent},
                    )

                    if resp_token.status_code == 200:
                        token_json = resp_token.json()
                        access_token = token_json.get("access_token")
                        exp = self._get_jwt_exp(access_token) if access_token else None
                        self.cache[provedor.id] = {
                            "token": access_token,
                            "exp": exp,
                            "created_at": time.time(),
                        }
                        exp_info = f", expira em {int(exp - time.time())}s" if exp else ""
                        print(f"[{provedor.nome}] Sucesso! Token obtido (cat_{brand}){exp_info}.")
                        return access_token

                print(
                    f"[{provedor.nome}] Falha no login (Status: {resp_post.status_code})"
                )
                return None

            except Exception as e:
                print(f"[{provedor.nome}] Erro inesperado: {e}")
                return None


auth_service = AuthService()
