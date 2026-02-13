import httpx
import asyncio
import json


async def test_cofap_search():
    codes = ["22036", "22010"]
    params = {"provedores": "38"}  # ID 38 restored

    async with httpx.AsyncClient(timeout=30.0) as client:
        for code in codes:
            url = f"http://localhost:8000/search/{code}"
            print(f"\n--- Testing search: {code} ---")
            try:
                response = await client.get(url, params=params)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    results = response.json()
                    print(f"Results found: {len(results)}")
                    if results:
                        for i, res in enumerate(results[:5]):
                            print(
                                f"\n[Result {i+1}] {res.get('marca')} - {res.get('veiculo')}"
                            )
                            print(f"  Modelo: {res.get('modelo')}")
                            print(
                                f"  Anos: {res.get('ano_inicio')} / {res.get('ano_fim')}"
                            )
                            print(f"  Referências: {res.get('referencias')}")
                            print(f"  Observação: {res.get('observacao')}")
                            print(f"  Imagem Principal: {res.get('imagem')}")
                    else:
                        print(f"No results found for {code}.")
                else:
                    print(f"Error ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"Error connecting to backend for {code}: {e}")


if __name__ == "__main__":
    asyncio.run(test_cofap_search())
