import json
import logging
import os
from sqlalchemy.orm import Session
from app.models import models

logger = logging.getLogger("db_seed")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SEED_FILE = os.path.join(DATA_DIR, "initial_seed.json")


def load_seed_data() -> dict:
    if not os.path.exists(SEED_FILE):
        logger.warning(f"[SEED] Arquivo de seed não encontrado em: {SEED_FILE}")
        return {}
    try:
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[SEED] Erro ao ler seed JSON: {e}")
        return {}


def auto_seed_db(db: Session, force: bool = False) -> dict:
    """
    Popula o banco de dados caso esteja vazio ou se force=True.
    Garante que em ambientes com disco efêmero (como Render), o banco
    sempre suba com os 64 provedores, siglas e configurações.
    """
    total_provedores = db.query(models.Provedor).count()

    if total_provedores > 0 and not force:
        logger.info(f"[SEED] Banco já possui {total_provedores} provedores. Auto-seed ignorado.")
        return {"status": "skipped", "message": f"Banco já populado com {total_provedores} provedores."}

    data = load_seed_data()
    if not data:
        return {"status": "error", "message": "Nenhum dado de seed encontrado."}

    logger.info(f"[SEED] {'Forçando recriação do' if force else 'Iniciando auto-seed no'} banco de dados...")

    stats = {}

    if force:
        # Limpar registros atuais
        db.query(models.Provedor).delete()
        db.query(models.Sigla).delete()
        db.query(models.PalavraRemover).delete()
        db.query(models.Configuracao).delete()
        db.query(models.ConfiguracaoImagem).delete()
        db.commit()

    # 1. Provedores
    if "provedores" in data and (total_provedores == 0 or force):
        provs = [models.Provedor(**row) for row in data["provedores"]]
        db.add_all(provs)
        stats["provedores"] = len(provs)

    # 2. Siglas
    if "siglas" in data and (db.query(models.Sigla).count() == 0 or force):
        siglas = [models.Sigla(**row) for row in data["siglas"]]
        db.add_all(siglas)
        stats["siglas"] = len(siglas)

    # 3. Palavras a remover
    if "palavras_remover" in data and (db.query(models.PalavraRemover).count() == 0 or force):
        palavras = [models.PalavraRemover(**row) for row in data["palavras_remover"]]
        db.add_all(palavras)
        stats["palavras_remover"] = len(palavras)

    # 4. Configurações gerais
    if "configuracoes" in data and (db.query(models.Configuracao).count() == 0 or force):
        configs = [models.Configuracao(**row) for row in data["configuracoes"]]
        db.add_all(configs)
        stats["configuracoes"] = len(configs)

    # 5. Configurações de imagem
    if "config_imagens" in data and (db.query(models.ConfiguracaoImagem).count() == 0 or force):
        cf_imgs = [models.ConfiguracaoImagem(**row) for row in data["config_imagens"]]
        db.add_all(cf_imgs)
        stats["config_imagens"] = len(cf_imgs)

    db.commit()
    logger.info(f"[SEED] Concluído com sucesso! Estatísticas: {stats}")
    return {"status": "success", "stats": stats}


def export_database_state(db: Session) -> dict:
    """Exporta o estado atual do banco em formato compatível com initial_seed.json"""
    provedores = [p.__dict__.copy() for p in db.query(models.Provedor).all()]
    siglas = [s.__dict__.copy() for s in db.query(models.Sigla).all()]
    palavras = [w.__dict__.copy() for w in db.query(models.PalavraRemover).all()]
    configs = [c.__dict__.copy() for c in db.query(models.Configuracao).all()]
    imagens = [i.__dict__.copy() for i in db.query(models.ConfiguracaoImagem).all()]

    for items in [provedores, siglas, palavras, configs, imagens]:
        for item in items:
            item.pop("_sa_instance_state", None)

    return {
        "provedores": provedores,
        "siglas": siglas,
        "palavras_remover": palavras,
        "configuracoes": configs,
        "config_imagens": imagens,
    }


def import_database_state(db: Session, data: dict) -> dict:
    """Importa e substitui estado do banco a partir de um dicionário JSON"""
    if "provedores" not in data:
        raise ValueError("JSON inválido: chave 'provedores' não encontrada.")

    # Limpar tabelas
    db.query(models.Provedor).delete()
    db.query(models.Sigla).delete()
    db.query(models.PalavraRemover).delete()
    db.query(models.Configuracao).delete()
    db.query(models.ConfiguracaoImagem).delete()
    db.commit()

    stats = {}

    if "provedores" in data:
        provs = [models.Provedor(**row) for row in data["provedores"]]
        db.add_all(provs)
        stats["provedores"] = len(provs)

    if "siglas" in data:
        siglas = [models.Sigla(**row) for row in data["siglas"]]
        db.add_all(siglas)
        stats["siglas"] = len(siglas)

    if "palavras_remover" in data:
        palavras = [models.PalavraRemover(**row) for row in data["palavras_remover"]]
        db.add_all(palavras)
        stats["palavras_remover"] = len(palavras)

    if "configuracoes" in data:
        configs = [models.Configuracao(**row) for row in data["configuracoes"]]
        db.add_all(configs)
        stats["configuracoes"] = len(configs)

    if "config_imagens" in data:
        cf_imgs = [models.ConfiguracaoImagem(**row) for row in data["config_imagens"]]
        db.add_all(cf_imgs)
        stats["config_imagens"] = len(cf_imgs)

    db.commit()
    return {"status": "success", "stats": stats}
