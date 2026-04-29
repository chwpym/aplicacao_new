import os
import duckdb
import httpx
from thefuzz import process
import logging
from app.services.logging_service import logger

from app.utils.synonyms import AUTOMAKER_SYNONYMS

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".automakers.duckdb")

class AutomakerService:
    _instance = None
    _connection = None
    _cached_names = []
    _cached_models = {}  # Cache de modelos por marca

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomakerService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self._connection = duckdb.connect(DB_PATH)
            # Verifica se as tabelas existem
            tables = self._connection.execute("SELECT table_name FROM information_schema.tables WHERE table_name IN ('montadoras', 'modelos')").fetchall()
            existing_tables = [t[0] for t in tables]
            
            if 'montadoras' not in existing_tables:
                self._setup_db()
            
            if 'modelos' not in existing_tables:
                self._setup_modelos()
            else:
                # Se a tabela existe mas está vazia, força a carga
                count = self._connection.execute("SELECT COUNT(*) FROM modelos").fetchone()[0]
                if count == 0:
                    self._setup_modelos()
            
            self._load_cache()
            logger.info("DATABASE", "Master Catalog (DuckDB) inicializado com sucesso.")
        except Exception as e:
            logger.error("DATABASE", f"Erro ao inicializar duckdb: {e}")

    def _setup_db(self):
        logger.info("DATABASE", "Carregando base de montadoras da BrasilAPI FIPE...")
        self._connection.execute("CREATE TABLE IF NOT EXISTS montadoras (id INTEGER PRIMARY KEY, nome TEXT, tipo TEXT)")
        self._connection.execute("CREATE TABLE IF NOT EXISTS modelos (id INTEGER PRIMARY KEY, marca_id INTEGER, nome TEXT, FOREIGN KEY(marca_id) REFERENCES montadoras(id))")
        
        print("[AutomakerService] Carregando marcas FIPE...", flush=True)
        for tipo in ["carros", "motos", "caminhoes"]:
            try:
                url = f"https://brasilapi.com.br/api/fipe/marcas/v1/{tipo}"
                resp = httpx.get(url, timeout=15.0)
                if resp.status_code == 200:
                    marcas = resp.json()
                    for m in marcas:
                        self._connection.execute(
                            "INSERT OR IGNORE INTO montadoras (id, nome, tipo) VALUES (?, ?, ?)",
                            [int(m["valor"]), m["nome"].upper(), tipo]
                        )
            except Exception as e:
                logger.error("FIPE_API", f"Erro ao carregar marcas de {tipo}: {e}")

    def _setup_modelos(self):
        """Carrega todos os modelos da FIPE via BrasilAPI"""
        logger.info("FIPE_API", "Iniciando carga de modelos FIPE (Master Catalog)...")
        
        # Pega as marcas do DB com o tipo correspondente
        montadoras = self._connection.execute("SELECT id, nome, tipo FROM montadoras").fetchall()
        total_marcas = len(montadoras)
        processed = 0
        
        with httpx.Client(timeout=30.0) as client:
            for m_id, m_nome, tipo in montadoras:
                try:
                    # Se o tipo estiver vazio (marcas legadas), assume carros
                    tipo = tipo or "carros"
                    
                    # Endpoint correto: /fipe/veiculos/v1/{tipo}/{codigoMarca}
                    url = f"https://brasilapi.com.br/api/fipe/veiculos/v1/{tipo}/{m_id}"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        modelos = resp.json()
                        if isinstance(modelos, list):
                            for mod in modelos:
                                mod_nome = mod.get("modelo", "").upper()
                                if mod_nome:
                                    self._connection.execute("INSERT INTO modelos (nome, marca_id) VALUES (?, ?)", [mod_nome, m_id])
                            
                            processed += 1
                            if processed % 10 == 0:
                                logger.info("FIPE_API", f"Progresso: {processed}/{total_marcas} marcas processadas...")
                except Exception as e:
                    logger.warning("FIPE_API", f"Falha na marca {m_nome} ({m_id}): {e}")
                    continue

    def _load_cache(self):
        if self._connection:
            resultados = self._connection.execute("SELECT nome FROM montadoras").fetchall()
            self._cached_names = [row[0] for row in resultados]

    def padronizar(self, nome_bruto: str) -> str:
        if not nome_bruto:
            return ""
            
        nome_clean = nome_bruto.strip().upper()
        resultado = nome_clean
        
        # 1. Verifica Dicionário Central (Sinônimos Básicos)
        if nome_clean in AUTOMAKER_SYNONYMS:
            resultado = AUTOMAKER_SYNONYMS[nome_clean]
            
        # 2. Busca Exata
        elif nome_clean in self._cached_names:
            resultado = nome_clean
            
        # 3. Fuzzy Matching (Aproximação) contra o Cache
        elif self._cached_names:
            best_match, score = process.extractOne(nome_clean, self._cached_names)
            if score >= 85:
                resultado = best_match

        # 4. Preferências de Exibição Interna
        if any(x in resultado for x in ["CHEVROLET", "GM ", "GM-"]) or resultado == "GM":
            return "GM"
        if any(x in resultado for x in ["VOLKSWAGEN", "VW "]) or resultado == "VW":
            return "VW"
            
        return resultado

    def validar_aplicacao(self, montadora_bruta: str, modelo_bruto: str):
        """
        A 'Mágica' do Master Catalog:
        Verifica se a montadora e o modelo estão invertidos ou se a montadora é na verdade um modelo.
        """
        m_clean = str(montadora_bruta).strip().upper()
        mod_clean = str(modelo_bruto).strip().upper()

        # Dicionário de emergência para modelos ultra-comuns caso a base FIPE falhe ou esteja incompleta
        KNOWN_MODELS_FALLBACK = {
            "FOX": "VW",
            "CROSS FOX": "VW",
            "CROSSFOX": "VW",
            "SPACE FOX": "VW",
            "SPACEFOX": "VW",
            "GOL": "VW",
            "SAVEIRO": "VW",
            "PARATI": "VW",
            "VOYAGE": "VW",
            "CORSA": "GM",
            "CELTA": "GM",
            "ASTRA": "GM",
            "VECTRA": "GM",
            "ONIX": "GM",
            "PRISMA": "GM",
            "PALIO": "FIAT",
            "UNO": "FIAT",
            "STRADA": "FIAT",
            "SIENA": "FIAT",
            "MOBI": "FIAT",
            "ARGO": "FIAT",
            "FIESTA": "FORD",
            "KA": "FORD",
            "ECOSPORT": "FORD",
            "RANGER": "FORD",
            "CIVIC": "HONDA",
            "FIT": "HONDA",
            "COROLLA": "TOYOTA",
            "HILUX": "TOYOTA",
            "HB20": "HYUNDAI",
            "TUCSON": "HYUNDAI",
            "SANDERO": "RENAULT",
            "LOGAN": "RENAULT",
            "DUSTER": "RENAULT",
            "KWID": "RENAULT",
            "CLIO": "RENAULT",
            "206": "PEUGEOT",
            "207": "PEUGEOT",
            "208": "PEUGEOT",
            "307": "PEUGEOT",
            "308": "PEUGEOT",
            "C3": "CITROEN",
            "C4": "CITROEN"
        }

        # 0. Verificação rápida em dicionário de emergência (antes mesmo de tentar DuckDB)
        if m_clean in KNOWN_MODELS_FALLBACK:
            return KNOWN_MODELS_FALLBACK[m_clean], (mod_clean if mod_clean and mod_clean != m_clean else m_clean)

        # 1. Caso: Swapped Columns (Montadora no Modelo e vice-versa)
        if (mod_clean in self._cached_names or mod_clean in AUTOMAKER_SYNONYMS) and \
           (m_clean not in self._cached_names and m_clean not in AUTOMAKER_SYNONYMS):
            return self.padronizar(mod_clean), m_clean

        # 2. Caso: Montadora reconhecida, vida que segue
        if m_clean in self._cached_names or m_clean in AUTOMAKER_SYNONYMS:
            return self.padronizar(m_clean), mod_clean

        # 3. Caso: Montadora vazia ou suspeita, mas Modelo contém a marca
        if not m_clean or len(m_clean) < 2:
            for syn, target in AUTOMAKER_SYNONYMS.items():
                if mod_clean.startswith(f"{syn} "):
                    return self.padronizar(target), mod_clean.replace(f"{syn} ", "").strip()

        # 4. Caso: A montadora informada é na verdade um MODELO conhecido no DuckDB
        res = self._connection.execute("""
            SELECT m.nome as marca_nome 
            FROM modelos mod
            JOIN montadoras m ON mod.marca_id = m.id
            WHERE mod.nome = ? OR mod.nome LIKE ? || ' %' OR ? = mod.nome
            LIMIT 1
        """, [m_clean, m_clean, m_clean]).fetchone()

        if res:
            return self.padronizar(res[0]), mod_clean

        return self.padronizar(m_clean), mod_clean

    def __del__(self):
        if self._connection:
            try:
                self._connection.close()
            except:
                pass

# Singleton handler
automaker_service = AutomakerService()
