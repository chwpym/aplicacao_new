from abc import ABC, abstractmethod
import logging
import re
import traceback
from ..schemas.peca import PecaSchema
from app.services.logging_service import logger
from app.services.automaker_service import automaker_service
from app.services.normalization_service import normalization_service

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
        match = re.match(r"^([A-Z]{2,4})(\d+)$", clean)
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

        clean = id_peca.upper().replace(" ", "").strip()
        sub_parts = clean.split("/")
        main_part = sub_parts[0]

        if "-" not in main_part:
            match = re.match(r"^([A-Z]{2,4})(\d+)$", main_part)
            if match:
                main_part = f"{match.group(1)}-{match.group(2)}"

        sub_parts[0] = main_part
        return "-".join(sub_parts)

    def extrair_anos(self, ano_str):
        if not ano_str:
            return "", ""
        
        text_upper = str(ano_str).upper()
        is_onwards = any(x in text_upper for x in ["-->", "...", "DIANTE", "ONWARDS", " ON", "..", ">"])
        
        # Tenta capturar anos em formatos como 10/2000, 01/03 ou apenas 2005
        # Regex procura por grupos de dígitos que podem estar precedidos por /
        matches = re.findall(r"(?:/)?(\d{2,4})\b", str(ano_str))
        
        def normalizar_ano(a):
            a = str(a).strip()
            if len(a) == 2:
                val = int(a)
                return str(2000 + val if val <= 40 else 1900 + val)
            return a

        if not matches:
            return str(ano_str), ""

        # Se tiver formato MM/AAAA, o ano é o segundo grupo ou o grupo mais longo
        # Vamos filtrar para pegar apenas o que parece ano (2 ou 4 dígitos, ignorando meses < 13 se houver ambiguidade)
        anos_validos = []
        for m in matches:
            if len(m) == 4:
                anos_validos.append(m)
            elif len(m) == 2 and (not anos_validos or int(m) > 12): # Heurística simples
                anos_validos.append(normalizar_ano(m))

        if not anos_validos:
            # Fallback para o primeiro match se nada for ideal
            ano_ini = normalizar_ano(matches[0])
            ano_fim = normalizar_ano(matches[1]) if len(matches) > 1 else ""
        else:
            ano_ini = anos_validos[0]
            ano_fim = anos_validos[1] if len(anos_validos) > 1 else ""
        
        if is_onwards:
            ano_fim = ""
            
        return ano_ini, ano_fim

    def extrair_combustivel(self, texto: str) -> str:
        """
        [DEPRECATED] Use normalization_service internamente via formatar_resultado.
        Mantido apenas para compatibilidade. Usa busca por substring (menos precisa).
        Para uso interno do pipeline, o NormalizationService usa regex com \\b (word boundary).
        """
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
        """Remove caracteres de controle ou codificação quebrada."""
        if not texto: return ""
        t = str(texto).replace("\ufffd", "À")
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def mesclar_motorizacao(self, termo: str, texto: str) -> str:
        """Adiciona apenas as partes do termo que não existem no texto base (busca por tokens)."""
        if not termo: return texto
        if not texto: return termo
        
        t_texto = re.sub(r'[/()|,]', ' ', str(texto).upper())
        tokens_texto = set(t_texto.split())
        
        partes_termo = str(termo).upper().split()
        partes_para_adicionar = []
        
        for p in partes_termo:
            p_clean = re.sub(r'[/()|,]', ' ', p)
            todas_partes_presentes = all(sub_p in tokens_texto for sub_p in p_clean.split())
            if not todas_partes_presentes:
                partes_para_adicionar.append(p)
                
        if partes_para_adicionar:
            return f"{' '.join(partes_para_adicionar)} {texto}".strip()
        return str(texto).strip()

    def parse_specifications(self, specifications: any) -> dict:
        """Parser universal para transformar especificações em dicionário plano UPPER CASE."""
        if not specifications: return {}
        ficha = {}
        if isinstance(specifications, list):
            for spec in specifications:
                if isinstance(spec, dict):
                    desc = spec.get("description") or spec.get("label") or spec.get("name")
                    val = spec.get("value")
                    if desc and val:
                        ficha[str(desc).strip().upper()] = str(val).strip().upper()
        elif isinstance(specifications, dict):
            for k, v in specifications.items():
                if k and v:
                    ficha[str(k).strip().upper()] = str(v).strip().upper()
        return ficha

    def formatar_resultado(self, raw_data, skip_automaker=False):
        """Padroniza os campos seguindo a SKILL: veiculo=Montadora, modelo=Carro, versao=Modelo."""
        # Nota: automaker_service e normalization_service importados no topo do arquivo
        
        # 1. Identidade (Master Catalog / FIPE Validation)
        montadora_bruta = str(raw_data.get("montadora", raw_data.get("veiculo", raw_data.get("brand", "")))).upper()
        modelo_bruto = str(raw_data.get("modelo", raw_data.get("model", raw_data.get("name", "")))).upper()
        versao_bruta = str(raw_data.get("versao", raw_data.get("version", ""))).upper()

        # Validação Cruzada FIPE (DuckDB) - Com bypass opcional para performance
        if skip_automaker:
            montadora_padronizada = montadora_bruta
            modelo_fipe = modelo_bruto
        else:
            logger.info("NORMALIZATION", f"Processando: {montadora_bruta} {modelo_bruto} ({self.config.get('nome')})")
            montadora_padronizada, modelo_fipe = automaker_service.validar_aplicacao(montadora_bruta, modelo_bruto)
            
            if montadora_padronizada != montadora_bruta:
                logger.info("NORMALIZATION", f"Marca Corrigida: {montadora_bruta} -> {montadora_padronizada}")
        
        # Se o modelo bruto estava vazio e a FIPE retornou algo (via busca por marca), usamos.
        modelo_final = modelo_fipe if modelo_fipe and not modelo_bruto else modelo_bruto

        # 2. Referências
        referencias_brutas = raw_data.get("referencias", raw_data.get("originalNumbers", raw_data.get("crossReferences", "")))
        referencias_limpas = ""
        if referencias_brutas:
            if isinstance(referencias_brutas, list):
                referencias_brutas = " | ".join(referencias_brutas)
            try:
                referencias_limpas = normalization_service.padronizar_referencias(referencias_brutas, montadora_padronizada)
            except:
                referencias_limpas = str(referencias_brutas)

        # 3. Motorização e Normalização Técnica
        motor_bruto = str(raw_data.get("motor", "")).upper()
        config_bruta = str(raw_data.get("configuracao_motor", "")).upper()

        motor_padrao = motor_bruto
        config_padrao = config_bruta
        modelo_padrao = modelo_final
        versao_padrao = versao_bruta

        try:
            # Normalizamos o conjunto completo para separar Motor de Configuração de forma inteligente
            # Concatenamos motor e config para re-extrair padrões (ex: VHC 1.0 8V -> 1.0 8V | VHC)
            texto_completo_motor = f"{motor_bruto} {config_bruta}".strip()
            if texto_completo_motor:
                m_p, c_p, residuo_motor = normalization_service.extrair_motorizacao(texto_completo_motor)
                
                # Se conseguimos extrair algo, usamos os valores padronizados
                # Caso contrário, mantemos os originais (definidos acima)
                if m_p or c_p or residuo_motor:
                    motor_padrao = m_p
                    config_padrao = c_p
                    
                    # O que sobrou da limpeza vai para a configuração
                    if residuo_motor:
                        config_padrao = f"{config_padrao} {residuo_motor}".strip()
                    
                    # Se mesmo após a extração o motor ficou vazio (ex: só tinha siglas), 
                    # mas o bruto tinha algo, mantemos o bruto para não perder informação,
                    # a menos que o bruto seja puramente técnico (já movido para config).
                    if not motor_padrao and motor_bruto and motor_bruto not in config_padrao:
                        motor_padrao = motor_bruto

            # Limpamos o nome do carro e a versão de resíduos de motor (ex: CELTA 1.0 -> CELTA)
            # Salvamos o que foi extraído caso o motor original estivesse incompleto
            m_p_mod, c_p_mod, modelo_limpo = normalization_service.extrair_motorizacao(modelo_final)
            m_p_ver, c_p_ver, versao_limpa = normalization_service.extrair_motorizacao(versao_bruta)
            
            # Se o modelo ou versão tinham cilindrada/válvulas que o motor não tem, nós mesclamos
            # Fase 3: Usando mesclar_motorizacao para evitar falso positivo (ex: 8V em 1.8V)
            motor_padrao = self.mesclar_motorizacao(m_p_mod, motor_padrao)
            motor_padrao = self.mesclar_motorizacao(m_p_ver, motor_padrao)
            
            config_padrao = self.mesclar_motorizacao(c_p_mod, config_padrao)
            config_padrao = self.mesclar_motorizacao(c_p_ver, config_padrao)

            modelo_padrao = modelo_limpo
            versao_padrao = versao_limpa
        except Exception as e:
            logger.warning(
                "NORMALIZATION",
                f"Erro na normalização [{self.config.get('nome', 'DESCONHECIDO')}]: {e}\n{traceback.format_exc()}"
            )

        res_dict = {
            "marca": str(raw_data.get("marca_peca", raw_data.get("marca", raw_data.get("provedor", "")))).upper(),
            "veiculo": montadora_padronizada, # Coluna Montadora
            "modelo": modelo_padrao,         # Coluna Veículo/Carro
            "versao": versao_padrao,         # Coluna Modelo/Versão
            "motor": motor_padrao,
            "configuracao_motor": config_padrao,
            "sistema_freio": str(raw_data.get("brakeSystem", raw_data.get("sistema_freio", ""))).upper(),
            "combustivel": "",
        }

        # 4. Anos
        y_ini, y_fim = self.extrair_anos(raw_data.get("ano_inicio", raw_data.get("startYear", "")))
        if not y_fim:
            y_fim, _ = self.extrair_anos(raw_data.get("ano_fim", raw_data.get("endYear", "")))
        res_dict["ano_inicio"] = y_ini
        res_dict["ano_fim"] = y_fim

        # 5. Combustível via NormalizationService (usa regex com \b - correto e consistente)
        # Constrói um texto agregado de todos os campos que podem conter o combustível
        texto_combustivel = f"{versao_bruta} {modelo_bruto} {config_padrao} {raw_data.get('fuel', '')} {raw_data.get('combustivel', '')}".strip()
        _, config_com_fuel, _ = normalization_service.extrair_motorizacao(texto_combustivel)
        # O NormalizationService coloca o combustivel dentro da config. Extraimos ele.
        fuel_val = ""
        for comb in normalization_service.combustiveis:
            if comb in config_com_fuel.upper():
                fuel_val = comb
                break
        res_dict["combustivel"] = fuel_val or ""

        # 6. Limpeza e Campos Extras
        for key in ["modelo", "versao", "veiculo", "motor", "configuracao_motor", "observacao"]:
            if key in res_dict:
                # Primeiro a limpeza técnica padrão
                val = self.limpar_texto_wega(res_dict[key]).upper()
                # Depois a limpeza customizada (Demanda 1)
                res_dict[key] = normalization_service.aplicar_limpeza_customizada(key, val)

        res_dict.update({
            "observacao": str(raw_data.get("observacao", raw_data.get("note", ""))).upper(),
            "apenas": str(raw_data.get("apenas", raw_data.get("only", ""))).upper(),
            "restricao": str(raw_data.get("restricao", raw_data.get("restriction", ""))).upper(),
            "posicao": str(raw_data.get("posicao", raw_data.get("position", ""))).upper(),
            "lado": str(raw_data.get("lado", raw_data.get("side", ""))).upper(),
            "direcao": str(raw_data.get("direcao", raw_data.get("steering", ""))).upper(),
            "imagem": raw_data.get("imagem", raw_data.get("image", raw_data.get("imageUrl", ""))),
            "imagens": raw_data.get("imagens", raw_data.get("images", [])),
            "referencias": referencias_limpas,
            "ficha_tecnica": self.parse_specifications(raw_data.get("ficha_tecnica") or raw_data.get("specifications")),
            "provider_id": self.config.get("id"),
            "provedor": str(self.config.get("nome")).upper(),
            "codigo": raw_data.get("codigo"),
        })

        try:
            # Validação rápida de schema antes de retornar
            PecaSchema(**res_dict)
        except Exception as e:
            logging.warning(f"Erro Schema em {self.config.get('nome')}: {e}")

        return res_dict
