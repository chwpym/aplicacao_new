import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/services/services-3.55.0.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    
    # Find all patterns like "/public/service/..." or "/query/..." or "/login/..." inside quotes
    matches = re.findall(r'"/public/[^"]+"|\'/public/[^\']+\'|"/query/[^"]+"|\'/query/[^\']+\'|"/service/[^"]+"|\'/service/[^\']+\'', content)
    unique_matches = sorted(list(set(matches)))
    print(f"\n--- FOUND {len(unique_matches)} SERVICE PATHS ---")
    for m in unique_matches[:100]:
        print(m)
else:
    print("Failed to fetch.")
