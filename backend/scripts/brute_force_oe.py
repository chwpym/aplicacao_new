import asyncio
import httpx

async def brute_force_oe():
    api_base = "https://vehiclelifetimesolutions.schaeffler.com.br/api/AAM-BR"
    product_code = "TA-479-6193015000"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*"
    }
    params = {"lang": "pt_BR", "curr": "BRL", "catalogCountry": "BR"}

    endpoints = [
        f"/products/{product_code}/oereferences",
        f"/products/{product_code}/productReferences",
        f"/products/{product_code}/linkages/oeNumbers",
        f"/products/{product_code}/cross-references",
        f"/products/{product_code}/crossReferences",
        f"/products/{product_code}/linkages/manufacturers/TA-35/oeNumbers",
        f"/products/{product_code}/linkages/manufacturers/TA-35/productReferences"
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for ep in endpoints:
            url = f"{api_base}{ep}"
            r = await client.get(url, params=params, headers=headers)
            print(f"GET {ep} -> {r.status_code}")
            if r.status_code == 200:
                print(r.text[:200])

asyncio.run(brute_force_oe())
