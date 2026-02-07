import httpx
import json
import asyncio


async def test_autoexperts():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Tentativa 4: POST /catalog/search (Frequentemente usado em BFFs)
        print("\n--- Tentando POST search ---")
        url4 = "https://api.autoexperts.parts/autexp/bff/v1/catalog/search"
        try:
            r4 = await client.post(
                url4, headers=headers, json={"query": "C2182", "skip": 0, "take": 10}
            )
            print(f"Status: {r4.status_code}")
            if r4.status_code == 200:
                print(json.dumps(r4.json(), indent=2)[:2000])
        except Exception as e:
            print(f"Erro: {e}")

        # Tentativa 5: GET /catalog/search (Com query param)
        print("\n--- Tentando GET search ---")
        url5 = f"https://api.autoexperts.parts/autexp/bff/v1/catalog/search?q=C2182"
        try:
            r5 = await client.get(url5, headers=headers)
            print(f"Status: {r5.status_code}")
            if r5.status_code == 200:
                print(json.dumps(r5.json(), indent=2)[:2000])
        except Exception as e:
            print(f"Erro: {e}")

        # Tentativa 3 corrigida: POST products (Applications)
        print("\n--- Tentando POST products (Applications) ---")
        url3 = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        payload3 = {
            "skip": 0,
            "take": 10,
            "related": True,
            "productId": "e6317b79-4195-92314cc6-2fb6-8ab203dc-11ec",
        }
        try:
            r3 = await client.post(url3, headers=headers, json=payload3)
            print(f"Status: {r3.status_code}")
            if r3.status_code == 200:
                data = r3.json()
                print(json.dumps(data, indent=2)[:3000])
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_autoexperts())
