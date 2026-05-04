import re
from typing import Tuple
from app.utils.synonyms import TECHNICAL_BRANDS, AUTOMAKER_SYNONYMS, ENGINE_KEYWORDS, FUEL_SYNONYMS

class NormalizationService:
    """
    Serviço de normalização central para padronizar dados brutos 
    recebidos dos provedores de catálogo antes do agrupamento.
    """
    def __init__(self):
        # Combustíveis comuns no Brasil e Mercosul (nomes completos)
        self.combustiveis = ["FLEX", "GASOLINA", "DIESEL", "ALCOOL", "ÁLCOOL", "TETRAFUEL", "GNV", "HÍBRIDO", "HIBRIDO", "ELETRICO", "ELÉTRICO", "LPG", "BI-FUEL", "BIFUEL"]
        
    def extrair_motorizacao(self, texto: str) -> Tuple[str, str, str]:
        """
        Extrai cilindrada, válvulas e combustível do texto e limpa o texto original.
        Retorna (motor_padronizado, configuracao_padronizada, texto_limpo).
        
        EXEMPLO: "VHC 1.0 8V FLEX" -> ("1.0 8V", "FLEX VHC", "")
        """
        if not texto:
            return "", "", ""
            
        texto_limpo = str(texto).upper().replace("  ", " ").strip()
        
        # 1. Extrair Cilindrada (ex: 1.0, 1.4, 2.0, 1.0L, 1,4)
        cilindrada = ""
        # Regex atualizada: suporta ponto ou vírgula (\d[\.,]\d)
        cilindrada_match = re.search(r'\b(\d[\.,]\d)L?\b', texto_limpo)
        if cilindrada_match:
            cilindrada = cilindrada_match.group(1).replace(",", ".") # Padroniza para ponto
            texto_limpo = re.sub(r'\b' + re.escape(cilindrada_match.group(0)) + r'\b', '', texto_limpo)
            
        # 2. Extrair Válvulas (ex: 8V, 16V)
        valvulas = ""
        valvulas_match = re.search(r'\b(\d{1,2}V)\b', texto_limpo)
        if valvulas_match:
            valvulas = valvulas_match.group(1)
            texto_limpo = re.sub(r'\b' + re.escape(valvulas) + r'\b', '', texto_limpo)
            
        # 3. Extrair Combustível e Keywords Técnicas
        config_parts = []
        
        # Primeiro tenta os sinônimos de combustível (F -> FLEX)
        for sigla, nome_completo in FUEL_SYNONYMS.items():
            # Usamos boundary e escape para segurança
            pattern = r'\b' + re.escape(sigla) + r'\b'
            if re.search(pattern, texto_limpo):
                config_parts.append(nome_completo)
                texto_limpo = re.sub(pattern, '', texto_limpo)
                # Removemos do set de keywords para não duplicar se a sigla estiver lá também
                break
        
        # Se não achou por sigla, tenta por nome direto (GASOLINA, DIESEL, HÍBRIDO)
        for comb in self.combustiveis:
            pattern = r'\b' + re.escape(comb) + r'\b'
            if re.search(pattern, texto_limpo):
                config_parts.append(comb)
                texto_limpo = re.sub(pattern, '', texto_limpo)
                # Não damos break aqui para capturar casos como "HÍBRIDO GASOLINA"
        
        # 4. Identificar Keywords Técnicas (VHC, MPFI, etc.)
        # Elas vão para a coluna de configuração/residuo
        encontradas_kw = []
        for kw in ENGINE_KEYWORDS:
             if re.search(r'\b' + re.escape(kw) + r'\b', texto_limpo):
                encontradas_kw.append(kw)
                texto_limpo = re.sub(r'\b' + re.escape(kw) + r'\b', '', texto_limpo)
        
        # Adiciona as keywords encontradas à configuração
        if encontradas_kw:
            config_parts.extend(sorted(encontradas_kw))

        # Montar campos padronizados
        motor_parts = []
        if cilindrada: motor_parts.append(cilindrada)
        if valvulas: motor_parts.append(valvulas)
        motor_padrao = " ".join(motor_parts)
        
        # Remove duplicatas mantendo ordem (Combustível primeiro)
        vistos = set()
        config_final = []
        for p in config_parts:
            if p not in vistos:
                config_final.append(p)
                vistos.add(p)
                
        config_padrao = " ".join(config_final)
        
        # Limpa espaços extras e pontuação órfã no resíduo
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        # Remove separadores soltos no início/fim (- , / |)
        texto_limpo = re.sub(r'^[\s\-/|,\.]+|[\s\-/|,\.]+$', '', texto_limpo)
        
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
                
                # Garante que códigos internos (ex: COD1:COD2) usem o separador ' - '
                codigo = str(codigo).replace(":", " - ").strip()

                # Se for marca técnica, vai pro aftermarket
                if marca in TECHNICAL_BRANDS:
                    aftermarket_refs.append(f"{marca}: {codigo}")
                else:
                    # Verifica sinônimos de montadora (VW -> VOLKSWAGEN)
                    if marca in AUTOMAKER_SYNONYMS:
                        marca = AUTOMAKER_SYNONYMS[marca]
                    oem_refs.append(f"{marca}: {codigo}")
            else:
                # Não tem ":", limpamos colons órfãos também
                outras_refs.append(str(parte).replace(":", " - ").strip())
                
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
