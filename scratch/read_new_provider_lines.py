import re

file_path = r"d:\Dev\aplicacao_new\NEW_PROVIDER.txt"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Vamos procurar por URLs ou palavras interessantes nas linhas
url_pattern = re.compile(r'https?://[^\s\'"]+')

endpoints = set()
for idx, line in enumerate(lines):
    # Procura por URLs
    matches = url_pattern.findall(line)
    for m in matches:
        endpoints.add(m)
        
    # Se contiver curl ou similar, vamos printar as proximas 2 linhas
    if "curl" in line.lower() or "similar" in line.lower() or "relacionad" in line.lower():
        print(f"L{idx+1}: {line.strip()[:150]}")

print("\nAll unique URLs found:")
for ep in sorted(list(endpoints)):
    print(ep)
