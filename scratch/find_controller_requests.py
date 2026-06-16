import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/controllers/controllers-3.55.0.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    print(f"Fetched controllers, length {len(content)}")
    
    matches = [m.start() for m in re.finditer(r'\.request\(', content)]
    print(f"Found {len(matches)} occurrences of '.request('.")
    
    endpoints = set()
    for pos in matches:
        snippet = content[pos:pos+150]
        strs = re.findall(r'["\']([^"\']+)["\']', snippet)
        if strs:
            endpoints.add(strs[0])
            
    print("\n--- UNIQUE ENDPOINTS IN CONTROLLER .request() ---")
    for ep in sorted(list(endpoints)):
        print(ep)
else:
    print("Failed to fetch.")
