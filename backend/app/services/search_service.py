import asyncio
import json
import threading
import time
from sqlalchemy.orm import Session
from app.models import models
from app.providers import provider_factory
from app.services import text_service
from app.services.cache_service import cache_service

# Cache em memória para Siglas e Palavras a Remover (evita 50 queries SQLite por busca global)
_rules_lock = threading.Lock()
_cached_siglas_map: dict = {}
_cached_remover_map: dict = {}
_rules_last_load: float = 0.0


def _get_text_rules_cached(db: Session) -> tuple[dict, dict]:
    """Retorna (siglas_map, remover_map) usando cache em memória de 60 segundos."""
    global _cached_siglas_map, _cached_remover_map, _rules_last_load
    now = time.time()
    if now - _rules_last_load < 60 and (_cached_siglas_map or _cached_remover_map):
        return _cached_siglas_map, _cached_remover_map

    with _rules_lock:
        if time.time() - _rules_last_load < 60 and (_cached_siglas_map or _cached_remover_map):
            return _cached_siglas_map, _cached_remover_map

        siglas_map = {}
        for s in db.query(models.Sigla).all():
            campo = s.campo or "marca"
            if campo not in siglas_map:
                siglas_map[campo] = {}
            siglas_map[campo][s.nome_completo.upper().strip()] = s.abreviacao

        remover_map = {}
        for p in db.query(models.PalavraRemover).all():
            if p.campo not in remover_map:
                remover_map[p.campo] = []
            remover_map[p.campo].append(p.palavra)

        _cached_siglas_map = siglas_map
        _cached_remover_map = remover_map
        _rules_last_load = time.time()
        return _cached_siglas_map, _cached_remover_map


async def buscar_em_todos(
    id_peca: str, db: Session, provedor_ids: list[int] = None, agrupar: bool = True
):
    """
    Orquestra a busca em múltiplos provedores com suporte a cache.
    """
    start_time = time.time()
    
    # [PLACEHOLDER] Registro de Auditoria SaaS: Logar quem buscou o quê
    # LogEvent(user_id=None, action="search", query=id_peca, providers=provedor_ids)
    print(f"[AUDIT] Iniciando busca global por: {id_peca}")

    from app.services.normalization_service import normalization_service
    normalization_service.carregar_regras_db(db)

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

        # Salva dados brutos no cache (apenas se houver ao menos 1 resultado válido)
        if any(raw_respostas):
            cache_service.set(cache_key, raw_respostas)

    # 4. Carrega Siglas e Palavras para remover (Com cache em memória de 60s)
    siglas_map, remover_map = _get_text_rules_cached(db)

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
    Lógica interna para agrupar aplicações idênticas e mesclar ranges de anos,
    preservando a ordem original dos termos técnicos.
    """
    extra_fields = ["observacao", "posicao", "lado", "direcao", "sistema_freio", "restricao", "apenas", "referencias", "combustivel"]
    agrupados = {}
    
    for app in todas_aplicacoes:
        # Agrupamento Relaxado (ignorando configuracao_motor para a chave primária)
        key = (
            str(app.get("marca", "")),
            str(app.get("codigo", "")),
            str(app.get("veiculo", "")),
            str(app.get("modelo", "")),
            str(app.get("versao", "")),
            str(app.get("motor", "")),
            str(app.get("observacao", "")) if app.get("provedor") == "DAYCO" else ""
        )

        if key not in agrupados:
            agrupados[key] = {**app, "anos": [], "configs": []}
            for f in extra_fields:
                agrupados[key][f + "_list"] = []
                
        # Popula os campos extras preservando a ordem original (sem duplicatas)
        for f in extra_fields:
            val = app.get(f)
            if val:
                target_list = agrupados[key][f + "_list"]
                if f == "referencias":
                    for ref_part in str(val).split(" | "):
                        ref_clean = ref_part.strip()
                        if ref_clean and ref_clean not in target_list:
                            target_list.append(ref_clean)
                else:
                    if val not in target_list:
                        target_list.append(val)

        if app.get("ano_inicio") or app.get("ano_fim"):
            agrupados[key]["anos"].append((app.get("ano_inicio"), app.get("ano_fim")))
            
        cfg = app.get("configuracao_motor")
        if cfg and cfg not in agrupados[key]["configs"]:
            agrupados[key]["configs"].append(cfg)

    resultados_finais = []
    for key, data in agrupados.items():
        ano_ini, ano_fim = text_service.merge_year_ranges(data["anos"])
        data["ano_inicio"] = str(ano_ini) if ano_ini is not None else None
        data["ano_fim"] = str(ano_fim) if ano_fim is not None else None
        del data["anos"]
        
        # Mescla as configurações divergentes mantendo a ordem original
        configs = [c for c in data["configs"] if c]
        data["configuracao_motor"] = " / ".join(configs) if configs else ""
        del data["configs"]
        
        # Mescla extra_fields mantendo a ordem original
        for f in extra_fields:
            if f + "_list" in data:
                f_items = [v for v in data[f + "_list"] if v]
                if f_items:
                    # Referências usa pipe padrão, o resto usa barra
                    joiner = " | " if f == "referencias" else " / "
                    data[f] = joiner.join(f_items)
                else:
                    data[f] = ""
                del data[f + "_list"]
            
        resultados_finais.append(data)

    return resultados_finais
