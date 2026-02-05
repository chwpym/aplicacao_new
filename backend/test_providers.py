import asyncio
import httpx
from app.providers.graphql_provider import GraphQLProvider
from app.providers.ds_provider import DSProvider
from app.providers.rest_provider import RESTProvider

async def test_graphql():
    print("\n--- Testando GraphQL (Discovery + Multi-market) ---")
    config = {
        "nome": "Sabo",
        "url": "https://bff.catalogofraga.com.br/gateway/graphql",
        "tipo": "graphql",
        "headers": {
            "origin": "https://catalogo.sabo.com.br",
            "referer": "https://catalogo.sabo.com.br/"
        },
        "query": "query GetProductById($id: String!, $market: MarketType!) {\n  product(id: $id, market: $market) {\n    partNumber\n    vehicles {\n      brand\n      name\n      model\n      engineName\n      engineConfiguration\n      startYear\n      endYear\n    }\n  }\n}"
    }
    provider = GraphQLProvider(config)
    results = await provider.buscar("02525BRAGF")
    print(f"Resultados Sabo: {len(results)}")
    if results:
        print(f"Primeiro resultado: {results[0]['veiculo']} {results[0]['modelo']}")

async def test_ds():
    print("\n--- Testando DS (Multi-category Scraping) ---")
    config = {
        "nome": "DS",
        "url": "https://www.ds.ind.br/pt/produtos/regulador-de-pressao/{id}",
        "tipo": "ds"
    }
    provider = DSProvider(config)
    results = await provider.buscar("1102")
    print(f"Resultados DS (1102): {len(results)}")

async def main():
    await test_graphql()
    # await test_ds() # Scraping pode demorar e falhar se o site mudar

if __name__ == "__main__":
    asyncio.run(main())
