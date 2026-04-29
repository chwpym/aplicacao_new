import json
import sqlite3
import duckdb
import os
from datetime import datetime

# Caminhos dos bancos
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
SQL_DB = os.path.join(BACKEND_DIR, "catalogo.db")
DUCK_DB = os.path.join(BACKEND_DIR, ".automakers.duckdb")
BACKUP_DIR = os.path.join(BACKEND_DIR, "backups")

def export_state():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    
    if not os.path.exists(current_backup_dir):
        os.makedirs(current_backup_dir)

    print(f"--- Iniciando Exportação Total ({timestamp}) ---")

    # 1. Exportar SQLite (Provedores, Siglas, Limpeza)
    print("Exportando configurações SQL (Provedores/Siglas)...")
    try:
        conn = sqlite3.connect(SQL_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql_data = {}
        for table in ["provedores", "siglas", "palavras_remover"]:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            sql_data[table] = [dict(row) for row in rows]
        
        with open(os.path.join(current_backup_dir, "sql_configs.json"), "w", encoding="utf-8") as f:
            json.dump(sql_data, f, indent=4, ensure_ascii=False)
        conn.close()
        print(f"   [OK] {len(sql_data['provedores'])} provedores exportados.")
    except Exception as e:
        print(f"   [ERRO] Falha ao exportar SQL: {e}")

    # 2. Exportar DuckDB (Master Catalog)
    print("Exportando Master Catalog (DuckDB)...")
    try:
        conn_duck = duckdb.connect(DUCK_DB)
        
        # Exporta Montadoras
        montadoras = conn_duck.execute("SELECT * FROM montadoras").fetchall()
        # Exporta Modelos
        modelos = conn_duck.execute("SELECT * FROM modelos").fetchall()
        
        duck_data = {
            "montadoras": [list(m) for m in montadoras],
            "modelos": [list(m) for m in modelos]
        }
        
        with open(os.path.join(current_backup_dir, "fipe_catalog.json"), "w", encoding="utf-8") as f:
            json.dump(duck_data, f, indent=4, ensure_ascii=False)
        conn_duck.close()
        print(f"   [OK] {len(duck_data['montadoras'])} marcas e {len(duck_data['modelos'])} modelos exportados.")
    except Exception as e:
        print(f"   [ERRO] Falha ao exportar DuckDB: {e}")

    print(f"\nSucesso! Backup salvo em: {current_backup_dir}")
    return current_backup_dir

if __name__ == "__main__":
    export_state()
