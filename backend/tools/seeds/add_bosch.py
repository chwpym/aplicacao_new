import json
from app.database import SessionLocal
from app.models import models


def add_bosch_provider():
    db = SessionLocal()
    try:
        # Verifica se já existe
        exists = (
            db.query(models.Provedor).filter(models.Provedor.nome == "BOSCH").first()
        )
        if exists:
            print("Provedor BOSCH já existe. Atualizando...")
            bosch = exists
        else:
            bosch = models.Provedor(nome="BOSCH", slug="bosch", ativo=True)
            db.add(bosch)

        bosch.tipo = "bosch"
        bosch.url = "https://am.boschaftermarket.com/"

        # Configura Labels para o Workspace
        mapeamento = {
            "labels": {
                "configuracao_motor": "Designação / Medidas",
                "referencias": "Referências OE",
                "veiculo": "Fabricante",
            }
        }
        bosch.mapeamento = json.dumps(mapeamento)

        db.commit()
        print("Provedor BOSCH cadastrado com sucesso!")

        # Adicionar Sigla se não existir
        sigla_exists = (
            db.query(models.Sigla).filter(models.Sigla.abreviacao == "BOSCH").first()
        )
        if not sigla_exists:
            sigla = models.Sigla(nome_completo="ROBERT BOSCH LTDA", abreviacao="BOSCH")
            db.add(sigla)
            db.commit()
            print("Sigla BOSCH adicionada.")

    except Exception as e:
        print(f"Erro ao cadastrar: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_bosch_provider()
