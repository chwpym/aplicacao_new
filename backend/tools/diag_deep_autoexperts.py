import httpx
import json
import asyncio


async def test_deep_endpoints():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    prod_id = "e6317b79-4195-92314cc6-2fb6-8ab203dc-11ec"  # C2182

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Teste 1: GET /products/{id}
        print(f"\n--- Testando GET /products/{prod_id} ---")
        try:
            r1 = await client.get(
                f"https://api.autoexperts.parts/autexp/bff/v1/catalog/products/{prod_id}",
                headers=headers,
            )
            print(f"Status: {r1.status_code}")
            if r1.status_code == 200:
                print(json.dumps(r1.json(), indent=2)[:2000])
        except Exception as e:
            print(f"Erro: {e}")

        # Teste 2: GET /products/{id}/applications (Chute comum)
        print(f"\n--- Testando GET /products/{prod_id}/applications ---")
        try:
            r2 = await client.get(
                f"https://api.autoexperts.parts/autexp/bff/v1/catalog/products/{prod_id}/applications",
                headers=headers,
            )
            print(f"Status: {r2.status_code}")
            if r2.status_code == 200:
                print(json.dumps(r2.json(), indent=2)[:2000])
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_deep_endpoints())
