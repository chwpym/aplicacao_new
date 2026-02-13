import httpx
import asyncio


async def probe_urls():
    code = "680402"
    bases = [
        "https://catalogo.viemar.com.br/images/product/",
        "https://catalogo.viemar.com.br/images/products/",
        "https://catalogo.viemar.com.br/catalog/image/",
        "https://www.viemar.com.br/images/",
        "https://viemar.com.br/images/",
        "https://catalog.viemar.com.br/images/",
        "https://www.viemar.com.br/arquivos/produtos/",
        "https://viemar.com.br/arquivos/produtos/",
        "https://backend.viemar.com.br/uploads/",
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for base in bases:
            url = f"{base}{code}.jpg"
            try:
                print(f"Testing: {url}")
                resp = await client.get(url, follow_redirects=True)
                ct = resp.headers.get("content-type", "")
                print(f"  Status: {resp.status_code}, CT: {ct}")
                if resp.status_code == 200 and "image" in ct:
                    print(f"  FOUND! {url}")
                    # return url
            except Exception as e:
                print(f"  Error: {e}")
    return None


if __name__ == "__main__":
    asyncio.run(probe_urls())
