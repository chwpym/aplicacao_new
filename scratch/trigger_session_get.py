import requests

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
}

urls = [
    "https://b2b.jahu.com.br/server",
    "https://b2b.jahu.com.br/server/",
    "https://b2b.jahu.com.br/server/public",
    "https://b2b.jahu.com.br/server/public/"
]

for url in urls:
    print(f"Requesting GET {url}...")
    try:
        res = session.get(url, headers=headers, timeout=10)
        print("Status:", res.status_code)
        print("Cookies:", session.cookies.get_dict())
        print("Set-Cookie header:", res.headers.get('Set-Cookie'))
        print("-" * 40)
    except Exception as e:
        print("Error:", e)
