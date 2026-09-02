import re

def remover_palavras_avancado(texto: str, palavras: list[str]) -> str:
    """Remove palavras ou frases indesejadas do texto."""
    if not texto or not palavras:
        return texto or ""
        
    # Ordena por tamanho descendente para remover frases longas antes de palavras curtas
    palavras_ordenadas = sorted(set(palavras), key=len, reverse=True)
    
    for palavra in palavras_ordenadas:
        if not palavra.strip():
            continue
        # Padrao regex para palavra inteira, insensível a maiúsculas
        padrao = r'(?i)(?<!\w){}(?!\w)'.format(re.escape(palavra.strip()))
        texto = re.sub(padrao, ' ', texto)
        
    # Limpa espaços extras
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def aplicar_siglas_avancado(texto: str, siglas_map: dict) -> str:
    """Substitui ocorrências de palavras inteiras (boundary) pelas siglas mapeadas."""
    if not texto or not siglas_map:
        return texto or ""
        
    # Ordena as chaves por tamanho descendente para pegar frases longas primeiro
    chaves_ordenadas = sorted(siglas_map.keys(), key=len, reverse=True)
    
    for chave in chaves_ordenadas:
        if not chave.strip():
            continue
        substituto = siglas_map[chave]
        # Padrao regex para palavra inteira, insensível a maiúsculas
        padrao = r'(?i)(?<!\w){}(?!\w)'.format(re.escape(chave.strip()))
        texto = re.sub(padrao, substituto, texto)
        
    return texto.strip()

def merge_year_ranges(ranges: list[tuple]) -> tuple[str | None, str | None]:
    """Mescla múltiplos intervalos de anos em um intervalo único (mínimo e máximo), preservando strings originais."""
    if not ranges:
        return None, None
        
    def extract_year_int(val_str) -> int:
        if not val_str:
            return 0
        val_str = str(val_str).strip()
        if "/" in val_str:
            parts = val_str.split("/")
            year_part = parts[-1].strip()
        else:
            year_part = val_str
            
        match = re.search(r'\d+', year_part)
        if match:
            y = int(match.group(0))
            if len(match.group(0)) == 2:
                return 2000 + y if y <= 40 else 1900 + y
            return y
        return 0

    processed_ranges = []
    for s, e in ranges:
        start_val = extract_year_int(s) if s is not None and str(s).strip() != "" else 0
        end_val = extract_year_int(e) if e is not None and str(e).strip() != "" else 9999
        processed_ranges.append((start_val, end_val, s, e))
        
    if not processed_ranges:
        return None, None
        
    sorted_ranges = sorted(processed_ranges, key=lambda x: x[0])
    
    overall_min_val = sorted_ranges[0][0]
    overall_min_str = sorted_ranges[0][2]
    
    overall_max_val = sorted_ranges[0][1]
    overall_max_str = sorted_ranges[0][3]
    
    for i in range(1, len(sorted_ranges)):
        next_start_val, next_end_val, next_start_str, next_end_str = sorted_ranges[i]
        
        if next_start_val > 0 and (overall_min_val == 0 or next_start_val < overall_min_val):
            overall_min_val = next_start_val
            overall_min_str = next_start_str
            
        if next_end_val > overall_max_val:
            overall_max_val = next_end_val
            overall_max_str = next_end_str
            
    final_min_start = overall_min_str if overall_min_val != 0 else None
    final_max_end = overall_max_str if overall_max_val != 9999 else None
    
    return final_min_start, final_max_end

def format_ano_string(start_year, end_year):
    """Formata o intervalo de anos para exibição."""
    if start_year is not None and end_year is not None:
        if start_year == end_year:
            return str(start_year)
        else:
            return f"{start_year}...{end_year}"
    elif start_year is not None:
        return f"{start_year}..."
    elif end_year is not None:
        return f"...{end_year}"
    return ""
