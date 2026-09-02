# Catalogo V4 - Core Architecture & Standards

Esta skill documenta a arquitetura central do **Catalogo V4 (Gerenciador de Peças)**. Qualquer alteração nos arquivos listados aqui deve seguir critérios rigorosos de impacto global, garantindo que melhorias para um provedor não quebrem a lógica de outros.

## Arquivos Core (Sensíveis)

### 1. `backend/app/services/normalization_service.py`
- **Função:** Extração técnica de motorização, cilindrada, válvulas e combustíveis.
- **Regra de Ouro:** O regex de motorização deve ser capaz de lidar com cilindradas simples (`1.0`) e compostas (`1.0/1.3`), preservando ranges para evitar agrupamentos errôneos.
- **Impacto:** Afeta a "chave de agrupamento" de todas as peças.

### 2. `backend/app/services/automaker_service.py`
- **Função:** Identificação e tradução de montadoras e modelos via Master Catalog (JSON/FIPE).
- **Regra de Ouro:** Deve priorizar a detecção por substring (primeira palavra) para resolver casos como "COURIER ROCAM" -> "FORD".
- **Impacto:** Define a marca que aparece na coluna principal da tabela.

### 3. `backend/app/services/text_service.py`
- **Função:** Limpeza de strings, aplicação de siglas e mesclagem de anos.
- **Regra de Ouro:** As siglas devem ser aplicadas de forma contextual para evitar substituições indesejadas em nomes de modelos.
- **Impacto:** Visual final dos textos e ranges de anos no frontend.

### 4. `backend/app/providers/base_provider.py`
- **Função:** Classe base para todos os provedores. Define a estrutura do `formatar_resultado`.
- **Regra de Ouro:** Novos campos devem ser adicionados aqui primeiro para garantir que todos os provedores os suportem.

### 5. `backend/app/services/search_service.py`
- **Função:** Orquestração de buscas, cache e agrupamento (`_agrupar_por_veiculo`).
- **Regra de Ouro:** O agrupamento deve sempre considerar `marca`, `veiculo`, `modelo` e `motor` como chaves primárias.

## Padrões de Nomenclatura e UI
- **Nome do Sistema:** Catalogo V4 / Gerenciador de Peças.
- **Estética:** Premium, Dark Mode, Toasts Globais para feedback, Modais Customizados (ConfirmModal) para ações críticas.
- **Feedback:** Nunca usar `alert()` ou `confirm()` nativos do navegador. Utilizar sempre o sistema de `toast` e `ConfirmModal`.

## Workflow de Alteração
1. **Problema Específico:** Resolver no arquivo do provedor (`{nome}_provider.py`).
2. **Evolução Técnica:** Resolver nos arquivos Core listados acima, após validar impacto em múltiplos provedores.
