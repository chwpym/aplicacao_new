import httpx
import asyncio
from typing import Dict, Optional
import re
from app.models import models

class AuthService:
    def __init__(self):
        self.cache = {} # Dict[provedor_id, token_data]

    async def get_token(self, provedor: models.Provedor) -> Optional[str]:
        """
        Retorna um token válido para o provedor. Tenta carregar do cache primeiro.
        """
        if provedor.id in self.cache:
            # TODO: Validar expiração
            return self.cache[provedor.id].get('token')
        
        if provedor.nome.upper() == 'AUTHOMIX' or 'AUTHOMIX' in provedor.url.upper():
            return await self._login_keycloak_fraga(provedor)
        
        return None

    async def _login_keycloak_fraga(self, provedor: models.Provedor) -> Optional[str]:
        """
        Realiza o fluxo de login no Keycloak da Fraga (Authomix).
        """
        username = provedor.username.strip() if provedor.username else ""
        password = provedor.password.strip() if provedor.password else ""

        if not username or not password:
            print(f"[{provedor.nome}] Login requerido mas credenciais não fornecidas (após strip).")
            return None

        # Headers de navegador real
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                # 1. Começamos na URL do catálogo para deixar que ele nos redirecione para o login
                # Isso garante que pegamos o state e nonce corretos.
                init_url = "https://catalogo.authomix.com.br/autenticacao"
                print(f"[{provedor.nome}] Iniciando sessão em {init_url}...")
                
                resp = await client.get(init_url, headers={"User-Agent": user_agent})
                
                # Se não redirecionou para o accounts.fraga.com.br, forçamos a ida
                if "accounts.fraga.com.br" not in str(resp.url):
                    login_page_url = "https://accounts.fraga.com.br/realms/cat_authomix/protocol/openid-connect/auth?client_id=catalog-user&redirect_uri=https://catalogo.authomix.com.br&response_type=code&scope=openid"
                    resp = await client.get(login_page_url, headers={"User-Agent": user_agent})

                if resp.status_code != 200:
                    print(f"[{provedor.nome}] Erro ao carregar página de login: {resp.status_code}")
                    return None

                # Extrair o action do form (contém session_code e execution)
                action_match = re.search(r'action="([^"]+)"', resp.text)
                if not action_match:
                    print(f"[{provedor.nome}] Action do form não encontrado. Possível bloqueio de bot?")
                    # print(resp.text[:500])
                    return None
                
                auth_url = action_match.group(1).replace('&amp;', '&')
                
                # 2. Preparar payload com campos obrigatórios
                payload = {
                    "username": username,
                    "password": password,
                    "credentialId": "",
                    "login": "Entrar"
                }
                
                # Extrair hiddens dinâmicos se houver
                for field in ["execution", "session_code", "client_id", "tab_id"]:
                    match = re.search(rf'name="{field}"[^>]+value="([^"]+)"', resp.text)
                    if match:
                        payload[field] = match.group(1)

                # 3. Enviar as credenciais
                headers_login = {
                    "Referer": str(resp.url),
                    "Origin": "https://accounts.fraga.com.br",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": user_agent
                }

                # IMPORTANTE: Desativar redirects aqui para capturar o 302 do sucesso
                resp_post = await client.post(auth_url, data=payload, headers=headers_login, follow_redirects=False)
                print(f"[{provedor.nome}] Resposta POST Login: {resp_post.status_code}")
                
                if resp_post.status_code == 302:
                    location = resp_post.headers.get('Location', '')
                    print(f"[{provedor.nome}] Login OK. Trocando código por Token...")
                    
                    # 4. Extrair o 'code' da URL de redirecionamento
                    code_match = re.search(r'code=([^&]+)', location)
                    if not code_match:
                        print(f"[{provedor.nome}] Código de autorização não encontrado no redirect.")
                        return None
                    
                    auth_code = code_match.group(1)
                    
                    # 5. Trocar o Code pelo Access Token final
                    token_url = "https://accounts.fraga.com.br/realms/cat_authomix/protocol/openid-connect/token"
                    token_payload = {
                        "code": auth_code,
                        "grant_type": "authorization_code",
                        "client_id": "catalog-user",
                        "redirect_uri": "https://catalogo.authomix.com.br"
                    }
                    
                    resp_token = await client.post(token_url, data=token_payload, headers={"User-Agent": user_agent})
                    
                    if resp_token.status_code == 200:
                        token_data = resp_token.json()
                        access_token = token_data.get('access_token')
                        print(f"[{provedor.nome}] Sucesso! Token JWT obtido.")
                        self.cache[provedor.id] = {'token': access_token}
                        return access_token
                    else:
                        print(f"[{provedor.nome}] Erro na troca de token: {resp_token.status_code}")
                        return None
                
                if resp_post.status_code == 200:
                    # Se caiu aqui, provavelmente o login foi recusado (erro na página)
                    if "Invalid username or password" in resp_post.text or "Usuário ou senha inválidos" in resp_post.text:
                        print(f"[{provedor.nome}] Credenciais Inválidas.")
                    else:
                        print(f"[{provedor.nome}] Login retornou 200 inesperado. Verifique logs ou HTML.")
                        alert_match = re.search(r'class="[^"]*alert[^"]*".*?<span>(.*?)</span>', resp_post.text, re.DOTALL)
                        if alert_match:
                            print(f"[{provedor.nome}] Mensagem do Servidor: {alert_match.group(1).strip()}")
                        else:
                            print(f"[{provedor.nome}] Inspecionando início do HTML: {resp_post.text[:300].replace('\n', ' ')}")
                
                return None

            except Exception as e:
                print(f"[{provedor.nome}] Erro inesperado no login: {e}")
                return None

# Instância única para o app
auth_service = AuthService()
