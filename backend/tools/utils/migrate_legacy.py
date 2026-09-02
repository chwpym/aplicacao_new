import sqlite3
import json
import os

def migrate():
    # Caminhos dos arquivos legados
    legacy_path = r'C:\Users\Estoque_Original\Desktop\APLICAÇÃO'
    db_path = r'd:\Dev\aplicacao_new\backend\catalogo.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Migrar Provedores
    try:
        with open(os.path.join(legacy_path, 'provedores.json'), 'r', encoding='utf-8') as f:
            provedores = json.load(f)
            for key, p in provedores.items():
                cursor.execute("SELECT id FROM provedores WHERE nome = ?", (p['nome'],))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO provedores (nome, url, tipo, ativo, headers, query)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        p['nome'],
                        p.get('url', ''),
                        p['tipo'],
                        p.get('ativo', True),
                        json.dumps(p.get('headers', {})),
                        p.get('query', '')
                    ))
        print("Provedores migrados!")
    except Exception as e:
        print(f"Erro ao migrar provedores: {e}")

    # 2. Migrar Siglas
    try:
        with open(os.path.join(legacy_path, 'siglas.json'), 'r', encoding='utf-8') as f:
            siglas = json.load(f)
            for s, r in siglas.items():
                cursor.execute("SELECT id FROM siglas WHERE nome_completo = ?", (s,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO siglas (nome_completo, abreviacao) VALUES (?, ?)", (s, r))
        print("Siglas migradas!")
    except Exception as e:
        print(f"Erro ao migrar siglas: {e}")

    # 3. Migrar Palavras de Remover
    try:
        with open(os.path.join(legacy_path, 'palavras_remover.json'), 'r', encoding='utf-8') as f:
            palavras = json.load(f)
            for category, words in palavras.items():
                for w in words:
                    cursor.execute("SELECT id FROM palavras_remover WHERE palavra = ? AND campo = ?", (w, category))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO palavras_remover (palavra, campo) VALUES (?, ?)", (w, category))
        print("Palavras de remoção migradas!")
    except Exception as e:
        print(f"Erro ao migrar palavras: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
