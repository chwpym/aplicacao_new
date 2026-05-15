import asyncio
import json
import httpx

async def find_contains():
    api_base = "https://vehiclelifetimesolutions.schaeffler.com.br/api/AAM-BR"
    product_code = "TA-479-6193015000"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://vehiclelifetimesolutions.schaeffler.com.br/pt-br/catalog/auto-parts/clutch-attachment-parts/clutch-kit/clutch-kit-luk-repset/p-TA-479-6193015000",
    }
    params = {"lang": "pt_BR", "curr": "BRL", "catalogCountry": "BR"}

    endpoints = [
        f"/products/{product_code}/contains",
        f"/products/{product_code}/components",
        f"/products/{product_code}/parts",
        f"/products/{product_code}/subProducts",
        f"/products/{product_code}/sub-products",
        f"/products/{product_code}/kitContents",
        f"/products/{product_code}/kit-contents",
        f"/products/{product_code}/bundleEntries",
        f"/products/{product_code}/entries",
        f"/products/{product_code}/variants",
    ]

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for ep in endpoints:
            url = f"{api_base}{ep}"
            r = await client.get(url, params=params, headers=headers)
            status = r.status_code
            marker = " <-- FOUND!" if status == 200 else ""
            print(f"{ep} -> {status}{marker}")
            if status == 200:
                print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:1500])

asyncio.run(find_contains())
