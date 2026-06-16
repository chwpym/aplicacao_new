import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/wmw-3.55.0.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    print(f"Length of wmw.js: {len(content)}")
    
    # Search for authService or wmw.factory or wmw.service
    matches = [m.start() for m in re.finditer(r'authService|sessionService|requestFactory', content)]
    print(f"Found {len(matches)} matches.")
    for idx, pos in enumerate(matches[:10]):
        start = max(0, pos - 150)
        end = min(len(content), pos + 150)
        print(f"Match {idx+1} at pos {pos}:")
        print(content[start:end])
        print("-" * 50)
else:
    print("Failed to fetch.")
