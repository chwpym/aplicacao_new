import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/components/safira/js/safira-3.1.76.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
if res.status_code == 200:
    content = res.text
    pos = content.find('wmw.factory("authService"')
    if pos != -1:
        # Let's extract 15000 characters from pos
        snippet = content[pos:pos+15000]
        # Let's find where the factory ends or search for returned service object
        # In angular factory, it usually returns {...} at the end.
        # Let's write it to a local scratch file so we can view it fully.
        with open("scratch/authService_extracted.js", "w", encoding="utf-8") as f:
            f.write(snippet)
        print("Successfully extracted authService snippet to scratch/authService_extracted.js")
    else:
        print("Not found.")
else:
    print("Failed to fetch.")
