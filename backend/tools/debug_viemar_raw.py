import httpx
import asyncio
import json


async def test_viemar_raw():
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }
    payload = {"searchCode": "680402", "cardMode": True}

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"Buscando 680402 na Viemar...")
        response = await client.post(url, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Resposta JSON recebida.")

            for catalog in data.get("catalog", []):
                # Simular o novo parser de imagem
                image_data = catalog.get("image")
                primary_image = ""
                all_images = []

                if isinstance(image_data, list) and image_data:
                    primary_image = image_data[0].get("value") or ""
                    all_images = [
                        img.get("value") for img in image_data if img.get("value")
                    ]
                elif isinstance(image_data, dict):
                    primary_image = image_data.get("value") or ""
                    if primary_image:
                        all_images = [primary_image]

                print(f"\nItem: {catalog.get('model', {}).get('value')}")
                print(f"  Imagem Principal: {primary_image}")
                print(f"  Total Imagens: {len(all_images)}")
        else:
            print(f"Erro: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_viemar_raw())
