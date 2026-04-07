from abc import ABC, abstractmethod
import logging
from ..schemas.peca import PecaSchema

class BaseProvider(ABC):
    @abstractmethod
    async def buscar(self, termo: str) -> list[dict]:
        """
        Realiza a busca no provedor e retorna uma lista de dicionários
        com as aplicações encontradas.
        """
        pass

    async def get_details(self, codigo_peca: str) -> dict:
        """
        Busca detalhes adicionais (ficha técnica, imagens extras) de uma peça.
        Pode ser sobrescrito por provedores que suportam carregamento sob demanda.
        """
        return {"ficha_tecnica": {}, "imagens": []}

    def normalizar_codigo(self, id_peca: str) -> list[str]:
        """
        Gera variações do código para busca (com/sem hifens, espaços, etc).
        Retorna uma lista de strings candidatas sempre em MAIÚSCULAS.
        """
        if not id_peca:
            return []

        id_peca = id_peca.upper().strip()
        variacoes = [id_peca]
        # Remove hifens e espaços
        clean = id_peca.replace("-", "").replace(" ", "").strip()
        if clean not in variacoes:
            variacoes.append(clean)

        # Tenta injetar hífen se for padrão comum (ex: WO545 -> WO-545)
        import re

        match = re.match(r"^([A-Z]{2,3})(\d+)$", clean)
        if match:
            with_hyphen = f"{match.group(1)}-{match.group(2)}"
            if with_hyphen not in variacoes:
                variacoes.append(with_hyphen)

        return variacoes

    def canonicalizar_id_para_imagem(self, id_peca: str) -> str:
        """
        Transforma o ID para o formato ideal de imagem (MAIÚSCULAS e com hífen se for padrão WEGA).
        """
        if not id_peca:
            return ""

        import re
        clean = id_peca.upper().replace(" ", "").strip()
        sub_parts = clean.split("/")
        main_part = sub_parts[0]

        if "-" not in main_part:
            match = re.match(r"^([A-Z]{2,3})(\d+)$", main_part)
            if match:
                main_part = f"{match.group(1)}-{match.group(2)}"

        sub_parts[0] = main_part
        return "-".join(sub_parts)

    def extrair_anos(self, ano_str):
        if not ano_str:
            return "", ""
        import re
        anos = re.findall(r"\b\d{2,4}\b", str(ano_str))

        def normalizar_ano(a):
            if len(a) == 2:
                val = int(a)
                return str(2000 + val if val <= 40 else 1900 + val)
            return a

        if not anos:
            return str(ano_str), ""

        ano_ini = normalizar_ano(anos[0])
        ano_fim = normalizar_ano(anos[1]) if len(anos) > 1 else ""
        return ano_ini, ano_fim

    def formatar_resultado(self, raw_data):
        """Padroniza os campos retornados pelos diferentes provedores."""
        res_dict = {
            "marca": str(raw_data.get("brand", raw_data.get("marca", raw_data.get("montadora", "")))).upper(),
            "veiculo": str(raw_data.get("name", raw_data.get("veiculo", ""))).upper(),
            "modelo": str(raw_data.get("model", raw_data.get("modelo", ""))).upper(),
            "versao": str(raw_data.get("version", raw_data.get("versao", ""))).upper(),
            "motor": str(raw_data.get("engineName", raw_data.get("motor", ""))).upper(),
            "configuracao_motor": str(raw_data.get("engineConfiguration", raw_data.get("configuracao_motor", ""))).upper(),
            "sistema_freio": str(raw_data.get("brakeSystem", raw_data.get("sistema_freio", ""))).upper(),
            "ano_inicio": self.extrair_anos(raw_data.get("startYear", raw_data.get("ano_inicio")))[0],
            "ano_fim": self.extrair_anos(raw_data.get("startYear", raw_data.get("ano_inicio")))[1] 
                      or self.extrair_anos(raw_data.get("endYear", raw_data.get("ano_fim")))[0],
            "observacao": str(raw_data.get("note", raw_data.get("observacao", ""))).upper(),
            "apenas": str(raw_data.get("only", raw_data.get("apenas", ""))).upper(),
            "restricao": str(raw_data.get("restriction", raw_data.get("restricao", ""))).upper(),
            "posicao": str(raw_data.get("position", raw_data.get("posicao", ""))).upper(),
            "lado": str(raw_data.get("side", raw_data.get("lado", ""))).upper(),
            "direcao": str(raw_data.get("steering", raw_data.get("direcao", ""))).upper(),
            "imagem": raw_data.get("image", raw_data.get("imageUrl", raw_data.get("imagem", ""))),
            "imagens": raw_data.get("images", raw_data.get("imagens", [])),
            "referencias": raw_data.get("originalNumbers", raw_data.get("crossReferences", raw_data.get("referencias", ""))),
            "ficha_tecnica": raw_data.get("ficha_tecnica"),
            "provider_id": raw_data.get("provider_id"),
            "provedor": raw_data.get("provedor"),
            "codigo": raw_data.get("codigo"),
        }

        # Validação Silenciosa
        try:
            PecaSchema(**res_dict)
        except Exception as e:
            logging.warning(f"Integridade de dados comprometida: {e}")

        return res_dict
