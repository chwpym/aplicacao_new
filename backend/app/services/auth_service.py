import httpx
import asyncio
from typing import Dict, Optional
import re
import json
from app.models import models


class AuthService:
    def __init__(self):
        self.cache = {}  # Dict[provedor_id, token_data]

    async def get_token(self, provedor: models.Provedor) -> Optional[str]:
        """
        Retorna um token válido para o provedor. Tenta carregar do cache primeiro.
        """
        if provedor.id in self.cache:
            # TODO: Validar expiração
            return self.cache[provedor.id].get("token")

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
                        access_token = resp_token.json().get("access_token")
                        print(f"[{provedor.nome}] Sucesso! Token obtido (cat_{brand}).")
                        self.cache[provedor.id] = {"token": access_token}
                        return access_token

                print(
                    f"[{provedor.nome}] Falha no login (Status: {resp_post.status_code})"
                )
                return None

            except Exception as e:
                print(f"[{provedor.nome}] Erro inesperado: {e}")
                return None


auth_service = AuthService()
