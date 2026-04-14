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
