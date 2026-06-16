import httpx
import json
import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://b2b.jahu.com.br",
        "Referer": "https://b2b.jahu.com.br/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }
    
    login_url = "https://b2b.jahu.com.br/server/public/service/auth/loginAcessoPublico"
    search_url = "https://b2b.jahu.com.br/server/public/service/produto/findProdutoList/produtoController/findAllByExampleByPages"
    details_url = "https://b2b.jahu.com.br/server/public/service/query/execute/produtoController/findProdutoByPrimaryKey"
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        # Login
        payload_login = {
            "host": "https://b2b.jahu.com.br",
            "usuario": {"cdSistema": 50, "flAtivo": "S"}
        }
        resp_login = await client.post(login_url, json=payload_login, headers=headers)
        session_id = resp_login.json().get("sessionId")
        print("SessionId:", session_id)
        
        # Search "350047"
        payload_search = {
            "cdEmpresa": "2",
            "cdClienteFilter": "700000",
            "clienteEmpresa": {"vlIndiceCliente": 1},
            "cdGrupoClienteFilter": "201",
            "dsPalavraChave": "350047",
            "opcaoFiltro": "1",
            "pageLines": 16,
            "currentPage": 1,
            "filtros": {},
            "sortColumns": "2-PRODUTO-1",
            "session": {
                "cdSistema": 50,
                "sessionId": session_id,
                "isUsuarioAnomimo": True,
                "usuario": {"cdUsuario": "PUBLICO"}
            },
            "flAtivo": "S"
        }
        
        resp_search = await client.post(search_url, json=payload_search, headers=headers)
        if resp_search.status_code == 200:
            data = resp_search.json()
            collections = data.get("collections", [])
            if collections and collections[0]:
                prod = collections[0][0]
                cd_prod = prod.get("cdProduto")
                cd_dept = prod.get("cdDepartamento", "DEPARTAMENTO")
                cd_cat = prod.get("cdCategoria", "")
                
                # Get Details
                payload_details = {
                    "cdEmpresa": "2",
                    "cdClienteFilter": "700000",
                    "cdGrupoClienteFilter": "201",
                    "cdProduto": cd_prod,
                    "cdDepartamento": cd_dept,
                    "cdCategoria": cd_cat,
                    "sortColumns": "TB.CDCATEGORIA3 DESC, TB.CDCATEGORIA2 DESC, LOCALESTOQUE.NUORDEM, LOCALESTOQUE.DSLOCALESTOQUE",
                    "session": {
                        "cdSistema": 50,
                        "sessionId": session_id,
                        "isUsuarioAnomimo": True,
                        "usuario": {"cdUsuario": "PUBLICO"}
                    },
                    "flAtivo": "S"
                }
                
                resp_det = await client.post(details_url, json=payload_details, headers=headers)
                det_data = resp_det.json()
                print("--- PRODUTO 350047 ---")
                print("dsProduto:", det_data.get("dsProduto"))
                print("flFoto:", det_data.get("flFoto"))
                print("camposDinamicos:")
                for k, v in det_data.get("camposDinamicos", {}).items():
                    if k != "AD_DSAPLICACAO":
                        print(f"  {k}: {v}")
            else:
                print("Produto 350047 não encontrado")

if __name__ == "__main__":
    asyncio.run(main())
