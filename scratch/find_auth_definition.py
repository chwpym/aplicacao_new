import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

js_files = [
    "custom/js/cielo-silent-order-post.prod.js",
    "custom/js/custom.js",
    "components/safira/js/components-3.1.76.min.js",
    "js/wmw-3.55.0.js",
    "components/safira/js/safira-3.1.76.min.js",
    "js/format/format-3.55.0.min.js",
    "js/controllers/controllers-3.55.0.min.js",
    "js/services/services-3.55.0.min.js",
    "js/directives/directives-3.55.0.min.js",
    "js/filters/filters-3.55.0.min.js",
    "js/utils/utils-3.55.0.min.js",
    "js/constants/constants-3.55.0.min.js",
    "js/config/wmwconfig-3.55.0.js",
    "custom/config/up.config-3.55.0.js",
    "js/wmwRun-3.55.0.js",
]

for path in js_files:
    url = f"https://b2b.jahu.com.br/{path}"
    print(f"\n==========================================")
    print(f"FETCHING AND SEARCHING: {url}")
    print(f"==========================================")
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        print("Status:", res.status_code)
        if res.status_code == 200:
            content = res.text
            print(f"Length: {len(content)}")
            
            # Find definitions of authService like factory("authService" or similar
            matches = [m.start() for m in re.finditer(r'["\']authService["\']', content)]
            if matches:
                print(f"Found {len(matches)} occurrences of 'authService' in quotes.")
                for idx, pos in enumerate(matches):
                    start = max(0, pos - 100)
                    end = min(len(content), pos + 300)
                    print(f"Occurrence {idx+1} at index {pos}:")
                    print(content[start:end])
                    print("-" * 50)
            else:
                print("No authService found.")
        else:
            print("Failed to fetch.")
    except Exception as e:
        print("Error:", e)
