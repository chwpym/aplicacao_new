from typing import Dict, Any
from app.providers.busca_na_rede_provider import BaseBuscaNaRedeProvider

class SampelProvider(BaseBuscaNaRedeProvider):
    """
    Provedor específico para Sampel.
    Herda do portal Busca na Rede e ajusta colunas se necessário.
    """
    def __init__(self, config: Dict[str, Any]):
        # Forçar o brand_slug e o nome padrão
        if not config.get("nome"):
            config["nome"] = "SAMPEL"
        
        # Injetar ou garantir o brand_slug no mapeamento
        mapeamento = config.get("mapeamento", {})
        if isinstance(mapeamento, str):
            import json
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        mapeamento["brand_slug"] = "sampel"
        config["mapeamento"] = mapeamento
        
        super().__init__(config)

    def _parse_application_block(self, block: str) -> dict | None:
        parsed = super()._parse_application_block(block)
        if not parsed:
            return None
        
        # Ajuste Sampel: O site às vezes coloca o motor ANTES da montadora.
        # Ex: "E-TORQ E-TORQ E-TORQ FIAT FIAT FIAT..."
        # Nesse caso a montadora vira "E-TORQ" e o modelo vira "FIAT".
        montadora = parsed.get("montadora", "").upper()
        modelo = parsed.get("modelo", "").upper()
        
        # Lista de palavras que a Sampel costuma colocar no início (motor)
        motor_keywords = ["E-TORQ", "FIRE", "EVO", "VHC", "ZETEC", "ROCAM", "FLEX", "MPI", "MPFI"]
        
        if montadora in motor_keywords or any(kw in montadora for kw in motor_keywords):
            # Se a montadora é na verdade um motor, e o modelo for a montadora real:
            # Jogamos a montadora pro motor, o modelo pra montadora, e a versão pro modelo
            parsed["motor"] = f"{montadora} {parsed.get('motor', '')}".strip()
            parsed["montadora"] = modelo
            parsed["modelo"] = parsed.get("versao", "")
            parsed["versao"] = ""
            
        # Resgate de modelo escondido no motor (Ex: 8132 Hyundai Santa Fe -> SANTA FE SANTA FE SANTA)
        motor = parsed.get("motor", "")
        if motor:
            import re
            from collections import Counter
            
            # Pega palavras do motor que não são números nem palavras-chave de motor
            words = [w.upper() for w in re.split(r'\W+', motor) if w and not re.match(r'^\d', w) and w.upper() not in ('FLEX', 'GASOLINA', 'ALCOOL', 'DIESEL', 'VHC', 'MPI', 'MPFI', 'EFI', 'TDI', 'TSI', '16V', '8V', 'E-TORQ', 'ETORQ')]
            
            if words:
                c = Counter(words)
                # Pega as palavras que se repetem 2 vezes ou mais
                repeated = [w for w, count in c.items() if count >= 2]
                
                if repeated:
                    # O modelo real estava escondido no motor!
                    for w in repeated:
                        motor = re.sub(rf'\b{w}\b', '', motor, flags=re.IGNORECASE)
                    
                    parsed["motor"] = re.sub(r'\s+', ' ', motor).replace('/ ', ' ').replace(' /', ' ').strip()
                    
                    # Se o modelo atual estava vazio, assumimos essas palavras repetidas
                    if not parsed.get("modelo"):
                        parsed["modelo"] = " ".join(repeated)
            
        return parsed
