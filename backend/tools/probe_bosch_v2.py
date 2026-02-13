import asyncio
import httpx
from app.providers.bosch_provider import BoschProvider


async def probe_bosch_v2():
    provider = BoschProvider({"id": 999, "nome": "BOSCH", "tipo": "bosch"})
    prod_num = "0986BB0096"
    endpoints = [
        "product-details",
        "product-technical-data",
        "product-specifications",
        "product-info",
        "search",
        "product-search",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for ep in endpoints:
            url = f"{provider.api_base}/{ep}/{prod_num}"
            if ep == "search" or ep == "product-search":
                url = f"{provider.api_base}/{ep}?query={prod_num}"

            print(f"Tentando {url}...")
            try:
                resp = await client.get(url, headers=provider.headers)
                ctype = resp.headers.get("Content-Type", "")
                if resp.status_code == 200 and "application/json" in ctype:
                    print(f"!!! SUCESSO EM {ep} !!!")
                    print(f"JSON: {resp.text[:200]}")
                else:
                    print(f"Falha {ep}: {resp.status_code} ({ctype})")
                    if "text/html" not in ctype:
                        print(f"Body: {resp.text[:100]}")
            except Exception as e:
                print(f"Erro {ep}: {e}")


if __name__ == "__main__":
    asyncio.run(probe_bosch_v2())
