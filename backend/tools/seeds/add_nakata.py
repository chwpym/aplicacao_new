import json
from app.database import SessionLocal
from app.models import models


def add_nakata_provider():
    db = SessionLocal()
    try:
        # 1. Registro do Provedor
        exists = (
            db.query(models.Provedor)
            .filter(models.Provedor.nome == "Nakata")
            .first()
        )
        if exists:
            print("Provedor Nakata já existe. Atualizando...")
            nkt = exists
        else:
            nkt = models.Provedor(nome="Nakata", slug="nakata", ativo=True)
            db.add(nkt)

        nkt.tipo = "nakata"
        nkt.url = "https://www.catalogonakata.com.br"
        nkt.headers = json.dumps({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        # Configura Labels para o Workspace
        mapeamento = {
            "labels": {
                "veiculo": "Montadora",
                "modelo": "Veículo",
                "versao": "Modelo / Versão",
                "motor": "Motor",
                "posicao": "Posição",
                "lado": "Lado",
                "direcao": "Direção",
                "referencias": "Referências Cruzadas",
                "observacao": "Observações",
            }
        }
        nkt.mapeamento = json.dumps(mapeamento)
        db.commit()
        print("Provedor Nakata cadastrado com sucesso!")

    except Exception as e:
        print(f"Erro ao cadastrar: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_nakata_provider()
