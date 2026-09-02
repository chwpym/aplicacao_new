import json
import sqlite3
import duckdb
import os
import sys

# Caminhos dos bancos
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
SQL_DB = os.path.join(BACKEND_DIR, "catalogo.db")
DUCK_DB = os.path.join(BACKEND_DIR, ".automakers.duckdb")

def import_state(backup_path):
    if not os.path.exists(backup_path):
        print(f"Erro: Caminho de backup não encontrado: {backup_path}")
        return

    print(f"--- Iniciando Restauração Total de: {backup_path} ---")

    # 1. Restaurar SQL Configs
    sql_json = os.path.join(backup_path, "sql_configs.json")
    if os.path.exists(sql_json):
        print("Restaurando configurações SQL...")
        try:
            with open(sql_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            conn = sqlite3.connect(SQL_DB)
            cursor = conn.cursor()
            
            for table, rows in data.items():
                print(f"   Limpando e populando tabela '{table}'...")
                cursor.execute(f"DELETE FROM {table}")
                if rows:
                    cols = list(rows[0].keys())
                    placeholders = ", ".join(["?"] * len(cols))
                    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
                    cursor.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
            
            conn.commit()
            conn.close()
            print("   [OK] Configurações SQL restauradas.")
        except Exception as e:
            print(f"   [ERRO] Falha ao restaurar SQL: {e}")

    # 2. Restaurar DuckDB
    duck_json = os.path.join(backup_path, "fipe_catalog.json")
    if os.path.exists(duck_json):
        print("Restaurando Master Catalog (DuckDB)...")
        try:
            with open(duck_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            conn_duck = duckdb.connect(DUCK_DB)
            
            print("   Limpando e populando 'montadoras'...")
            conn_duck.execute("DELETE FROM montadoras")
            conn_duck.executemany("INSERT INTO montadoras VALUES (?, ?, ?)", data["montadoras"])
            
            print("   Limpando e populando 'modelos'...")
            conn_duck.execute("DELETE FROM modelos")
            conn_duck.executemany("INSERT INTO modelos VALUES (?, ?, ?)", data["modelos"])
            
            conn_duck.close()
            print("   [OK] Master Catalog restaurado.")
        except Exception as e:
            print(f"   [ERRO] Falha ao restaurar DuckDB: {e}")

    print("\nRestauração concluída com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/import_system_state.py <caminho_da_pasta_de_backup>")
    else:
        import_state(sys.argv[1])
