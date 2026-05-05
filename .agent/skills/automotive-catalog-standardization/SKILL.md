---
name: automotive-catalog-standardization
description: Diretrizes e padrões para normalização de dados automotivos (anos, combustíveis, montadoras e referências).
---

# Automotive Catalog Standardization

Esta skill reúne o conhecimento acumulado sobre como tratar a diversidade e a baixa qualidade dos dados em catálogos automotivos brasileiros.

## 1. Normalização de Montadoras (Automakers)
A normalização deve ser feita via `AutomakerService.padronizar()`.

### Marcas Técnicas Protegidas
Para evitar que algoritmos de *fuzzy matching* convertam marcas de peças em montadoras (ex: converter "FRAM" em "RAM"), utilizamos a lista `TECHNICAL_BRANDS` em `backend/app/utils/synonyms.py`.
- **Regra:** Se a marca identificada estiver nesta lista, a normalização de montadora deve ser ignorada para evitar "alucinações" do sistema.

## 2. Motor de Anos (Year Parsing)
Os catálogos utilizam formatos inconsistentes. O sistema deve normalizar para:
- **Padrão de Continuidade (`-->`):** Indica que o veículo ainda está em produção. Ex: `2024 -->` vira `ano_inicio: 2024` e `ano_fim: ""`.
- **Padrão de Faixa (`16 -- 25`):** Deve ser convertido para quatro dígitos. Ex: `16 -- 25` vira `2016` e `2025`.
- **Anos de 2 dígitos:** Devem ser expandidos inteligentemente (ex: `98` vira `1998`, `24` vira `2024`).

## 3. Inteligência de Combustível
Muitos catálogos omitem o campo de combustível, inserindo-o na descrição do modelo.
- **Estratégia:** Busca agressiva por palavras-chave (FLEX, DIESEL, GASOLINA, ALCOOL) em todas as fontes disponíveis: `versao`, `modelo` e `description`.
- **Prioridade:** O campo `combustivel` oficial (se houver) tem precedência, mas a extração por regex serve como rede de segurança.

## 4. Limpeza de Dados (Data Cleaning)
Provedores como Wega podem retornar caracteres de controle ou encodings quebrados.
- **Ação:** Utilizar a função `limpar_texto_wega` ou similar para remover caracteres invisíveis, espaços duplos e placeholders de encoding (ex: `\ufffd`).

## 5. Estrutura de Referências (OEM & Cross)
As referências são o coração da busca reversa.
- **Formato:** Sempre `Marca: Código`.
- **OEM Filtering:** Se a marca for "ORIGINAL" ou "OEM", o sistema deve tentar substituir pelo nome da montadora normalizada do veículo atual para melhorar a legibilidade.

## 6. Arquitetura de Busca em 2 Níveis (Padrão TSA/Scrapers)
Para sites complexos onde a lista de resultados não traz todos os dados técnicos:
1. **Passo 1 (Discovery):** Captura o ID interno da peça no site do fabricante.
2. **Passo 2 (Hydration):** Realiza uma segunda requisição (ou extração em segundo plano) para a página de detalhes para obter referências OEM, fichas técnicas e imagens extras.

## 7. Preservação de Ordem em Termos Técnicos
Ao normalizar strings de motores ou configurações (ex: `NormalizationService`), a **ordem original dos termos deve ser preservada** se eles forem semanticamente dependentes.

- **Regra de Ouro:** Nunca use ordenação alfabética automática (`sorted()`) em termos técnicos. 
- **Exemplo Crítico:** 
    - Correto: `FIRE EVO` (Nomenclatura oficial Fiat).
    - Errado: `EVO FIRE` (A ordenação alfabética destrói a semântica).
- **Implementação:** A extração deve seguir a posição original de cada termo encontrado na string bruta (`raw_text.find(keyword)`).
## 8. Localização do Banco de Dados Oficial

Para garantir a integridade dos dados e evitar duplicidade, o sistema utiliza um banco de dados centralizado.

- **Arquivo:** `backend/catalogo.db`
- **Importante:** Todos os scripts de manutenção e sementes (seeds) devem utilizar caminhos absolutos para acessar este arquivo, evitando a criação de arquivos `catalogo.db` fantasmas na raiz do projeto.
