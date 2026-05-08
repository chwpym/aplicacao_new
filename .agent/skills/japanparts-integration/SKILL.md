---
name: japanparts-integration
description: Conhecimento técnico sobre a integração com o catálogo REST da Japanparts.
---

# Japanparts Integration

## Visão Geral
A Japanparts (japanparts.com.br) é um fabricante de filtros automotivos. Seu catálogo utiliza uma **API REST pura** (sem necessidade de scraping) hospedada em `api.japanparts.com.br`.

## Arquitetura: Discovery → Hydration (4 chamadas paralelas)

### 1. Discovery: Código → part_id
```
GET https://api.japanparts.com.br/api/parts?filter[where][code]={CODIGO}
```
**Resposta:** Array com objeto contendo `id` (part_id numérico), `code`, `thumb`, `bar_code`, `part_subcategory_name`.

### 2. Hydration: 2 Chamadas Paralelas

#### Veículos (Aplicações)
```
GET https://api.japanparts.com.br/api/vehicles/findByPartId?partId={part_id}
```
**Retorna:** `data[]` com:
- `model` → Modelo do veículo (ONIX, TRACKER)
- `version` → Versão (1.0 12V TURBO FLEX) — pode ser `null`
- `engine` → Motor (CSS PRIME) — pode ser `null`
- `year_from` → ISO 8601 ("2019-01-01T00:00:00.000Z") — extrair primeiros 4 chars
- `year_to` → ISO 8601 ou `null` (veículo atual)
- `vehicleManufacturers.name` → Montadora (CHEVROLET)

#### Equivalências (Referências Cruzadas)
```
GET https://api.japanparts.com.br/api/part_equivalences/findall?partId={part_id}
```
**Retorna:** `data[]` com:
- `name` → Marca da referência (GM, TECFIL, MANN)
- `equivalence_code` → Código (55509268, PSL612)
- `original` → 1 = OE (Original Equipment), 0 = Aftermarket

#### Dimensões (Enriquecimento/Fallback)
```
GET https://api.japanparts.com.br/api/part_dimensions?filter[where][part_id]={part_id}
```
**Retorna:** Array com objeto contendo `weight`, `height`, `length`, `width`, `external_diam`, `internal_diam`, `screw_in`, `screw_out`.
Usado para enriquecer a ficha técnica (peso, diâmetros, roscas).

#### Imagens Extras (Enriquecimento/Fallback)
```
GET https://api.japanparts.com.br/api/part_images?filter[where][part_id]={part_id}
```
**Retorna:** Array com objetos contendo `thumb`. Usado como fallback se o discovery não trouxer imagem.

## Headers Obrigatórios (CORS)
```json
{
    "Origin": "https://japanparts.com.br",
    "Referer": "https://japanparts.com.br/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Accept": "application/json, text/plain, */*"
}
```

## Mapeamento para BaseProvider
| API Field | BaseProvider Key | Exemplo |
|---|---|---|
| `vehicleManufacturers.name` | `montadora` | CHEVROLET |
| `model` | `modelo` | ONIX |
| `version` | `motor` | 1.0 12V TURBO FLEX |
| `engine` | `configuracao_motor` | CSS PRIME |
| `year_from[:4]` | `ano_inicio` | 2019 |
| `year_to[:4]` | `ano_fim` | (vazio se null) |
| `config.nome` | `marca_peca` | JAPANPARTS (dinâmico) |

## Códigos de Teste Validados
- **FO313S** → 35 veículos, 7 montadoras (Asia Motors, KIA, Mazda, Nissan, Subaru, Suzuki, Massey Ferguson), 20 refs cruzadas
- **FOBR174S** → 4 veículos, 1 montadora (Chevrolet/GM), 5 refs cruzadas

## Notas Técnicas
- A marca da peça é obtida **dinamicamente** do `config.nome` — nunca chumbada no código
- **ATENÇÃO:** `version` na API = Motor (1.0 12V TURBO FLEX), `engine` na API = Config. Motor (CSS PRIME)
- Ambos campos podem ser `null` — sempre tratar com `(vehicle.get("field") or "").strip()`
- Imagens: prefixar com `https://static.japanparts.com.br` (**NÃO** `japanparts.com.br`)
- As equivalências `original=1` são exibidas primeiro nas referências
