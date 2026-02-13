import httpx
import json
import asyncio


async def test_all_keys():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-region": "br",
    }

    prod_id = "0108b62b-f139-92314cc6-2fb6-87077f6a-c82e"  # BD8930

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n--- Analisando Chaves de /products/{prod_id} ---")
        try:
            r = await client.get(
                f"https://api.autoexperts.parts/autexp/bff/v1/catalog/products/{prod_id}",
                headers=headers,
            )
            if r.status_code == 200:
                data = r.json()
                print(f"Todas as chaves: {list(data.keys())}")

                # Procura por referências cruzadas em campos comuns
                for k, v in data.items():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        print(
                            f"Campo de lista '{k}' (exemplo): {json.dumps(v[0], indent=2)[:500]}"
                        )
                    elif isinstance(v, dict):
                        print(f"Campo de dict '{k}' (keys): {list(v.keys())}")
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_all_keys())
