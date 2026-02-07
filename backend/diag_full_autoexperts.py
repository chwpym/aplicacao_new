import httpx
import json
import asyncio


async def detailed_analysis():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        # Pesquisando C2182 (Controil)
        try:
            r = await client.post(
                url, headers=headers, json={"query": "C2182", "take": 1}
            )
            if r.status_code == 200:
                data = r.json()
                product = data.get("data", [{}])[0]

                print("\n--- ANÁLISE DE CAMPOS ---")
                print(f"Campos no Produto: {list(product.keys())}")

                # Verifica Imagens
                images = product.get("images", [])
                print(f"Imagens encontradas: {len(images)}")

                # Verifica Referências OE
                # Às vezes está em 'relatedProducts' ou 'crossReferences'
                # Mas no BFF pode ser diferente.
                print(
                    f"Referências Cruzadas: {product.get('crossReferences', 'Não encontrado na raiz')}"
                )

                # Verifica veículos e Detalhes de Motor
                vehicles = product.get("vehicles", [])
                if vehicles:
                    print(f"Primeiro Veículo: {json.dumps(vehicles[0], indent=2)}")

                # Verifica Atributos técnicos
                specs = product.get("specifications", [])
                print(f"Especificações Técnicas: {len(specs)}")

                print("\n--- JSON COMPLETO (PRIMEIRO PRODUTO) ---")
                print(json.dumps(product, indent=2))
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(detailed_analysis())
