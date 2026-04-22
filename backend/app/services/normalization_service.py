import re
from typing import Tuple
from app.utils.synonyms import TECHNICAL_BRANDS, AUTOMAKER_SYNONYMS

class NormalizationService:
    """
    Serviço de normalização central para padronizar dados brutos 
    recebidos dos provedores de catálogo antes do agrupamento.
    """
    def __init__(self):
        # Combustíveis comuns no Brasil
        self.combustiveis = ["FLEX", "GASOLINA", "DIESEL", "ALCOOL", "ÁLCOOL", "TETRAFUEL", "GNV", "HÍBRIDO", "ELETRICO", "ELÉTRICO"]
        
    def extrair_motorizacao(self, texto: str) -> Tuple[str, str, str]:
        """
        Extrai cilindrada, válvulas e combustível do texto e limpa o texto original.
        Retorna (motor_padronizado, configuracao_padronizada, texto_limpo).
        """
        if not texto:
            return "", "", ""
            
        texto_limpo = str(texto).upper()
        
        # 1. Extrair Cilindrada (ex: 1.0, 1.4, 2.0, 1.0L)
        cilindrada = ""
        cilindrada_match = re.search(r'\b(\d\.\d)L?\b', texto_limpo)
        if cilindrada_match:
            cilindrada = cilindrada_match.group(1)
            # Remove a cilindrada do texto para limpar
            texto_limpo = re.sub(r'\b' + re.escape(cilindrada_match.group(0)) + r'\b', '', texto_limpo)
            
        # 2. Extrair Válvulas (ex: 8V, 16V)
        valvulas = ""
        valvulas_match = re.search(r'\b(\d{1,2}V)\b', texto_limpo)
        if valvulas_match:
            valvulas = valvulas_match.group(1)
            texto_limpo = re.sub(r'\b' + re.escape(valvulas) + r'\b', '', texto_limpo)
            
        # 3. Extrair Combustível
        combustivel = ""
        for comb in self.combustiveis:
            if re.search(r'\b' + comb + r'\b', texto_limpo):
                combustivel = comb
                texto_limpo = re.sub(r'\b' + comb + r'\b', '', texto_limpo)
                break
                
        # Montar "motor" padronizado
        motor_parts = []
        if cilindrada: motor_parts.append(cilindrada)
        if valvulas: motor_parts.append(valvulas)
        motor_padrao = " ".join(motor_parts)
        
        # A configuração de motor padronizada (combustível)
        config_padrao = combustivel
        
        # Limpa espaços extras
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        
        return motor_padrao, config_padrao, texto_limpo

    def padronizar_referencias(self, referencias_raw: str, montadora_padronizada: str = "") -> str:
        """
        Transforma string bruta de referências, separando OEM (Montadoras) de 
        Aftermarket (Marcas Técnicas) e ordenando OEM primeiro.
        """
        if not referencias_raw:
            return ""
            
        # Tenta padronizar os separadores mais comuns para " | "
        refs_limpas = str(referencias_raw).replace(",", " | ").replace("\n", " | ").replace(";", " | ")
        
        # Divide por | e limpa
        partes = [p.strip() for p in refs_limpas.split("|") if p.strip()]
        
        oem_refs = []
        aftermarket_refs = []
        outras_refs = []
        vistos = set()
        
        for parte in partes:
            if parte in vistos:
                continue
            vistos.add(parte)
            
            # Tenta identificar "MARCA: CODIGO"
            if ":" in parte:
                marca, codigo = parte.split(":", 1)
                marca = marca.strip().upper()
                codigo = codigo.strip()
                
                if marca == "OEM":
                    marca = "ORIGINAL"
                    
                if marca == "ORIGINAL" and montadora_padronizada:
                    marca = montadora_padronizada
                
                # Se for marca técnica, vai pro aftermarket
                if marca in TECHNICAL_BRANDS:
                    aftermarket_refs.append(f"{marca}: {codigo}")
                else:
                    # Verifica sinônimos de montadora (VW -> VOLKSWAGEN)
                    if marca in AUTOMAKER_SYNONYMS:
                        marca = AUTOMAKER_SYNONYMS[marca]
                    oem_refs.append(f"{marca}: {codigo}")
            else:
                # Não tem ":", jogamos em outras
                outras_refs.append(parte)
                
        # Junta na ordem solicitada (OEM/Originais primeiro)
        resultado_final = []
        if oem_refs:
            resultado_final.extend(sorted(oem_refs))
        if aftermarket_refs:
            resultado_final.extend(sorted(aftermarket_refs))
        if outras_refs:
            resultado_final.extend(sorted(outras_refs))
            
        return " | ".join(resultado_final)

normalization_service = NormalizationService()
