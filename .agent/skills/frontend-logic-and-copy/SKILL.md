---
name: frontend-logic-and-copy
description: Lógica de processamento de resultados, agrupamento e padrões de cópia (clipboard) no Frontend.
---

# Frontend Logic & Copy Patterns

Esta skill explica como os resultados vindos do backend são tratados e transformados em texto para o usuário.

## 1. Processamento de Resultados
Os resultados chegam do backend como uma lista plana. O componente `Home.tsx` realiza as seguintes operações:
- **Parse de Anos**: Converte strings de datas em objetos comparáveis para ordenação.
- **Deduplicação**: Remove entradas idênticas vindas de diferentes provedores (Baseado em Marca, Veículo, Motor e Ano).

## 2. Lógica de Agrupamento (`agrupar`)
Quando o modo "Agrupar" está ativo:
- O sistema agrupa por `veiculo`.
- Dentro de cada veículo, as variações de `motor` e `ano` são combinadas.
- Isso reduz o tamanho da tabela, facilitando a leitura de catálogos muito extensos.

## 3. Padrões de Cópia (Clipboard)
A lógica de cópia foi extraída para o utilitário `frontend_new/src/utils/clipboard.ts`.
Existem três modos de cópia, todos integrados na função `copyToClipboard`:
- **Completa**: Copia todos os campos visíveis de todas as linhas.
- **Intermediária**: Copia Marca, Veículo, Motor e Ano (ignora notas técnicas longas).
- **Agrupada**: Segue a lógica visual do agrupamento por veículo.

**IMPORTANTE (Bloco REFERÊNCIA DE SIMILARES e Caixa Acima da Tabela):**
A lógica do frontend (`generateUniqueReferences` em `clipboard.ts`) que gera a caixa "Cross References" acima da tabela e o bloco no final da cópia **EXIGE** que as referências tenham um prefixo de marca.
- O formato obrigatório enviado pelo backend é `MARCA: CÓDIGO` ou `MARCA - CÓDIGO` (ex: `FIAT: 147442` ou `ORIGINAL: 545512E00PH`).
- **Atenção:** Se o provedor backend enviar apenas o número cru (ex: `545512E00PH`), o frontend **VAI IGNORÁ-LO SILENCIOSAMENTE** no agrupamento, e o código não aparecerá na caixa do topo nem na cópia final.
- Caso o provedor não forneça a marca da referência cruzada, o backend deve forçar um prefixo como `ORIGINAL: ` para garantir que a interface agrupe e exiba a informação.

Ao final de qualquer cópia, o sistema coleta todas as referências válidas e cria um bloco consolidado:
- Montadoras e `ORIGINAL`/`OEM` ficam no topo (prioridade).
- Marcas técnicas ficam abaixo em ordem alfabética.
- Códigos duplicados entre marcas são removidos automaticamente (deduplicação global).
```text
REFERÊNCIA DE SIMILARES :
ORIGINAL: 5U0615301C - 545512E00PH
VOLKSWAGEN: 5U0601301C - JZZ698302C
FRAS-LE: FLDI00096
FREMAX: BD5297
```

## 4. Estados de Visibilidade
Os checkboxes de visualização controlam o estado `visibleFields`. 
- Ao adicionar novos campos no Backend, eles **devem** ser incluídos neste estado no Frontend (`useCatalog.ts`) para que possam ser ocultados/mostrados seletivamente.
- A ordem das colunas no `COLUMN_CONFIG` do `DataTable.tsx` é: `marca`, `codigo`, `veiculo`, `modelo`, `versao`, `motor`, `configuracao_motor`, `combustivel`, `ano`, `observacao`, `posicao`, `lado`, `direcao`, `sistema_freio`, `restricao`, `apenas`, `referencias`, `acoes`.

## 5. Persistência de Preferências do Usuário
As preferências de visualização (quais colunas mostrar por padrão) devem ser persistidas localmente para evitar que o usuário precise reconfigurar a tabela a cada busca.

- **Mecanismo:** Utilizar `localStorage` via hook `useCatalog`.
- **Chave:** `catalog-visible-fields`.
- **Fallback:** Caso não exista nada salvo, utilizar a lista de `DEFAULT_VISIBLE_FIELDS` definida no código.
- **Reset:** O sistema deve oferecer um botão de "Restaurar Padrões" para limpar o `localStorage` e voltar à configuração de fábrica.

