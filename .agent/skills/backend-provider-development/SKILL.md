---
name: backend-provider-development
description: Guia para criar, implementar e registrar novos provedores (classes Python) no backend.
---

# Backend Provider Development

Esta skill detalha como expandir o sistema com novas fontes de dados.

## 1. Criando a Classe do Provedor
Todos os provedores devem herdar de `BaseProvider` e ser salvos em `backend/app/providers/`.

```python
from app.providers.base_provider import BaseProvider

class MeuNovoProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        self.headers = { "User-Agent": "..." }

    async def buscar(self, part_id):
        # Lógica de request usando self.client (httpx)
        # Extração de dados
        return [self.formatar_resultado(v) for v in resultados]
```

## 2. Padronização de Retorno (Smart Mapping)
O `BaseProvider.formatar_resultado()` é inteligente e aceita diversos nomes de chaves (sinônimos) para preencher os campos do Frontend. O desenvolvedor deve retornar um dicionário com os dados brutos; o sistema cuidará da normalização (Upper Case, limpeza Wega, extração de anos e combustíveis).

| Campo Final | Chaves Aceitas no Raw Data (Sinônimos) | Descrição |
| :--- | :--- | :--- |
| **Marca Peça** | `marca_peca`, `marca`, `provedor` | Marca da peça (ex: NAKATA, COFAP) |
| **Cód. Peça** | `codigo` | Código do fabricante |
| **Montadora** | `montadora`, `brand` | A marca do veículo (**CHEVROLET**, **GM**) |
| **Veículo** | `modelo`, `name` | O nome do carro (**CELTA**, **CORSA**) |
| **Versão** | `versao`, `model`, `version` | Versão/Detalhe (**SPIRIT**, **LIFE**) |
| **Motor** | `motor`, `engineName` | Cilindrada e Válvulas (**1.0 8V**) |
| **Config.** | `configuracao_motor` | Siglas técnicas e combustível (**VHC FLEX**) |

> [!CAUTION]
> **NÃO USE A CHAVE `veiculo` PARA MARCA**: Historicamente, a chave `veiculo` causou inversão de colunas. Use sempre `montadora` para a marca e `modelo` para o nome do carro. O `BaseProvider` possui um **Master Catalog (DuckDB)** que validará se o que você enviou é realmente uma marca FIPE ou um modelo trocado, corrigindo automaticamente se necessário.

## 3. Inteligência de Normalização (Master Catalog)
O sistema utiliza o **DuckDB** com dados da FIPE para garantir a integridade:
- **Maker Guard**: Valida se a Montadora informada existe. Se você enviar "CELTA" na montadora, o sistema detectará que é um modelo da "GM" e fará o swap automático.
- **Resíduo de Motor**: O `NormalizationService` remove termos como "VHC", "MPFI" e "FLEX" da coluna de motor e os move para a coluna de configuração, mantendo a busca padronizada.

## 4. Registro e Ativação
1. Adicione a classe ao diretório `backend/app/providers/`.
2. Registre o novo tipo no `ProviderFactory` em `backend/app/providers/provider_factory.py`.
3. Ative o provedor no banco de dados oficial `backend/catalogo.db` (tabela `provedores`).


## 5. Arquitetura de Busca em 2 Níveis (Discovery-Hydration)
Para sites complexos onde a lista de resultados não traz todos os dados técnicos:
1.  **Discovery:** Captura o ID interno ou a URL da peça no site.
2.  **Hydration:** Realiza uma segunda requisição para a página de detalhes para extrair Referências OE e Fichas Técnicas.
3.  **Performance:** Use `asyncio.gather` para hidratar múltiplos itens se necessário, mas prefira hidratar apenas o primeiro se as referências forem globais para o código.
## 6. Padrões Avançados de Scraping (HTML)

Para provedores que extraem dados de tabelas HTML (Web Scraping), utilize o padrão de **Mapeamento Dinâmico de Colunas**. Isso evita quebras se o fabricante mudar a ordem das colunas ou adicionar novas.

### Dynamic Column Mapping (O "Padrão Nakata")
1.  **Discovery de Cabeçalhos:** No `buscar()`, leia o `<thead>` primeiro para identificar o índice de cada coluna.
2.  **Helper `get_val`:** Utilize uma função auxiliar para buscar o valor pelo nome da coluna, tratando `colspan` e ausência de campos.

```python
# Exemplo de implementação resiliente
headers = [{"label": th.text.lower(), "idx": i} for i, th in enumerate(soup.select("thead th"))]

def get_field(cells, target):
    for h in headers:
        if target in h["label"]:
            return cells[h["idx"]].text.strip()
    return "" # Retorno seguro se a coluna não existir
```

### Boas Práticas:
- **Fallback de Código:** Se o código não estiver na tabela, tente extrair do `<h1>` ou `title` da página.
- **Normalização de Anos:** Converta formatos como `01/94` para `1994` usando regex no provedor antes de enviar para o `formatar_resultado`.
- **User-Agent:** Sempre utilize um User-Agent de navegador moderno para evitar bloqueios (403 Forbidden).
## 7. Infraestrutura de Dados e Banco de Dados Único

Para evitar problemas de dessincronização e duplicidade, o sistema utiliza um **Banco de Dados Único e Centralizado**.

- **Caminho Oficial:** `backend/catalogo.db`
- **Configuração de Conexão:** Localizada em `backend/app/database.py`.
- **Regra de Ouro:** Nunca utilize caminhos relativos como `./catalogo.db`. Utilize sempre caminhos absolutos calculados em tempo de execução para garantir que o banco seja aberto corretamente, independente de onde o servidor ou script seja disparado.

### Como o caminho é resolvido no código:
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/app
PROJECT_ROOT = os.path.dirname(BASE_DIR) # backend
DB_PATH = os.path.join(PROJECT_ROOT, "catalogo.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
```
