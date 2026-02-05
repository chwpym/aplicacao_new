from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    async def buscar(self, termo: str) -> list[dict]:
        """
        Realiza a busca no provedor e retorna uma lista de dicionários
        com as aplicações encontradas.
        Cada dicionário deve seguir o formato padronizado do sistema.
        """
        pass

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
        Ex: wo130 -> WO-130
        """
        if not id_peca:
            return ""

        # Sempre Maiúsculo e Limpo
        clean = id_peca.upper().replace(" ", "").strip()

        # Se contiver hífen, apenas garante maiúsculas
        if "-" in clean:
            return clean

        # Se for padrão Letras + Números (WEGA/SABO/etc), injeta hífen
        import re

        match = re.match(r"^([A-Z]{2,3})(\d+)$", clean)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        return clean

    def extrair_anos(self, ano_str):
        """Extrai ano de início e fim de strings como '2014 -->', '14 - 18', etc."""
        if not ano_str:
            return "", ""
        import re

        # Encontra todos os números de 2 ou 4 dígitos
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
        return {
            "marca": str(
                raw_data.get(
                    "brand", raw_data.get("marca", raw_data.get("montadora", ""))
                )
            ).upper(),
            "veiculo": str(raw_data.get("name", raw_data.get("veiculo", ""))).upper(),
            "modelo": str(raw_data.get("model", raw_data.get("modelo", ""))).upper(),
            "motor": str(raw_data.get("engineName", raw_data.get("motor", ""))).upper(),
            "configuracao_motor": str(
                raw_data.get(
                    "engineConfiguration", raw_data.get("configuracao_motor", "")
                )
            ).upper(),
            "sistema_freio": str(
                raw_data.get("brakeSystem", raw_data.get("sistema_freio", ""))
            ).upper(),
            "ano_inicio": self.extrair_anos(
                raw_data.get("startYear", raw_data.get("ano_inicio"))
            )[0],
            "ano_fim": self.extrair_anos(
                raw_data.get("startYear", raw_data.get("ano_inicio"))
            )[1]
            or self.extrair_anos(raw_data.get("endYear", raw_data.get("ano_fim")))[0],
            "observacao": str(
                raw_data.get("note", raw_data.get("observacao", ""))
            ).upper(),
            "apenas": str(raw_data.get("only", raw_data.get("apenas", ""))).upper(),
            "restricao": str(
                raw_data.get("restriction", raw_data.get("restricao", ""))
            ).upper(),
            "posicao": str(
                raw_data.get("position", raw_data.get("posicao", ""))
            ).upper(),
            "lado": str(raw_data.get("side", raw_data.get("lado", ""))).upper(),
            "direcao": str(
                raw_data.get("steering", raw_data.get("direcao", ""))
            ).upper(),
            "imagem": raw_data.get(
                "image", raw_data.get("imageUrl", raw_data.get("imagem", ""))
            ),
            "imagens": raw_data.get("images", raw_data.get("imagens", [])),
            "referencias": raw_data.get(
                "originalNumbers",
                raw_data.get("crossReferences", raw_data.get("referencias", "")),
            ),
        }
