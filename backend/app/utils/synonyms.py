# Dicionário central de apelidos para as montadoras mais comuns do mercado brasileiro.
# O Serviço de Montadoras (AutomakerService) utilizará este dicionário como fallback 
# antes de tentar o fuzzy matching contra a base oficial da FIPE.

AUTOMAKER_SYNONYMS = {
    "VW": "VOLKSWAGEN",
    "V.W.": "VOLKSWAGEN",
    "V.W": "VOLKSWAGEN",
    "VOLKS": "VOLKSWAGEN",
    "GM": "CHEVROLET",
    "G.M.": "CHEVROLET",
    "CHEVY": "CHEVROLET",
    "MB": "MERCEDES-BENZ",
    "MBB": "MERCEDES-BENZ",
    "M.B.": "MERCEDES-BENZ",
    "MERCEDES": "MERCEDES-BENZ",
    "MERCEDES BENZ": "MERCEDES-BENZ",
    "LR": "LAND ROVER",
    "LANDROVER": "LAND ROVER",
    "ALFA": "ALFA ROMEO",
    "CITROËN": "CITROEN",  # Remover acentuação no mapeamento cruzado pode facilitar
    "MITSUBISHI MOTORS": "MITSUBISHI",
    "HYUNDAI MOTORS": "HYUNDAI",
    "TOYOTA MOTORS": "TOYOTA",
    "HONDA MOTORS": "HONDA",
    "FIAT AUTOMOVEIS": "FIAT",
}

# Marcas genéricas ou de peças (não-montadoras de veículos FIPE)
# que devem ser preservadas no bloco de "Referências" em vez de associadas à OEM
TECHNICAL_BRANDS = [
    "ORIGINAL",
    "OEM",
    "BOSCH",
    "WEGA",
    "TSA",
    "VIEMAR",
    "FRAGA",
    "COFAP",
    "MONROE",
    "MAGNETI MARELLI",
    "MARELLI",
    "DELPHI",
    "NGK",
    "VALEO",
    "DENSO",
    "BROSOL",
    "MTE-THOMSON",
    "FRAM",
    "MANN",
    "MAHLE",
    "TECFIL",
    "VOX",
    "WIX",
    "AUTHOMIX",
    "LUBER-FINER",
    "INTERFIL",
    "JAPANPARTS",
    "FRANIG",
    "UFI",
    "HENGST",
    "PURFLUX"
]

# Palavras-chave técnicas de motor que devem ser movidas para a coluna de Configuração
ENGINE_KEYWORDS = {
    "VHC", "VHC-E", "VHCE", "MPFI", "SFI", "DOHC", "SOHC", "E-TORQ", "ETORQ",
    "MIVEC", "VVT", "VVTI", "TIVCT", "THP", "TSI", "TFSI", "ECONOFLEX", "FLEXPOWER",
    "MCE", "MCE2", "FIRE", "FIREFLY", "EVO", "ZETEC", "ROCAM", "SIGMA", "DURATEC",
    "AP", "CHT", "POWER", "AT", "EA111", "EA211", "K4M", "F4R", "H4M", "5N", 
    "C10NE", "C14SE", "C16SE", "C18XE", "111L", "E-TECH", "SCE", "H4K", "SMARTFIRE",
    "L3", "L4", "V6", "V8", "W12", "TURBO", "BITURBO", "SUPERCHARGER",
    "3CIL", "4CIL", "5CIL", "6CIL", "8CIL", "10CIL", "12CIL"
}

# Sinônimos de combustível para padronização
FUEL_SYNONYMS = {
    "GSL": "GASOLINA",
    "ALC": "ÁLCOOL",
    "GAS": "GASOLINA",
    "DSL": "DIESEL",
    "FLEXPOWER": "FLEX",
    "ECONOFLEX": "FLEX",
    "BIFUEL": "FLEX"
}

# Fallback de modelos ultra-comuns para deduzir montadora quando tudo mais falha.
# Editavel aqui sem precisar de deploy do AutomakerService.
KNOWN_MODELS_FALLBACK = {
    "FOX": "VW", "GOL": "VW", "SAVEIRO": "VW", "VOYAGE": "VW",
    "POLO": "VW", "PASSAT": "VW", "AMAROK": "VW",
    "CORSA": "GM", "CELTA": "GM", "ONIX": "GM", "CRUZE": "GM",
    "S10": "GM", "MONTANA": "GM", "TRACKER": "GM",
    "PALIO": "FIAT", "UNO": "FIAT", "STRADA": "FIAT",
    "SIENA": "FIAT", "BRAVO": "FIAT", "PUNTO": "FIAT",
    "TORO": "FIAT", "DOBLO": "FIAT", "MOBI": "FIAT",
    "FIESTA": "FORD", "KA": "FORD", "COURIER": "FORD",
    "ECOSPORT": "FORD", "RANGER": "FORD", "FOCUS": "FORD",
    "208": "PEUGEOT", "307": "PEUGEOT", "408": "PEUGEOT",
    "C3": "CITROEN", "C4": "CITROEN", "XSARA": "CITROEN",
    "CLIO": "RENAULT", "SANDERO": "RENAULT", "DUSTER": "RENAULT",
    "LOGAN": "RENAULT", "KWID": "RENAULT",
    "HB20": "HYUNDAI", "I30": "HYUNDAI", "TUCSON": "HYUNDAI",
    "CIVIC": "HONDA", "FIT": "HONDA", "CITY": "HONDA", "HR-V": "HONDA",
    "COROLLA": "TOYOTA", "HILUX": "TOYOTA", "RAV4": "TOYOTA",
    "ASX": "MITSUBISHI", "PAJERO": "MITSUBISHI", "L200": "MITSUBISHI",
}
