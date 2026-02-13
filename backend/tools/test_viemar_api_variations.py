import httpx
import asyncio
import json


async def test_viemar_variation(payload, description):
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "origin": "https://catalogo.viemar.com.br",
        "referer": "https://catalogo.viemar.com.br/",
    }

    async with httpx.AsyncClient() as client:
        print(f"\n--- Testing: {description} ---")
        print(f"Payload: {payload}")
        try:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Response structure keys: {list(data.keys())}")
                if "catalog" in data:
                    print(f"Items in catalog: {len(data['catalog'])}")
                    # print(json.dumps(data, indent=2)[:1000])
                return True
            else:
                print(f"Error Response: {response.text}")
                return False
        except Exception as e:
            print(f"Exception: {e}")
            return False


async def main():
    variations = [
        ({"searchCode": "503206", "cardMode": True}, "searchCode + cardMode=True"),
        ({"searchCode": "503206", "cardMode": False}, "searchCode + cardMode=False"),
        ({"searchCode": "503206", "cardMode": "true"}, "searchCode + cardMode='true'"),
        (
            {"obj": {"searchCode": "503206", "cardMode": True}},
            "Nested obj with searchCode + cardMode",
        ),
        (
            {"searchCode": "503206", "cardMode": True, "category": None},
            "Added category=None",
        ),
    ]

    for payload, desc in variations:
        await test_viemar_variation(payload, desc)


if __name__ == "__main__":
    asyncio.run(main())
