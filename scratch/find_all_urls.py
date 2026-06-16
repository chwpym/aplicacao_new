import re

file_path = r"d:\Dev\aplicacao_new\NEW_PROVIDER.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find all URLs in the file (any http or https URLs)
urls = re.findall(r'https?://[a-zA-Z0-9./_?=&%-]+', content)
unique_urls = sorted(list(set(urls)))

print("--- ALL UNIQUE URLS ---")
for url in unique_urls:
    print(url)
