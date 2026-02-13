import asyncio
import json
from sqlalchemy.orm import Session
from app.models import models
from app.providers import provider_factory
from app.services import text_service
from app.services.cache_service import cache_service


async def buscar_em_todos(
    id_peca: str, db: Session, provedor_ids: list[int] = None, agrupar: bool = True
):
    """
    Orquestra a busca em múltiplos provedores com suporte a cache.
    """
    id_peca = id_peca.upper().strip()

    # 1. Verificar Cache (Dados Brutos)
    cache_key = f"search_raw:{id_peca}:{provedor_ids}"
    raw_respostas = cache_service.get(cache_key)

    if raw_respostas is None:
        # 2. Buscar provedores ativos
        query = db.query(models.Provedor).filter(models.Provedor.ativo == True)
        if provedor_ids:
            query = query.filter(models.Provedor.id.in_(provedor_ids))

        provedores_db = query.all()

        # 3. Dispara buscas em paralelo
        tasks = []
        for p_db in provedores_db:
            provider = provider_factory.get_provider(p_db)
            if provider:
                tasks.append(provider.buscar(id_peca))

        if not tasks:
            return []

        raw_respostas = await asyncio.gather(*tasks)

        # Salva dados brutos no cache
        cache_service.set(cache_key, raw_respostas)

    # 4. Carrega Siglas e Palavras para remover (Sempre atualizado)
    siglas_map = {}
    for s in db.query(models.Sigla).all():
        campo = s.campo or "marca"
        if campo not in siglas_map:
            siglas_map[campo] = {}
        siglas_map[campo][s.nome_completo.upper().strip()] = s.abreviacao

    palavras_remover = db.query(models.PalavraRemover).all()
    remover_map = {}
    for p in palavras_remover:
        if p.campo not in remover_map:
            remover_map[p.campo] = []
        remover_map[p.campo].append(p.palavra)

    # 5. Processamento e Normalização Dinâmica
    todas_aplicacoes = []
    for resp in raw_respostas:
        for app_orig in resp:
            # Trabalha em uma cópia para não sujar o cache com dados limpos
            app = app_orig.copy()

            # Processamento de Siglas e Limpeza de texto avançada
            for campo in [
                "marca",
                "veiculo",
                "modelo",
                "motor",
                "configuracao_motor",
                "observacao",
            ]:
                val = app.get(campo, "")
                if not val:
                    continue

                # 1. Aplicar Siglas Contextuais
                val_upper = val.upper().strip()
                if campo in siglas_map and val_upper in siglas_map[campo]:
                    app[campo] = siglas_map[campo][val_upper]

                # 2. Limpeza de texto (Remoção de palavras)
                if campo in remover_map:
                    app[campo] = text_service.remover_palavras_avancado(
                        app[campo], remover_map.get(campo, [])
                    )

            # Garantir campos obrigatórios para o schema do frontend
            for field in [
                "versao",
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

    # 6. Agrupamento por modelo/motor (Dinâmico)
    if not agrupar:
        return todas_aplicacoes

    return _agrupar_por_veiculo(todas_aplicacoes)


def _agrupar_por_veiculo(todas_aplicacoes: list[dict]) -> list[dict]:
    """
    Lógica interna para agrupar aplicações idênticas e mesclar ranges de anos.
    """
    agrupados = {}
    for app in todas_aplicacoes:
        key = (
            app["marca"],
            app["veiculo"],
            app["modelo"],
            app.get("versao", ""),
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
