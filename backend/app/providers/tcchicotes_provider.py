from typing import Dict, Any
from app.providers.busca_na_rede_provider import BaseBuscaNaRedeProvider

class TcChicotesProvider(BaseBuscaNaRedeProvider):
    """
    Provedor específico para TC Chicotes.
    Herda do portal Busca na Rede e ajusta colunas se necessário.
    """
    def __init__(self, config: Dict[str, Any]):
        if not config.get("nome"):
            config["nome"] = "TC CHICOTES"
        
        mapeamento = config.get("mapeamento", {})
        if isinstance(mapeamento, str):
            import json
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        mapeamento["brand_slug"] = "tcchicotes"
        config["mapeamento"] = mapeamento
        
        super().__init__(config)

    async def buscar(self, termo: str) -> list[dict]:
        # Tratamento especial para TC Chicotes: se usuário digitar 1021021 (7 dígitos numéricos)
        # nós convertemos automaticamente para 102.1021
        termo_limpo = termo.replace(".", "").replace("-", "").strip()
        if len(termo_limpo) == 7 and termo_limpo.isdigit():
            termo_corrigido = f"{termo_limpo[:3]}.{termo_limpo[3:]}"
            import logging
            logging.info(f"TC Chicotes: Auto formatando termo {termo} para {termo_corrigido}")
            termo = termo_corrigido
            
        return await super().buscar(termo)

    def _parse_application_block(self, block: str) -> dict | None:
        # A descrição do TC Chicotes tem um SEO muito abusivo (ex: FIAT FIAT FIAT PALIO 1.5 PALIO 15 PALIO15)
        # Vamos remover palavras duplicadas sequenciais antes de mandar para a base
        words = block.split()
        clean_words = []
        for w in words:
            # Pula se for repetição da última palavra inserida
            if clean_words and w.upper() == clean_words[-1].upper():
                continue
            # Pula se for repetição da penúltima (ex: PALIO 1.5 PALIO 15)
            # Na verdade, deduplicar mantendo a ordem para qualquer palavra de texto
            if w.upper() not in [cw.upper() for cw in clean_words]:
                clean_words.append(w)
            elif w.replace(".", "").isdigit():
                # Mantém números (ex: 1.5, 16) mesmo que se repitam por acaso
                clean_words.append(w)
                
        block_limpo = " ".join(clean_words)
        
        parsed = super()._parse_application_block(block_limpo)
        if not parsed:
            return None
            
        return parsed
