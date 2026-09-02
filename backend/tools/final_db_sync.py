import sqlite3
import os
import json

# Caminho absoluto para o banco oficial
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "catalogo.db"))

def final_fix():
    print(f"Limpando e sincronizando banco oficial: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Desativar o 'TUBA' antigo
        cursor.execute("UPDATE provedores SET ativo = 0, nome = 'TUBA (INATIVO)' WHERE nome = 'TUBA' AND slug != 'tubacabos'")
        
        # 2. Garantir que as marcas Busca na Rede estão com o tipo correto
        marcas_busca_na_rede = [
            ("TUBA CABOS", "tubacabos"),
            ("SAMPEL", "sampel"),
            ("TC CHICOTES", "tcchicotes")
        ]
        
        for nome, slug in marcas_busca_na_rede:
            mapeamento = json.dumps({"brand_slug": slug})
            # Tenta atualizar
            cursor.execute("""
                UPDATE provedores 
                SET tipo = 'busca_na_rede', mapeamento = ?, ativo = 1 
                WHERE slug = ?
            """, (mapeamento, slug))
            
            if cursor.rowcount == 0:
                # Se não existir, cria (mas deve existir pois já rodamos seed antes)
                print(f"Aviso: {nome} não encontrado para atualizar, criando...")
                url = f"https://buscanarede.com.br/{slug}"
                cursor.execute("""
                    INSERT INTO provedores (nome, slug, url, tipo, ativo, mapeamento)
                    VALUES (?, ?, ?, 'busca_na_rede', 1, ?)
                """, (nome, slug, url, mapeamento))

        conn.commit()
        print("Sincronização concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro na sincronização: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    final_fix()
