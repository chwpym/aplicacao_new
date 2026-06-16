import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/wmw-3.55.0.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    print(f"wmw.js length: {len(content)}")
    
    # Let's search for redirect, location.href, location.replace, decodeRouteParam, etc.
    patterns = [r'location\.', r'redirect', r'decodeRouteParam', r'params\.params', r'changeSession']
    for pat in patterns:
        matches = [m.start() for m in re.finditer(pat, content, re.IGNORECASE)]
        print(f"Pattern '{pat}': found {len(matches)} occurrences.")
        for idx, pos in enumerate(matches[:5]):
            start = max(0, pos - 100)
            end = min(len(content), pos + 100)
            print(f"  Occur {idx+1} at index {pos}:")
            print(content[start:end])
            print("-" * 30)
else:
    print("Failed to fetch.")
