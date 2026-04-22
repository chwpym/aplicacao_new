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
    import time
    start_time = time.time()
    
    # [PLACEHOLDER] Registro de Auditoria SaaS: Logar quem buscou o quê
    # LogEvent(user_id=None, action="search", query=id_peca, providers=provedor_ids)
    print(f"[AUDIT] Iniciando busca global por: {id_peca}")

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

        # Injeta nome do provedor nos dados brutos para fallback de colunas
        for i, resp in enumerate(raw_respostas):
            if i < len(provedores_db):
                p_nome = provedores_db[i].nome.upper()
                for app in resp:
                    app["provedor"] = p_nome

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
                "versao",
                "motor",
                "configuracao_motor",
                "observacao",
                "sistema_freio",
                "posicao",
                "lado",
                "direcao",
            ]:
                val = app.get(campo, "")
                if not val:
                    continue

                # 1. Aplicar Siglas Contextuais (Substring Inteligente/Boundary)
                val_upper = val.upper().strip()
                if campo in siglas_map:
                    app[campo] = text_service.aplicar_siglas_avancado(val_upper, siglas_map[campo])
                else:
                    app[campo] = val_upper

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
    # [PLACEHOLDER] Analytics: Tempo de resposta total
    duration = time.time() - start_time
    print(f"[METRICS] Busca por {id_peca} concluída em {duration:.2f}s com {len(todas_aplicacoes)} resultados.")

    return _agrupar_por_veiculo(todas_aplicacoes)


async def buscar_detalhes(db: Session, provedor_id: int, codigo_peca: str):
    """
    Busca detalhes técnicos e imagens de uma peça específica em um provedor.
    """
    provedor_db = db.query(models.Provedor).filter(models.Provedor.id == provedor_id).first()
    if not provedor_db:
        return None
    
    provider = provider_factory.get_provider(provedor_db)
    if not provider:
        return None
    
    # Executa a busca de detalhes no provedor (pode ser Scraping ou API)
    return await provider.get_details(codigo_peca)


def _agrupar_por_veiculo(todas_aplicacoes: list[dict]) -> list[dict]:
    """
    Lógica interna para agrupar aplicações idênticas e mesclar ranges de anos.
    """
    extra_fields = ["observacao", "posicao", "lado", "direcao", "sistema_freio", "restricao", "apenas", "referencias"]
    agrupados = {}
    
    for app in todas_aplicacoes:
        # Agrupamento Relaxado (ignorando configuracao_motor para a chave primária)
        key = (
            app.get("marca", ""),
            app.get("veiculo", ""),
            app.get("modelo", ""),
            app.get("versao", ""),
            app.get("motor", ""),
        )

        if key not in agrupados:
            agrupados[key] = {**app, "anos": [], "configs": set()}
            for f in extra_fields:
                agrupados[key][f + "_set"] = set()
                
        # Popula os campos extras no set para não perder info no agrupamento
        for f in extra_fields:
            val = app.get(f)
            if val:
                if f == "referencias":
                    for ref_part in str(val).split(" | "):
                        if ref_part.strip():
                            agrupados[key][f + "_set"].add(ref_part.strip())
                else:
                    agrupados[key][f + "_set"].add(val)

        if app.get("ano_inicio") or app.get("ano_fim"):
            agrupados[key]["anos"].append((app.get("ano_inicio"), app.get("ano_fim")))
            
        if app.get("configuracao_motor"):
            agrupados[key]["configs"].add(app.get("configuracao_motor"))

    resultados_finais = []
    for key, data in agrupados.items():
        ano_ini, ano_fim = text_service.merge_year_ranges(data["anos"])
        data["ano_inicio"] = str(ano_ini) if ano_ini is not None else None
        data["ano_fim"] = str(ano_fim) if ano_fim is not None else None
        del data["anos"]
        
        # Mescla as configurações divergentes
        configs = [c for c in data["configs"] if c]
        data["configuracao_motor"] = " / ".join(sorted(configs)) if configs else ""
        del data["configs"]
        
        # Mescla extra_fields
        for f in extra_fields:
            if f + "_set" in data:
                f_items = [v for v in data[f + "_set"] if v]
                if f_items:
                    # Referências usa pipe padrão, o resto usa barra
                    joiner = " | " if f == "referencias" else " / "
                    data[f] = joiner.join(sorted(f_items))
                else:
                    data[f] = ""
                del data[f + "_set"]
            
        resultados_finais.append(data)

    return resultados_finais
