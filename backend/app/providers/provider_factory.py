import json
from app.providers.graphql_provider import GraphQLProvider
from app.providers.rest_provider import RESTProvider
from app.providers.ds_provider import DSProvider
from app.providers.generic_scraper_provider import GenericScraperProvider
from app.providers.bosch_provider import BoschProvider
from app.providers.autoexperts_provider import AutoExpertsProvider
from app.providers.mte_thomson_provider import MteThomsonProvider


def get_provider(config_model):
    """
    Retorna uma instância do provedor correto baseada no banco de dados.
    """
    config = {
        "id": config_model.id,
        "nome": config_model.nome,
        "url": config_model.url,
        "query": config_model.query,
        "headers": json.loads(config_model.headers) if config_model.headers else {},
        "login_required": config_model.login_required,
        "username": config_model.username,
        "password": config_model.password,
        "tipo": config_model.tipo,
        "mapeamento": config_model.mapeamento,
    }

    if config["tipo"] == "graphql":
        return GraphQLProvider(config)
    elif config["tipo"] == "rest":
        return RESTProvider(config)
    elif config["tipo"] == "ds":
        return DSProvider(config)
    elif config["tipo"] == "scraper":
        return GenericScraperProvider(config)
    elif config["tipo"] == "bosch":
        return BoschProvider(config)
    elif config["tipo"] == "autoexperts":
        return AutoExpertsProvider(config)
    elif config["tipo"] == "viemar":
        from app.providers.viemar_provider import ViemarProvider

        return ViemarProvider(config)

    elif config["tipo"] == "cofap":
        from app.providers.cofap_provider import CofapProvider

        return CofapProvider(config)

    elif config["tipo"] == "mte_thomson":
        return MteThomsonProvider(config)

    elif config["tipo"] == "tecfil":
        from app.providers.tecfil_provider import TecfilProvider

        return TecfilProvider(config)

    elif config["tipo"] == "ima":
        from app.providers.ima_provider import IMAProvider
        return IMAProvider(config)

    elif config["tipo"] == "tsa":
        from app.providers.tsa_provider import TSAProvider
        return TSAProvider(config)

    return None
