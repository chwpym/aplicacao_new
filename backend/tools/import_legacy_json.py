import json
import os
import sys

# Adiciona o diretório atual ao path para importar app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.models import PalavraRemover, Sigla

def import_data():
    json_dir = r"d:\Dev\aplicacao_new\JSON"
    db = SessionLocal()
    
    try:
        # 1. Importar Palavras de Remoção
        palavras_path = os.path.join(json_dir, "palavras_remover.json")
        with open(palavras_path, 'r', encoding='utf-8') as f:
            palavras_data = json.load(f)
            
            # Limpa palavras atuais para evitar duplicados ou conflitos com a vontade do usuário
            db.query(PalavraRemover).delete()
            
            count_p = 0
            for campo, lista in palavras_data.items():
                for palavra in lista:
                    new_p = PalavraRemover(palavra=palavra, campo=campo)
                    db.add(new_p)
                    count_p += 1
            print(f"Importadas {count_p} palavras de remoção.")

        # 2. Importar Siglas
        siglas_path = os.path.join(json_dir, "siglas.json")
        with open(siglas_path, 'r', encoding='utf-8') as f:
            siglas_data = json.load(f)
            
            # Limpa siglas atuais
            db.query(Sigla).delete()
            
            count_s = 0
            for original, abreviacao in siglas_data.items():
                new_s = Sigla(nome_completo=original, abreviacao=abreviacao)
                db.add(new_s)
                count_s += 1
            print(f"Importadas {count_s} siglas.")

        db.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro durante a migração: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
