import json
from app.providers.graphql_provider import GraphQLProvider
from app.providers.rest_provider import RESTProvider
from app.providers.ds_provider import DSProvider
from app.providers.generic_scraper_provider import GenericScraperProvider
from app.providers.bosch_provider import BoschProvider
from app.providers.autoexperts_provider import AutoExpertsProvider
from app.providers.mte_thomson_provider import MteThomsonProvider
from app.providers.notus_provider import NotusProvider


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

    elif config["tipo"] == "vox":
        from app.providers.vox_provider import VoxProvider

        return VoxProvider(config)

    elif config["tipo"] == "ima":
        from app.providers.ima_provider import IMAProvider
        return IMAProvider(config)

    elif config["tipo"] == "tsa":
        from app.providers.tsa_provider import TSAProvider
        return TSAProvider(config)

    elif config["tipo"] == "dayco":
        from app.providers.dayco_provider import DaycoProvider
        return DaycoProvider(config)

    elif config["tipo"] == "hipper_freios":
        from app.providers.hipperfreios_provider import HipperFreiosProvider
        return HipperFreiosProvider(config)

    elif config["tipo"] == "notus":
        return NotusProvider(config)

    elif config["tipo"] == "nakata":
        from app.providers.nakata_provider import NakataProvider
        return NakataProvider(config)

    elif config["tipo"] == "tubacabos":
        from app.providers.tubacabos_provider import TubaCabosProvider
        return TubaCabosProvider(config)
        
    elif config["tipo"] == "sampel":
        from app.providers.sampel_provider import SampelProvider
        return SampelProvider(config)
        
    elif config["tipo"] == "tcchicotes":
        from app.providers.tcchicotes_provider import TcChicotesProvider
        return TcChicotesProvider(config)

    elif config["tipo"] == "multiqualita":
        from app.providers.multiqualita_provider import MultiqualitaProvider
        return MultiqualitaProvider(config)

    elif config["tipo"] == "autafastar":
        from app.providers.autafastar_provider import AutafastarProvider
        return AutafastarProvider(config)

    elif config["tipo"] == "japanparts":
        from app.providers.japanparts_provider import JapanpartsProvider
        return JapanpartsProvider(config)

    elif config["tipo"] == "schaeffler":
        from app.providers.schaeffler_provider import SchaefflerProvider
        return SchaefflerProvider(config)

    elif config["tipo"] == "indisa_web":
        from app.providers.indisa_web_provider import IndisaWebProvider
        return IndisaWebProvider(config)

    elif config["tipo"] == "iguacu":
        from app.providers.iguacu_provider import IguacuProvider
        return IguacuProvider(config)

    elif config["tipo"] == "schadek":
        from app.providers.schadek_provider import SchadekProvider
        return SchadekProvider(config)

    elif config["tipo"] == "jahu":
        from app.providers.jahu_provider import JahuProvider
        return JahuProvider(config)

    elif config["tipo"] == "intermec":
        from app.providers.intermec_provider import IntermecProvider
        return IntermecProvider(config)

    elif config["tipo"] == "wega":
        from app.providers.wega_provider import WegaProvider
        return WegaProvider(config)

    elif config["tipo"] == "irb":
        from app.providers.irb_provider import IrbProvider
        return IrbProvider(config)

    elif config["tipo"] == "vetor":
        from app.providers.vetor_provider import VetorProvider
        return VetorProvider(config)

    return None

