import httpx
import json


def test_viemar_direct():
    url = "https://catalogo.viemar.com.br/catalog/search/catalog/code"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }
    payload = {"searchCode": "680185", "cardMode": True}

    print(f"Testing Viemar with code 680185...")
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # Mostra a estrutura do primeiro item do catálogo
            if data.get("catalog"):
                first = data["catalog"][0]
                print(f"\nKeys in catalog[0]: {list(first.keys())}")

                for key in ["brand", "model", "year", "productLine", "application"]:
                    val = first.get(key)
                    print(f"- {key}: {type(val)} -> {val}")
            else:
                print("No data in 'catalog'")
        else:
            print(f"Error Body: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    test_viemar_direct()
