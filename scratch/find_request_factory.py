import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/components/safira/js/safira-3.1.76.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
if res.status_code == 200:
    content = res.text
    pos = content.find('wmw.factory("requestFactory"')
    if pos != -1:
        print(f"Found wmw.factory('requestFactory') at index {pos}")
        print(content[pos:pos+3000])
    else:
        # Search for .factory("requestFactory" or similar
        pos = content.lower().find('requestfactory')
        if pos != -1:
            print(f"Found requestFactory in lower case at index {pos}")
            # Print around it
            print(content[max(0, pos-100):min(len(content), pos+1500)])
        else:
            print("Not found.")
else:
    print("Failed to fetch.")
