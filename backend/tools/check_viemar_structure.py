import httpx
import asyncio
import json


async def check_structure():
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "origin": "https://catalogo.viemar.com.br",
        "referer": "https://catalogo.viemar.com.br/",
    }
    payload = {"searchCode": "503206", "cardMode": True}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if "catalog" in data and len(data["catalog"]) > 0:
                print(json.dumps(data["catalog"][0], indent=2))
            else:
                print("No data found")
        else:
            print(f"Error: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(check_structure())
