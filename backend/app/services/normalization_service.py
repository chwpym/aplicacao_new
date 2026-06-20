import re
import threading
import time
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
        
        # Cache de regras de limpeza e siglas pré-processamento
        self.regras_limpeza = {}
        self.siglas_pre_processamento = {}
        self.ultima_atualizacao_regras = 0

        # Lock para garantir Thread-Safety na recarga do cache
        # Protege contra RuntimeError em ambientes com múltiplos workers (Uvicorn --workers N)
        self._cache_lock = threading.Lock()
    def extrair_motorizacao(self, texto: str) -> Tuple[str, str, str]:
        """
        Extrai cilindrada, válvulas e combustível do texto e limpa o texto original.
        Retorna (motor_padronizado, configuracao_padronizada, texto_limpo).
        
        EXEMPLO: "VHC 1.0 8V FLEX" -> ("1.0 8V", "FLEX VHC", "")
        """
        if not texto:
            return "", "", ""
            
        texto_limpo = str(texto).upper().replace("  ", " ").strip()
        
        # Pré-processamento dinâmico (Carregado do Dicionário de Siglas 'Todos os Campos')
        for termo, substituto in self.siglas_pre_processamento.items():
            pattern = r'\b' + re.escape(termo) + r'\b'
            texto_limpo = re.sub(pattern, substituto, texto_limpo)

        # Pré-processamento de siglas compostas que quebram a extração (Fallback)
        texto_limpo = re.sub(r'\bVHC\s+E\b', 'VHC-E', texto_limpo)
        texto_limpo = re.sub(r'\bE\s*[-]?\s*TORQ\b', 'E-TORQ', texto_limpo)
        
        # 1. Extrair Cilindrada (ex: 1.0, 1.4, 2.0, 1.0L, 1,4 ou múltiplos 1.0/1.3)
        cilindrada = ""
        # Regex aprimorada: suporta ponto/vírgula e padrões múltiplos como 1.0/1.3 ou 1.6-2.0
        pattern_cil = r'\b(\d[\.,]\d(?:[/\-]\d[\.,]\d)*)L?\b'
        cilindrada_match = re.search(pattern_cil, texto_limpo)
        if cilindrada_match:
            cilindrada = cilindrada_match.group(1).replace(",", ".") # Padroniza para ponto
            texto_limpo = re.sub(pattern_cil, '', texto_limpo)
            
        # Limpeza extra: Remove anos residuais que podem ter sobrado no texto (ex: 1996/1999)
        texto_limpo = re.sub(r'\b\d{4}(?:/\d{2,4})?\b', '', texto_limpo)
            
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
        # Elas vão para a coluna de configuração/residuo respeitando a ORDEM ORIGINAL
        matches = []
        texto_temp = texto_limpo
        # Ordena keywords da maior para a menor para evitar que VHC capture dentro de VHC-E
        for kw in sorted(ENGINE_KEYWORDS, key=len, reverse=True):
             for m in re.finditer(r'\b' + re.escape(kw) + r'\b', texto_temp):
                matches.append((m.start(), kw))
             # Consome a keyword do texto_temp para não dar match duplo
             texto_temp = re.sub(r'\b' + re.escape(kw) + r'\b', ' ' * len(kw), texto_temp)
        
        # Ordena as palavras encontradas pela posição no texto original (não alfabético)
        matches.sort()
        encontradas_kw = [m[1] for m in matches]
        
        # Remove as keywords do texto original verdadeiro para limpar o resíduo
        for kw in encontradas_kw:
            texto_limpo = re.sub(r'\b' + re.escape(kw) + r'\b', '', texto_limpo)
        
        # Adiciona as keywords encontradas à configuração na ordem certa
        if encontradas_kw:
            # Removemos duplicatas mantendo a ordem
            vistos_kw = set()
            for kw in encontradas_kw:
                if kw not in vistos_kw:
                    config_parts.append(kw)
                    vistos_kw.add(kw)

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

    def carregar_regras_db(self, db):
        """Carrega regras e siglas (Todos os Campos) do DB para o cache de pré-processamento.
        Thread-safe: usa Lock para evitar RuntimeError sob carga paralela com múltiplos workers.
        """
        from app.models.models import PalavraRemover, Sigla
        
        # Evita recarregar se foi atualizado nos últimos 60 segundos (verifica sem lock para performance)
        if time.time() - self.ultima_atualizacao_regras < 60:
            return

        # Adquire o lock antes de qualquer mutação do estado compartilhado
        with self._cache_lock:
            # Dupla verificação: outro worker pode ter recarregado enquanto esperava o lock
            if time.time() - self.ultima_atualizacao_regras < 60:
                return

            try:
                # 1. Regras de Limpeza
                termos = db.query(PalavraRemover).all()
                regras = {}
                for t in termos:
                    campo = t.campo.lower()
                    if campo not in regras:
                        regras[campo] = []
                    regras[campo].append(t.palavra.upper())
                
                # 2. Siglas de Pré-processamento ("Todos os Campos" e "Config. Motor")
                siglas_db = db.query(Sigla).filter(Sigla.campo.in_(["Todos os Campos", "Config. Motor"])).all()
                siglas_pre = {}
                for s in siglas_db:
                    siglas_pre[s.nome_completo.upper().strip()] = s.abreviacao.upper().strip()

                # Substituição atômica: atribui os novos dicionários de uma vez
                self.regras_limpeza = regras
                self.siglas_pre_processamento = siglas_pre
                self.ultima_atualizacao_regras = time.time()
            except Exception as e:
                print(f"Erro ao carregar regras de limpeza: {e}")

    def aplicar_limpeza_customizada(self, campo: str, texto: str) -> str:
        """Remove termos customizados cadastrados pelo usuário para um campo específico."""
        if not texto:
            return ""
        
        campo = campo.lower()
        if campo not in self.regras_limpeza:
            return texto
        
        texto_limpo = str(texto).upper()
        for termo in self.regras_limpeza[campo]:
            # Regex para remover a palavra exata com boundaries
            pattern = r'\b' + re.escape(termo) + r'\b'
            texto_limpo = re.sub(pattern, '', texto_limpo)
        
        return re.sub(r'\s+', ' ', texto_limpo).strip()

normalization_service = NormalizationService()
