from typing import Dict, Any
from app.providers.busca_na_rede_provider import BaseBuscaNaRedeProvider

class TubaCabosProvider(BaseBuscaNaRedeProvider):
    """
    Provedor específico para Tuba Cabos.
    Herda do portal Busca na Rede e ajusta colunas se necessário.
    """
    def __init__(self, config: Dict[str, Any]):
        if not config.get("nome"):
            config["nome"] = "TUBA CABOS"
        
        mapeamento = config.get("mapeamento", {})
        if isinstance(mapeamento, str):
            import json
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        mapeamento["brand_slug"] = "tubacabos"
        config["mapeamento"] = mapeamento
        
        super().__init__(config)

    def _parse_application_block(self, block: str) -> dict | None:
        parsed = super()._parse_application_block(block)
        if not parsed:
            return None
        
        # Ajustes Tuba Cabos:
        # A Tuba Cabos costuma quebrar nomes compostos (ex: DEL REY, PALIO WEEKEND).
        if parsed.get("versao") and parsed.get("modelo"):
            # Só junta se não for caso de modelo vazio
            parsed["modelo"] = f"{parsed['modelo']} {parsed['versao']}".strip()
            parsed["versao"] = ""

        # Resgate de modelo escondido no motor (Ex: 6353 - ATTRACTIVE ... GRAND SIENA GRAND SIENA)
        motor = parsed.get("motor", "")
        if motor:
            import re
            from collections import Counter
            
            # Pega palavras do motor que não são números nem palavras-chave de motor
            words = [w.upper() for w in re.split(r'\W+', motor) if w and not re.match(r'^\d', w) and w.upper() not in ('FLEX', 'GASOLINA', 'ALCOOL', 'DIESEL', 'VHC', 'MPI', 'MPFI', 'EFI', 'TDI', 'TSI', '16V', '8V')]
            
            if words:
                c = Counter(words)
                # Pega as palavras que se repetem 2 vezes ou mais
                repeated = [w for w, count in c.items() if count >= 2]
                
                if repeated:
                    # O modelo real estava escondido no motor!
                    for w in repeated:
                        motor = re.sub(rf'\b{w}\b', '', motor, flags=re.IGNORECASE)
                    
                    parsed["motor"] = re.sub(r'\s+', ' ', motor).replace('/ ', ' ').replace(' /', ' ').strip()
                    
                    # O que estava no modelo provavelmente era a versão (ex: ATTRACTIVE)
                    versao_antiga = parsed.get("modelo", "")
                    modelo_novo = " ".join(repeated)
                    
                    parsed["modelo"] = modelo_novo
                    if versao_antiga:
                        parsed["versao"] = versao_antiga
            
        return parsed
