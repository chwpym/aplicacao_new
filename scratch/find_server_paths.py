import re

file_path = r"d:\Dev\aplicacao_new\NEW_PROVIDER.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find any path starting with /server/
paths = re.findall(r'/server/\S+', content)
unique_paths = sorted(list(set(paths)))

print("--- UNIQUE /server/ PATHS ---")
for p in unique_paths:
    print(p)
