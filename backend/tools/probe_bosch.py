import asyncio
import httpx
from app.providers.bosch_provider import BoschProvider


async def probe_bosch():
    provider = BoschProvider({"id": 999, "nome": "BOSCH", "tipo": "bosch"})
    prod_num = "0986BB0096"
    endpoints = [
        "product-details",
        "product",
        "products",
        "details",
        "article",
        "articles",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for ep in endpoints:
            url = f"{provider.api_base}/{ep}/{prod_num}"
            print(f"Tentando {url}...")
            try:
                resp = await client.get(url, headers=provider.headers)
                if resp.status_code == 200 and "{" in resp.text:
                    print(f"!!! POSSÍVEL SUCESSO EM {ep} !!!")
                    print(f"JSON: {resp.text[:100]}")
                else:
                    print(f"Falha {ep}: {resp.status_code}")
            except Exception as e:
                print(f"Erro {ep}: {e}")


if __name__ == "__main__":
    asyncio.run(probe_bosch())
