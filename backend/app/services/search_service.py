import asyncio
from sqlalchemy.orm import Session
from app.models import models
from app.providers import provider_factory
from app.services import text_service


async def buscar_em_todos(
    id_peca: str, db: Session, provedor_ids: list[int] = None, agrupar: bool = True
):
    # Buscar provedores ativos
    query = db.query(models.Provedor).filter(models.Provedor.ativo == True)
    if provedor_ids:
        query = query.filter(models.Provedor.id.in_(provedor_ids))

    provedores_db = query.all()

    # 2. Carrega Siglas e Palavras para remover
    siglas = {
        s.nome_completo.upper(): s.abreviacao for s in db.query(models.Sigla).all()
    }
    palavras_remover = db.query(models.PalavraRemover).all()
    remover_map = {}
    for p in palavras_remover:
        if p.campo not in remover_map:
            remover_map[p.campo] = []
        remover_map[p.campo].append(p.palavra)

    # 3. Dispara buscas em paralelo
    tasks = []
    for p_db in provedores_db:
        provider = provider_factory.get_provider(p_db)
        if provider:
            tasks.append(provider.buscar(id_peca))

    if not tasks:
        return []

    respostas = await asyncio.gather(*tasks)

    # 4. Processamento de resultados
    todas_aplicacoes = []
    for resp in respostas:
        for app in resp:
            # Limpeza e padronização básica (sempre ocorre)
            marca_raw = app.get("marca", "").upper().strip()
            app["marca"] = siglas.get(marca_raw, marca_raw)

            for campo in [
                "veiculo",
                "modelo",
                "motor",
                "configuracao_motor",
                "observacao",
            ]:
                if app.get(campo):
                    app[campo] = text_service.remover_palavras_avancado(
                        app[campo], remover_map.get(campo, [])
                    )

            # Garantir campos obrigatórios para o schema
            for field in [
                "configuracao_motor",
                "sistema_freio",
                "observacao",
                "apenas",
                "restricao",
                "posicao",
                "lado",
                "direcao",
                "referencias",
            ]:
                if field not in app:
                    app[field] = ""

            todas_aplicacoes.append(app)

    if not agrupar:
        return todas_aplicacoes

    # 5. Agrupamento por modelo/motor
    agrupados = {}  # Chave: (marca, veiculo, modelo, motor, config_motor)
    for app in todas_aplicacoes:
        key = (
            app["marca"],
            app["veiculo"],
            app["modelo"],
            app["motor"],
            app["configuracao_motor"],
        )

        if key not in agrupados:
            agrupados[key] = {**app, "anos": []}

        if app.get("ano_inicio") or app.get("ano_fim"):
            agrupados[key]["anos"].append((app.get("ano_inicio"), app.get("ano_fim")))

    resultados_finais = []
    for key, data in agrupados.items():
        ano_ini, ano_fim = text_service.merge_year_ranges(data["anos"])
        data["ano_inicio"] = str(ano_ini) if ano_ini is not None else None
        data["ano_fim"] = str(ano_fim) if ano_fim is not None else None
        del data["anos"]
        resultados_finais.append(data)

    return resultados_finais
