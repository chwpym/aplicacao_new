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
        
        # Detectar se o texto indica "em diante" ou continuidade
        text_upper = str(ano_str).upper()
        # "2016 -->" ou "2016 ..." ou "2016 DIANTE"
        is_onwards = any(x in text_upper for x in ["-->", "...", "DIANTE", "ONWARDS", " ON", "..", "-->"])
        
        anos = re.findall(r"\b\d{2,4}\b", str(ano_str))

        def normalizar_ano(a):
            if len(a) == 2:
                val = int(a)
                return str(2000 + val if val <= 40 else 1900 + val)
            return a

        if not anos:
            return str(ano_str), ""

        ano_ini = normalizar_ano(anos[0])
        # Se houver segundo ano, usa ele. Se for "em diante", deixa vazio (o formatar_resultado cuidará).
        ano_fim = normalizar_ano(anos[1]) if len(anos) > 1 else ""
        
        return ano_ini, ano_fim

    def extrair_combustivel(self, texto: str) -> str:
        """Extrai o tipo de combustível de uma string sem alterar o texto original."""
        if not texto: return ""
        t = str(texto).upper()
        
        keywords = {
            "FLEX": "FLEX",
            "GASOLINA": "GASOLINA",
            "ALCOOL": "ALCOOL",
            "ÁLCOOL": "ALCOOL",
            "DIESEL": "DIESEL",
            "HIBRID": "HÍBRIDO",
            "HÍBRID": "HÍBRIDO",
            "TURBO DIESEL": "DIESEL",
            "ELETRIC": "ELÉTRICO"
        }
        
        for key, val in keywords.items():
            if key in t:
                return val
        return ""

    def limpar_texto_wega(self, texto: str) -> str:
        """Remove caracteres de controle ou codificação quebrada (como os da Wega)."""
        if not texto: return ""
        # Remove caracteres ASCII de controle e o específico que o usuário reportou
        import re
        # Substitui padrões comuns de erro de encoding da Wega
        t = str(texto).replace("\ufffd", "À") # Tenta converter o placeholder comum
        # Limpa espaços duplos
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def parse_specifications(self, specifications: any) -> dict:
        """
        Parser universal para transformar diferentes formatos de especificações
        em um dicionário plano { "Rótulo": "Valor" }.
        Suporta: Lista de objetos (Fraga), Dicionários e Listas simples.
        """
        if not specifications:
            return {}

        ficha = {}

        # Caso 1: Lista de Dicionários (Padrão Fraga/GraphQL)
        if isinstance(specifications, list):
            for spec in specifications:
                if isinstance(spec, dict):
                    # Fraga usa 'description' e 'value'
                    desc = spec.get("description") or spec.get("label") or spec.get("name")
                    val = spec.get("value")
                    if desc and val:
                        # Limpeza básica
                        label = str(desc).strip()
                        # Capitalização amigável (ex: "PESO BRUTO" -> "Peso Bruto")
                        if label.isupper() and len(label) > 3:
                            label = label.title()
                        
                        # Se houver categoria, podemos anexar se for útil, 
                        # mas por enquanto vamos manter limpo
                        ficha[label] = str(val).strip()
                elif isinstance(spec, str) and ":" in spec:
                    # Caso venha como "Chave: Valor"
                    parts = spec.split(":", 1)
                    ficha[parts[0].strip()] = parts[1].strip()

        # Caso 2: Dicionário Direto (Padrão REST/Scrapers internos)
        elif isinstance(specifications, dict):
            for k, v in specifications.items():
                if k and v:
                    label = str(k).strip()
                    if label.isupper() and len(label) > 3:
                        label = label.title()
                    ficha[label] = str(v).strip()

        return ficha

    def formatar_resultado(self, raw_data):
        """Padroniza os campos retornados pelos diferentes provedores."""
        from app.services.automaker_service import automaker_service
        from app.utils.synonyms import TECHNICAL_BRANDS
        import re

        # Identifica a montadora primeiro para aplicar nas referências se necessário
        montadora_bruta = str(raw_data.get("brand", raw_data.get("montadora", raw_data.get("marca_veiculo", "")))).upper()
        montadora_padronizada = automaker_service.padronizar(montadora_bruta)

        # Trata referências (converte OEM -> ORIGINAL -> Montadora_Padronizada)
        referencias_brutas = raw_data.get("originalNumbers", raw_data.get("crossReferences", raw_data.get("referencias", "")))
        referencias_limpas = ""

        if referencias_brutas:
            if isinstance(referencias_brutas, str):
                parts = []
                for chunk in referencias_brutas.split(" | "):
                    if ":" in chunk:
                        brand, code = chunk.split(":", 1)
                        brand = brand.strip().upper()
                        code = code.strip()

                        if brand == "OEM":
                            brand = "ORIGINAL"

                        # Se a marca for ORIGINAL e temos a montadora, trocamos pelo nome da montadora
                        if brand == "ORIGINAL" and montadora_padronizada:
                            brand = montadora_padronizada
                        
                        # Padroniza a montadora da referência se ela não for técnica
                        elif brand not in TECHNICAL_BRANDS:
                            brand = automaker_service.padronizar(brand)

                        parts.append(f"{brand}: {code}")
                    else:
                        parts.append(chunk)

                # Remove duplicadas mantendo a ordem
                seen = set()
                deduped = [x for x in parts if not (x in seen or seen.add(x))]
                referencias_limpas = " | ".join(deduped)
            else:
                referencias_limpas = referencias_brutas

        res_dict = {
            "marca": str(raw_data.get("marca_peca", raw_data.get("marca", raw_data.get("provedor", "")))).upper(),
            "veiculo": montadora_padronizada,
            "modelo": str(raw_data.get("name", raw_data.get("veiculo", raw_data.get("modelo", "")))).upper(),
            "versao": str(raw_data.get("model", raw_data.get("version", raw_data.get("versao", "")))).upper(),
            "motor": str(raw_data.get("engineName", raw_data.get("motor", ""))).upper(),
            "configuracao_motor": str(raw_data.get("engineConfiguration", raw_data.get("configuracao_motor", ""))).upper(),
            "sistema_freio": str(raw_data.get("brakeSystem", raw_data.get("sistema_freio", ""))).upper(),
            "combustivel": "",
        }

        # Extração de Anos Otimizada
        start_f = raw_data.get("startYear", raw_data.get("ano_inicio"))
        end_f = raw_data.get("endYear", raw_data.get("ano_fim"))
        
        # Se start e end apontam pro mesmo campo (ex: Wega), extraímos ambos de uma vez
        y_ini, y_fim = self.extrair_anos(start_f)
        
        # Se o fim veio vazio e temos um campo de fim diferente, tentamos buscar dele
        if not y_fim and end_f and end_f != start_f:
            y_fim, _ = self.extrair_anos(end_f)
            
        # Se for "em diante" (vazio) mas o campo original tinha marcadores, garantimos que y_fim é ""
        # (A lógica de fallback no UI já cuida de mostrar "...")
        
        res_dict["ano_inicio"] = y_ini
        res_dict["ano_fim"] = y_fim
        # Inteligência de Combustível (Busca agressiva em todas as fontes)
        fontes_combustivel = [
            raw_data.get("fuel"), 
            raw_data.get("combustivel"), 
            res_dict.get("versao"), 
            res_dict.get("modelo"),
            raw_data.get("description")
        ]
        
        fuel_val = ""
        for fonte in fontes_combustivel:
            if fonte:
                extracted = self.extrair_combustivel(str(fonte))
                if extracted:
                    fuel_val = extracted
                    break
        
        res_dict["combustivel"] = fuel_val or ""
        
        # DEBUG - Remover após correção
        if "WEGA" in str(res_dict.get("marca", "")).upper() or "WEGA" in str(raw_data.get("provedor", "")).upper():
            print(f"\n[DEBUG WEGA] Modelo: {res_dict['modelo']} | Combustivel Extraído: '{res_dict['combustivel']}'")
            print(f"[DEBUG WEGA] Fontes verificadas: {fontes_combustivel}\n")

        # Limpeza Final de Textos (Específico Wega + Upper Geral)
        for key in ["modelo", "versao", "veiculo", "observacao"]:
            if key in res_dict:
                cleaned = self.limpar_texto_wega(res_dict[key])
                res_dict[key] = cleaned.upper()

        res_dict.update({
            "observacao": str(raw_data.get("note", raw_data.get("observacao", ""))).upper(),
            "apenas": str(raw_data.get("only", raw_data.get("apenas", ""))).upper(),
            "restricao": str(raw_data.get("restriction", raw_data.get("restricao", ""))).upper(),
            "posicao": str(raw_data.get("position", raw_data.get("posicao", ""))).upper(),
            "lado": str(raw_data.get("side", raw_data.get("lado", ""))).upper(),
            "direcao": str(raw_data.get("steering", raw_data.get("direcao", ""))).upper(),
            "imagem": raw_data.get("image", raw_data.get("imageUrl", raw_data.get("imagem", ""))),
            "imagens": raw_data.get("images", raw_data.get("imagens", [])),
            "referencias": referencias_limpas,
            "ficha_tecnica": self.parse_specifications(raw_data.get("ficha_tecnica") or raw_data.get("specifications")),
            "provider_id": raw_data.get("provider_id"),
            "provedor": raw_data.get("provedor"),
            "codigo": raw_data.get("codigo"),
        })

        # Validação Silenciosa
        try:
            PecaSchema(**res_dict)
        except Exception as e:
            logging.warning(f"Integridade de dados comprometida: {e}")

        return res_dict
