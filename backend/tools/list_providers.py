import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SessionLocal
from app.models import models

def list_providers():
    db = SessionLocal()
    try:
        providers = db.query(models.Provedor).all()
        print(f"{'ID':<4} | {'Nome':<20} | {'Slug':<15} | {'Tipo':<15} | {'Ativo':<5}")
        print("-" * 65)
        for p in providers:
            print(f"{p.id:<4} | {p.nome:<20} | {p.slug:<15} | {p.tipo:<15} | {p.ativo:<5}")
    finally:
        db.close()

if __name__ == "__main__":
    list_providers()
