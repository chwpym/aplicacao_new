import os
import duckdb
import httpx
from thefuzz import process
import logging

from app.utils.synonyms import AUTOMAKER_SYNONYMS

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".automakers.duckdb")

class AutomakerService:
    _instance = None
    _connection = None
    _cached_names = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomakerService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self._connection = duckdb.connect(DB_PATH)
            # Verifica se a tabela existe
            res = self._connection.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name = 'montadoras'"
            ).fetchone()[0]
            
            if res == 0:
                self._setup_db()
            
            self._load_cache()
        except Exception as e:
            logging.error(f"Erro ao inicializar duckdb: {e}")

    def _setup_db(self):
        logging.info("Carregando base da BrasilAPI FIPE...")
        self._connection.execute("""
            CREATE TABLE montadoras (
                id INTEGER PRIMARY KEY,
                nome VARCHAR,
                tipo VARCHAR
            )
        """)
        
        tipos = ['carros', 'caminhoes', 'motos']
        
        import httpx
        import asyncio
        
        # Como o backend é async-first mas o init pode ser síncrono, usaremos httpx Client síncrono para o init
        with httpx.Client(timeout=30.0) as client:
            for tipo in tipos:
                try:
                    url = f"https://brasilapi.com.br/api/fipe/marcas/v1/{tipo}"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data:
                            nome = item.get("nome", "").upper()
                            val = item.get("valor", 0)
                            
                            # Evita dupes entre carros/caminhões mantendo o primeiro
                            self._connection.execute("""
                                INSERT INTO montadoras (id, nome, tipo) 
                                SELECT ?, ?, ? 
                                WHERE NOT EXISTS (SELECT 1 FROM montadoras WHERE nome = ?)
                            """, [int(val), nome, tipo, nome])
                except Exception as e:
                    logging.error(f"Erro ao buscar marcas de {tipo}: {e}")

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
            # Score de corte confiável > 85
            if score >= 85:
                resultado = best_match

        # 4. Preferências de Exibição Interna (Overrides Específicos do Sistema)
        if "CHEVROLET" in resultado or "GM " in resultado or resultado == "GM" or "GM-" in resultado:
            return "GM"
            
        if "VOLKSWAGEN" in resultado or resultado == "VW":
            return "VW"
            
        return resultado

    def __del__(self):
        if self._connection:
            self._connection.close()

# Singleton handler
automaker_service = AutomakerService()
