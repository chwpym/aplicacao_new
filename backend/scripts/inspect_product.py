import json

d = json.load(open('dump_product.json', encoding='utf-8'))

print("=== IMAGES (7) ===")
for i in d.get('images', []):
    print(f"  {i.get('format','?'):20s} -> {i.get('url','')}")

print("\n=== DIMENSIONS ===")
print(json.dumps(d.get('dimensions'), indent=2, ensure_ascii=False))

print("\n=== WEIGHT ===")
print(json.dumps(d.get('weight'), indent=2, ensure_ascii=False))

print("\n=== VIDEOS ===")
print(json.dumps(d.get('videos'), indent=2, ensure_ascii=False))

print("\n=== CLASSIFICATIONS ===")
for c in d.get('classifications', []):
    for feat in c.get('features', []):
        print(f"  {feat.get('name','?'):30s} = {', '.join(v.get('value','') for v in feat.get('featureValues',[]))}")

print("\n=== DOCUMENTS (first 5) ===")
for dg in d.get('documentGroups', [])[:5]:
    print(f"  Grupo: {dg.get('name','?')}")
    for doc in dg.get('documents', [])[:2]:
        print(f"    - {doc.get('description','')} -> {doc.get('url','')}")

print("\n=== FULL NAME ===")
print(f"  {d.get('fullName')}")

print("\n=== CATEGORIES ===")
for cat in d.get('categories', []):
    print(f"  {cat.get('name','?')}")
