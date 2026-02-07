import json
from app.providers.graphql_provider import GraphQLProvider
from app.providers.rest_provider import RESTProvider
from app.providers.ds_provider import DSProvider
from app.providers.generic_scraper_provider import GenericScraperProvider
from app.providers.bosch_provider import BoschProvider
from app.providers.autoexperts_provider import AutoExpertsProvider


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

    return None
