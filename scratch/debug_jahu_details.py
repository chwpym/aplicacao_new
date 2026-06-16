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
        # 1. Login
        payload_login = {
            "host": "https://b2b.jahu.com.br",
            "usuario": {
                "cdSistema": 50,
                "flAtivo": "S"
            }
        }
        resp_login = await client.post(login_url, json=payload_login, headers=headers)
        if resp_login.status_code != 200:
            print("Login failed:", resp_login.status_code)
            return
            
        login_data = resp_login.json()
        session_id = login_data.get("sessionId")
        print("SessionId:", session_id)
        
        # 2. Search "153549"
        payload_search = {
            "cdEmpresa": "2",
            "cdClienteFilter": "700000",
            "clienteEmpresa": {"vlIndiceCliente": 1},
            "cdGrupoClienteFilter": "201",
            "dsPalavraChave": "153549",
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
        if resp_search.status_code != 200:
            print("Search failed:", resp_search.status_code)
            return
            
        search_data = resp_search.json()
        collections = search_data.get("collections", [])
        if not collections or not collections[0]:
            print("No products found in search")
            return
            
        prod = collections[0][0]
        cd_prod = prod.get("cdProduto")
        cd_dept = prod.get("cdDepartamento", "DEPARTAMENTO")
        cd_cat = prod.get("cdCategoria", "")
        print(f"Product found: {cd_prod} - {prod.get('dsProduto')}")
        print("Product fields:", list(prod.keys()))
        print("Product raw json:\n", json.dumps(prod, indent=2, ensure_ascii=False))
        
        # 3. Details (PrimaryKey)
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
        if resp_det.status_code != 200:
            print("Details failed:", resp_det.status_code)
            return
            
        det_data = resp_det.json()
        
        # Salva o json de detalhes em um arquivo no scratch para inspecionar
        with open("scratch/product_details_153549.json", "w", encoding="utf-8") as f:
            json.dump(det_data, f, indent=2, ensure_ascii=False)
            
        print("Details saved to scratch/product_details_153549.json")
        print("Details response top-level keys:", list(det_data.keys()))
        
        # Vamos listar camposDinamicos e outras chaves interessantes
        if "camposDinamicos" in det_data:
            print("camposDinamicos keys:", list(det_data["camposDinamicos"].keys()))
            # Print values for some fields except heavy HTML
            for k, v in det_data["camposDinamicos"].items():
                if k != "AD_DSAPLICACAO":
                    print(f"  {k}: {v}")
                    
        # Tem "referenciaProdutoList"?
        if "referenciaProdutoList" in det_data:
            print("referenciaProdutoList (len):", len(det_data["referenciaProdutoList"]))
            for ref in det_data["referenciaProdutoList"][:5]:
                print("  Ref:", ref)

if __name__ == "__main__":
    asyncio.run(main())
