import httpx
import asyncio
import json


async def test_viemar():
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "origin": "https://catalogo.viemar.com.br",
        "referer": "https://catalogo.viemar.com.br/",
    }
    payload = {"code": "503206"}

    async with httpx.AsyncClient() as client:
        print(f"Testing Viemar with payload: {payload}")
        try:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Headers: {response.headers}")
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Raw Response: {response.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_viemar())
