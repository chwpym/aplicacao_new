import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    "https://b2b.jahu.com.br/js/wmwRun-3.55.0.js",
    "https://b2b.jahu.com.br/js/wmwRun.js",
    "https://b2b.jahu.com.br/js/wmw-3.55.0.js"
]

for url in urls:
    print(f"\n==========================================")
    print(f"FETCHING AND SEARCHING: {url}")
    print(f"==========================================")
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print("Status:", res.status_code)
        if res.status_code == 200:
            content = res.text
            print(f"Length of file: {len(content)}")
            
            # Find references to sessionId or session.sessionId
            matches = [m.start() for m in re.finditer(r'sessionId', content, re.IGNORECASE)]
            print(f"Found {len(matches)} occurrences of 'sessionId'.")
            for idx, pos in enumerate(matches[:5]):
                start = max(0, pos - 100)
                end = min(len(content), pos + 100)
                print(f"Occurrence {idx+1} at index {pos}:")
                print(content[start:end])
                print("-" * 50)
        else:
            print("Failed.")
    except Exception as e:
        print("Error:", e)
