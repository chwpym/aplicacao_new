import sys
import os

# PYTHONPATH já deve estar configurado, mas vamos garantir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SessionLocal
from app.models import models

def cleanup():
    db = SessionLocal()
    try:
        # 1. Desativar o 'TUBA' antigo (que não é o 'tubacabos')
        tuba_antigo = db.query(models.Provedor).filter(
            models.Provedor.nome == "TUBA",
            models.Provedor.slug != "tubacabos"
        ).first()
        
        if tuba_antigo:
            print(f"Desativando provedor antigo: {tuba_antigo.nome} (ID: {tuba_antigo.id})")
            tuba_antigo.ativo = False
            tuba_antigo.nome = "TUBA (INATIVO)"
            db.commit()
            print("Sucesso.")
        else:
            print("TUBA antigo não encontrado ou já desativado.")
            
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
