import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://b2b.jahu.com.br',
    'Referer': 'https://b2b.jahu.com.br/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
}

url = "https://b2b.jahu.com.br/server/public/service/produto/findProdutoList/produtoController/findAllByExampleByPages"

payload = {
    "cdEmpresa": "2",
    "cdClienteFilter": "700000",
    "clienteEmpresa": {"vlIndiceCliente": 1},
    "cdGrupoClienteFilter": "201",
    "dsPalavraChave": "153549",
    "opcaoFiltro": "1",
    "pageLines": 1,
    "currentPage": 1,
    "filtros": {},
    "sortColumns": "2-PRODUTO-1",
    "session": {
        "cdSistema": 50,
        "isUsuarioAnomimo": True,
        "usuario": {"cdUsuario": "PUBLICO"}
    },
    "flAtivo": "S"
}

print("Querying search endpoint...")
res = requests.post(url, json=payload, headers=headers, timeout=10)
print("Status:", res.status_code)
if res.status_code == 200:
    data = res.json()
    print("Response keys:", list(data.keys()))
    # Let's check if there is any 'session' or 'sessionId' key at the root of the response
    for k, v in data.items():
        if k != 'collections':
            print(f"Key '{k}': {v}")
    
    # Let's inspect the first collection
    collections = data.get("collections", [])
    if collections and collections[0]:
        prod = collections[0][0]
        print("\nFirst product keys:", list(prod.keys()))
        # Check if product contains any session info
        if 'session' in prod:
            print("Product has session field:", prod['session'])
else:
    print(res.text)
