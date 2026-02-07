import httpx
import json
import asyncio


async def test_bd8930():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        # Pesquisando BD8930 (Fremax) - O código exato do print do usuário
        try:
            r = await client.post(
                url, headers=headers, json={"query": "BD8930", "take": 5}
            )
            if r.status_code == 200:
                data = r.json().get("data", [])
                for prod in data:
                    print(
                        f"\nPRODUTO: {prod.get('partNumber')} - {prod.get('applicationDescription')}"
                    )
                    v = prod.get("vehicles", [])
                    if v:
                        print(f"Campos no veículo: {list(v[0].keys())}")
                        print(f"Exemplos de Veículo: {json.dumps(v[:2], indent=2)}")

                    # Procura por CROSS REFERENCES
                    print(
                        f"Cross References Keys: {[k for k in prod.keys() if 'cross' in k.lower() or 'ref' in k.lower()]}"
                    )
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_bd8930())
