import requests

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
}

url = "https://b2b.jahu.com.br/"
session = requests.Session()

print(f"Requesting {url}...")
try:
    res = session.get(url, headers=headers, timeout=15)
    print("Status:", res.status_code)
    print("Response headers:")
    for k, v in res.headers.items():
        print(f"  {k}: {v}")
    print("\nCookies in session:")
    print(session.cookies.get_dict())
    print("\nFirst 1000 characters of HTML:")
    print(res.text[:1000])
except Exception as e:
    print("Error:", e)
