import httpx
import json
import asyncio


async def detailed_id_analysis():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        # Usando o productId de C2182
        payload = {
            "skip": 0,
            "take": 10,
            "related": True,
            "productId": "e6317b79-4195-92314cc6-2fb6-8ab203dc-11ec",
        }

        try:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                data = r.json()
                # No curl do usuário, o retorno parece ser uma lista de 'vehicles' ou similar
                print("\n--- RESPOSTA DETALHADA POR ID ---")
                print(
                    json.dumps(data, indent=2)[:5000]
                )  # Ver primeiros 5000 caracteres
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(detailed_id_analysis())
