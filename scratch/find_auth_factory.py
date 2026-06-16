import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://b2b.jahu.com.br/js/services/services-3.55.0.min.js"
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
if res.status_code == 200:
    content = res.text
    
    # Search for .factory("authService" or .service("authService" or .provider("authService"
    for name in ["authService", "sessionService", "requestFactory", "session"]:
        print(f"\n==========================================")
        print(f"SEARCHING FOR REGISTERED: {name}")
        print(f"==========================================")
        pattern = r'\.(factory|service|provider)\(\s*["\']' + name + r'["\']'
        match = re.search(pattern, content)
        if match:
            start = match.start()
            print(content[start:start+3000])
        else:
            # Let's search just for the name in quotes, e.g. "authService"
            match_simple = re.search(r'["\']' + name + r'["\']\s*,\s*\[', content)
            if match_simple:
                start = match_simple.start()
                print(content[start-50:start+3000])
            else:
                print(f"Not found.")
else:
    print("Failed to fetch.")
