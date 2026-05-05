import os
import json
import duckdb
from typing import Dict, List, Tuple
from thefuzz import process
from app.services.logging_service import logger
from app.utils.synonyms import AUTOMAKER_SYNONYMS

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "automakers_catalog.json")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".automakers.duckdb")

class AutomakerService:
    _instance = None
    _catalog = {}
    _model_to_brand = {}
    _brands = []
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomakerService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Carrega o catálogo JSON mestre e prepara o DuckDB como fallback."""
        # 1. Carregar JSON (Prioridade 1 - Performance e Estabilidade)
        try:
            if os.path.exists(CATALOG_PATH):
                with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._catalog = data.get("catalog", {})
                    
                self._brands = list(self._catalog.keys())
                self._model_to_brand = {}
                
                for brand, models in self._catalog.items():
                    for model in models:
                        self._model_to_brand[model.upper()] = brand.upper()
                
                # Guarda a data da última atualização para exibir na interface
                self._last_update = data.get("last_update", "N/A")
                
                logger.info("DATABASE", f"Master Catalog JSON carregado: {len(self._brands)} marcas e {len(self._model_to_brand)} modelos.")
        except Exception as e:
            logger.error("DATABASE", f"Erro ao carregar JSON: {e}")

        # 2. Preparar DuckDB (Fallback / Segurança Profunda)
        try:
            if os.path.exists(DB_PATH):
                # Abre sempre em modo READ_ONLY para evitar travas de concorrência
                self._connection = duckdb.connect(DB_PATH, read_only=True)
                logger.info("DATABASE", "Segurança DuckDB ativada (Modo Leitura).")
        except Exception as e:
            logger.warning("DATABASE", f"DuckDB de segurança indisponível: {e}")

    def reload(self):
        """Recarrega os dados do JSON (útil após sincronização)."""
        logger.info("DATABASE", "Recarregando catálogo Automaker (Manual)...")
        self._initialize()

    def add_model_manual(self, brand: str, model: str):
        """Adiciona um modelo manualmente ao JSON."""
        brand = brand.strip().upper()
        model = model.strip().upper()
        
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if brand not in data["catalog"]:
                data["catalog"][brand] = []
            
            if model not in data["catalog"][brand]:
                data["catalog"][brand].append(model)
                data["catalog"][brand].sort()
                
            with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.reload()
            return True
        except Exception as e:
            logger.error("DATABASE", f"Erro ao adicionar modelo manual: {e}")
            return False

    def remove_model_manual(self, brand: str, model: str):
        """Remove um modelo do JSON."""
        brand = brand.strip().upper()
        model = model.strip().upper()
        
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if brand in data["catalog"] and model in data["catalog"][brand]:
                data["catalog"][brand].remove(model)
                
                with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.reload()
                return True
            return False
        except Exception as e:
            logger.error("DATABASE", f"Erro ao remover modelo manual: {e}")
            return False

    def padronizar(self, nome_bruto: str) -> str:
        """Padroniza o nome da montadora."""
        if not nome_bruto:
            return ""
            
        nome_clean = nome_bruto.strip().upper()
        
        if nome_clean in AUTOMAKER_SYNONYMS:
            return AUTOMAKER_SYNONYMS[nome_clean]
            
        if nome_clean in self._brands:
            return nome_clean
            
        if self._brands:
            best_match, score = process.extractOne(nome_clean, self._brands)
            if score >= 90:
                return best_match

        if any(x in nome_clean for x in ["CHEVROLET", "GM ", "GM-"]) or nome_clean == "GM":
            return "GM"
        if any(x in nome_clean for x in ["VOLKSWAGEN", "VW "]) or nome_clean == "VW":
            return "VW"
            
        return nome_clean

    def validar_aplicacao(self, montadora_bruta: str, modelo_bruto: str) -> Tuple[str, str]:
        """
        Dedução inteligente de montadora em camadas:
        Camada 1: JSON Mestre (Memória) - Rápido e editável
        Camada 2: DuckDB (Banco de Dados) - Consulta SQL profunda
        Camada 3: Sinônimos e Fallbacks - Dicionário de emergência
        """
        m_clean = str(montadora_bruta).strip().upper()
        mod_clean = str(modelo_bruto).strip().upper()

        # --- CAMADA 1: JSON MESTRE ---
        if m_clean in self._brands or m_clean in AUTOMAKER_SYNONYMS:
            return self.padronizar(m_clean), mod_clean

        if mod_clean in self._model_to_brand:
            return self.padronizar(self._model_to_brand[mod_clean]), mod_clean
            
        if m_clean in self._model_to_brand:
            brand = self._model_to_brand[m_clean]
            return self.padronizar(brand), (mod_clean if mod_clean and mod_clean != m_clean else m_clean)

        # Melhora: Tenta ver se a primeira palavra da montadora bruta é um modelo conhecido
        # Ex: "COURIER ROCAM" -> "COURIER" -> FORD
        m_parts = m_clean.split()
        if m_parts and m_parts[0] in self._model_to_brand:
            brand = self._model_to_brand[m_parts[0]]
            return self.padronizar(brand), mod_clean

        # --- CAMADA 2: DUCKDB FALLBACK ---
        if self._connection:
            try:
                # Busca por montadora que na verdade é modelo
                res = self._connection.execute("""
                    SELECT m.nome 
                    FROM modelos mod
                    JOIN montadoras m ON mod.marca_id = m.id
                    WHERE mod.nome = ? OR mod.nome LIKE ? || ' %'
                    LIMIT 1
                """, [m_clean, m_clean]).fetchone()
                
                if res:
                    return self.padronizar(res[0]), mod_clean

                # Busca por modelo na coluna correta
                res_mod = self._connection.execute("""
                    SELECT m.nome 
                    FROM modelos mod
                    JOIN montadoras m ON mod.marca_id = m.id
                    WHERE mod.nome = ? OR mod.nome LIKE ? || ' %'
                    LIMIT 1
                """, [mod_clean, mod_clean]).fetchone()
                
                if res_mod:
                    return self.padronizar(res_mod[0]), mod_clean
            except:
                pass

        # --- CAMADA 3: SINÔNIMOS E FALLBACKS ---
        for brand in self._brands:
            if mod_clean.startswith(f"{brand} "):
                return self.padronizar(brand), mod_clean.replace(f"{brand} ", "").strip()

        # Fallback de emergência (Hardcoded para modelos ultra-comuns se tudo falhar)
        KNOWN_MODELS_FALLBACK = {
            "FOX": "VW", "GOL": "VW", "SAVEIRO": "VW", "VOYAGE": "VW",
            "CORSA": "GM", "CELTA": "GM", "ONIX": "GM",
            "PALIO": "FIAT", "UNO": "FIAT", "STRADA": "FIAT",
            "FIESTA": "FORD", "KA": "FORD", "COURIER": "FORD",
            "208": "PEUGEOT", "C3": "CITROEN"
        }
        if mod_clean in KNOWN_MODELS_FALLBACK:
            return KNOWN_MODELS_FALLBACK[mod_clean], mod_clean

        return self.padronizar(m_clean), mod_clean

# Singleton handler
automaker_service = AutomakerService()
