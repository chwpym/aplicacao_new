import re

def canonicalizar_id_para_imagem(id_peca: str) -> str:
    if not id_peca:
        return ""

    # Sempre Maiúsculo e Limpo de espaços
    clean = id_peca.upper().replace(" ", "").strip()

    # Se contiver barra, separa para tratar
    sub_parts = clean.split("/")
    main_part = sub_parts[0]
    suffix = sub_parts[1] if len(sub_parts) > 1 else ""

    # Trata a parte principal (Injetar hífen se faltar)
    if "-" not in main_part:
        match = re.match(r"^([A-Z]{2,3})(\d+)$", main_part)
        if match:
            main_part = f"{match.group(1)}-{match.group(2)}"

    # Remonta com hífen no lugar da barra
    result = main_part
    if suffix:
        result = f"{main_part}-{suffix}"

    # Garante que qualquer outra barra perdida vire hífen
    return result.replace("/", "-")

tests = [
    "AKX-35323/C",
    "AKX35323/C",
    "AKX35323",
    "AKX-35323",
    "wo130",
    "wo-130",
    "AKX-35323/C/B"
]

print("=== TESTANDO CANONICALIZAÇÃO ===")
for t in tests:
    print(f"{t} -> {canonicalizar_id_para_imagem(t)}")
