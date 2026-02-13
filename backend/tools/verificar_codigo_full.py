import httpx
import asyncio
import json


async def test_code():
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "origin": "https://catalogo.viemar.com.br",
        "referer": "https://catalogo.viemar.com.br/",
    }
    payload = {"searchCode": "680185", "cardMode": True}

    async with httpx.AsyncClient() as client:
        print(f"Testing code 680185 at {url}")
        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"Error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_code())
