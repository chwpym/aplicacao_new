import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/services/services-3.55.0.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    print(f"Fetched services, length {len(content)}")
    
    # Search for all strings matching $http
    matches = [m.start() for m in re.finditer(r'\$http', content)]
    print(f"Found {len(matches)} occurrences of '$http'.")
    
    snippets = []
    for pos in matches[:20]:
        snippet = content[max(0, pos-50):min(len(content), pos+150)]
        print(snippet)
        print("-" * 50)
else:
    print("Failed to fetch.")
