import json
from app.database import SessionLocal
from app.models import models


def add_autoexperts_provider():
    db = SessionLocal()
    try:
        # 1. Registro do Provedor
        exists = (
            db.query(models.Provedor)
            .filter(models.Provedor.nome == "AutoExperts")
            .first()
        )
        if exists:
            print("Provedor AutoExperts já existe. Atualizando...")
            axp = exists
        else:
            axp = models.Provedor(nome="AutoExperts", slug="autoexperts", ativo=True)
            db.add(axp)

        axp.tipo = "autoexperts"
        axp.url = "https://api.autoexperts.parts/autexp/bff/v1/catalog/products"
        axp.headers = json.dumps(
            {"x-region": "br", "origin": "https://www.autoexperts.parts"}
        )

        # Configura Labels para o Workspace
        # Note que no frontend as chaves são as do schema padrão
        mapeamento = {
            "labels": {
                "veiculo": "Montadora",
                "modelo": "Veículo",
                "versao": "Modelo / Versão",
                "motor": "Motor",
                "configuracao_motor": "Combustível / Detalhes",
                "referencias": "Referências OE / Cruzadas",
            }
        }
        axp.mapeamento = json.dumps(mapeamento)
        db.commit()
        print("Provedor AutoExperts cadastrado com sucesso!")

        # 2. Garantir Siglas/Marcas
        siglas_to_add = [
            ("NAKATA", "NK"),
            ("FREMAX", "FRX"),
            ("CONTROIL", "CTR"),
            ("FRAS-LE", "FRL"),
            ("AUTOEXPERTS", "AXP"),
        ]

        for nome_raw, abreviacao in siglas_to_add:
            sigla_exists = (
                db.query(models.Sigla)
                .filter(models.Sigla.abreviacao == abreviacao)
                .first()
            )
            if not sigla_exists:
                print(f"Adicionando sigla {nome_raw} -> {abreviacao}")
                sigla = models.Sigla(nome_completo=nome_raw, abreviacao=abreviacao)
                db.add(sigla)

        db.commit()
        print("Siglas processadas.")

    except Exception as e:
        print(f"Erro ao cadastrar: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_autoexperts_provider()
