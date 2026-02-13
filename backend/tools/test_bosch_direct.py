import asyncio
import httpx
from app.providers.bosch_provider import BoschProvider


async def test_bosch_direct():
    config = {"id": 999, "nome": "BOSCH", "tipo": "bosch"}
    provider = BoschProvider(config)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Testando acesso direto via clean ID
        prod_num = "0986BB0096"
        print(f"Testando acesso direto ao produto {prod_num}...")

        det_url = f"{provider.api_base}/product-details/{prod_num}"
        resp = await client.get(det_url, headers=provider.headers)

        if resp.status_code == 200:
            print("Sucesso! Acesso direto funciona.")
            print(f"JSON: {resp.text[:200]}...")

            # Agora testa buscar aplicações
            print("Buscando makers...")
            mak_url = f"{provider.api_base}/usage-in-vehicles/{prod_num}/makers"
            m_resp = await client.get(mak_url, headers=provider.headers)
            print(f"Makers status: {m_resp.status_code}")
            print(f"Makers JSON: {m_resp.text[:200]}...")
        else:
            print(f"Falha no acesso direto. Status: {resp.status_code}")
            print(f"Body: {resp.text[:200]}")


if __name__ == "__main__":
    asyncio.run(test_bosch_direct())
