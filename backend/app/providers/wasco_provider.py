from typing import Dict, Any
from app.providers.busca_na_rede_provider import BaseBuscaNaRedeProvider


class WascoProvider(BaseBuscaNaRedeProvider):
    """
    Provedor específico para DHF WASCO (DHF é o antigo nome da marca).
    Herda do portal Busca na Rede (https://buscanarede.com.br/wasco).
    As abas DESCRIÇÃO/ADICIONAIS e similares são tratadas pelo provedor base.
    """
    def __init__(self, config: Dict[str, Any]):
        if not config.get("nome"):
            config["nome"] = "DHF WASCO"

        mapeamento = config.get("mapeamento", {})
        if isinstance(mapeamento, str):
            import json
            mapeamento = json.loads(mapeamento) if mapeamento.strip() else {}
        mapeamento["brand_slug"] = "wasco"
        config["mapeamento"] = mapeamento

        super().__init__(config)

    def formatar_resultado(self, item):
        # A tabela do site traz o intervalo junto ("2012 / 2021"); separamos início e fim
        anos = str(item.get("ano_inicio") or "")
        if "/" in anos and not item.get("ano_fim"):
            partes = [p.strip() for p in anos.split("/") if p.strip()]
            if partes:
                item["ano_inicio"] = partes[0]
                if len(partes) > 1:
                    item["ano_fim"] = partes[-1]
        return super().formatar_resultado(item)

    def _parse_application_block(self, block: str) -> dict | None:
        # Remove repetições adjacentes de SEO (ex: "FIAT FIAT PALIO PALIO") e hífens soltos
        clean_words = []
        for w in block.split():
            if w == "-":
                continue
            if clean_words and w.upper() == clean_words[-1].upper():
                continue
            clean_words.append(w)
        return super()._parse_application_block(" ".join(clean_words))
