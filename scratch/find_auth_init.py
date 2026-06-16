import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/services/services-3.55.0.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    print(f"Fetched services, length {len(content)}")
    
    # Search for all strings matching "/public/service/" or similar, but with different regex
    # In minified code, it might be: o.request("query/execute/...
    # Or requestFactory.request("
    # Let's search for "request(" or ".request("
    matches = [m.start() for m in re.finditer(r'\.request\(', content)]
    print(f"Found {len(matches)} occurrences of '.request('.")
    
    endpoints = set()
    for pos in matches:
        # Grab the text after .request(
        snippet = content[pos:pos+150]
        # Find string literals inside this snippet
        strs = re.findall(r'["\']([^"\']+)["\']', snippet)
        if strs:
            endpoints.add(strs[0])
            
    print("\n--- UNIQUE ENDPOINTS IN .request() ---")
    for ep in sorted(list(endpoints)):
        print(ep)
else:
    print("Failed to fetch.")
