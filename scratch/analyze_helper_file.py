import re

# Read NEW_PROVIDER.txt and extract all URL endpoints or curl-like requests
file_path = r"d:\Dev\aplicacao_new\NEW_PROVIDER.txt"

# Try reading as UTF-16 and UTF-8
content = ""
for encoding in ['utf-16', 'utf-8', 'latin-1']:
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        print(f"Successfully read file with {encoding} encoding.")
        break
    except Exception as e:
        print(f"Failed with {encoding}: {e}")

if not content:
    print("Could not read file.")
    exit(1)

# Find all occurrences of URLs that start with https://b2b.jahu.com.br/server/public/service
endpoints = re.findall(r'https://b2b\.jahu\.com\.br/server/public/service/\S+', content)
unique_endpoints = sorted(list(set(endpoints)))

print("\n--- FOUND ENDPOINTS ---")
for ep in unique_endpoints:
    print(ep)

# Also let's find lines containing curl
print("\n--- LINES WITH CURL ---")
lines = content.split('\n')
for idx, line in enumerate(lines):
    if 'curl' in line.lower():
        print(f"Line {idx+1}: {line}")
