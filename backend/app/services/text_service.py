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

def merge_year_ranges(ranges: list[tuple]) -> tuple[int | None, int | None]:
    """Mescla múltiplos intervalos de anos em um intervalo único (mínimo e máximo)."""
    if not ranges:
        return None, None
        
    processed_ranges = []
    for s, e in ranges:
        # Tenta converter para int se for string
        try:
            start_val = int(s) if s is not None and str(s).strip() != "" else 0
        except (ValueError, TypeError):
            start_val = 0
            
        try:
            end_val = int(e) if e is not None and str(e).strip() != "" else 9999
        except (ValueError, TypeError):
            end_val = 9999
            
        processed_ranges.append((start_val, end_val))
        
    if not processed_ranges:
        return None, None
        
    sorted_ranges = sorted(processed_ranges, key=lambda x: x[0])
    overall_min_start = sorted_ranges[0][0]
    overall_max_end = sorted_ranges[0][1]
    
    for i in range(1, len(sorted_ranges)):
        next_start, next_end = sorted_ranges[i]
        # Se os intervalos se sobrepõem ou são contínuos
        if next_start <= overall_max_end + 1:
            overall_max_end = max(overall_max_end, next_end)
        else:
            # No sistema antigo, ele apenas atualizava o max_end mesmo sem sobreposição 
            # (provavelmente para pegar o range total de aplicação da peça)
            overall_max_end = max(overall_max_end, next_end)
            
    final_min_start = overall_min_start if overall_min_start != 0 else None
    final_max_end = overall_max_end if overall_max_end != 9999 else None
    
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
