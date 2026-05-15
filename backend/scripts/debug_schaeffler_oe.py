import asyncio
import json
import httpx
from app.providers.schaeffler_provider import SchaefflerProvider

async def debug_oe():
    config = {
        "id": 999,
        "nome": "LUK",
        "tipo": "schaeffler",
        "url": "https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/catalog"
    }
    provider = SchaefflerProvider(config)
    codigo = "619301500"
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Tenta buscar os produtos primeiro
        products = await provider._discover_products(client, codigo)
        if not products:
            print("Produto não encontrado no _discover_products.")
            return
        
        product = products[0]
        product_code = product.get("code")
        print(f"Product Code: {product_code}")
        
        # Vamos olhar as chaves completas
        print("\nKeys in Product:", list(product.keys()))
        print("\nProduct References in Search:", json.dumps(product.get("productReferences"), indent=2))
        
        print("\nTest FULL DETAIL:")
        url_full = f"{provider.api_base}/products/{product_code}?fields=FULL"
        r_full = await client.get(url_full, params=provider.common_params, headers=provider.headers)
        if r_full.status_code == 200:
            with open("dump_product.json", "w", encoding="utf-8") as f:
                json.dump(r_full.json(), f, indent=2, ensure_ascii=False)
            print("Dump salvo em dump_product.json")

if __name__ == "__main__":
    asyncio.run(debug_oe())
