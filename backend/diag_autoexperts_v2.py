import httpx
import json
import asyncio
import re


async def test_autoexperts():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-region": "br",
        "origin": "https://www.autoexperts.parts",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Tentativa 6: GET no site para ver se tem links de API no source
        print("\n--- Tentando ler HTML do site ---")
        try:
            r0 = await client.get(
                "https://www.autoexperts.parts/pt/br/search?q=C2182", headers=headers
            )
            print(f"Status HTML: {r0.status_code}")
            # Procura por URLs de API ou JSON de estado inicial
            urls = re.findall(r'https://api\.autoexperts\.parts/[^\s"\'}]+', r0.text)
            for u in set(urls):
                print(f"URL encontrada no HTML: {u}")
        except Exception as e:
            print(f"Erro HTML: {e}")

        # Tentativa 7: POST /products com query (Pode ser o mesmo endpoint mas com campos diferentes)
        print("\n--- Tentando POST products com SEARCH ---")
        url7 = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        payloads = [
            {"query": "C2182", "skip": 0, "take": 10},
            {"search": "C2182", "skip": 0, "take": 10},
            {"partNumber": "C2182", "skip": 0, "take": 10},
        ]
        for p in payloads:
            try:
                r = await client.post(url7, headers=headers, json=p)
                print(f"Status {p}: {r.status_code}")
                if r.status_code == 200:
                    print(json.dumps(r.json(), indent=2)[:500])
            except Exception:
                pass

        # Tentativa 8: Endpoints comuns em Fras-le/Mobility
        print("\n--- Tentando Endpoints Comuns ---")
        paths = [
            "/autexp/bff/v1/catalog/search/query",
            "/autexp/bff/v1/catalog/products/search",
        ]
        for path in paths:
            u = f"https://api.autoexperts.parts{path}"
            try:
                r = await client.post(u, headers=headers, json={"query": "C2182"})
                print(f"Status {path}: {r.status_code}")
                if r.status_code == 200:
                    print(json.dumps(r.json(), indent=2)[:500])
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(test_autoexperts())
