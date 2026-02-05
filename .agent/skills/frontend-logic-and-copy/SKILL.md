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
Existem três modos de cópia, todos integrados no `copyToClipboard`:
- **Completa**: Copia todos os campos visíveis de todas as linhas.
- **Intermediária**: Copia Marca, Veículo, Motor e Ano (ignora notas técnicas longas).
- **Agrupada**: Segue a lógica visual do agrupamento por veículo.

**IMPORTANTE (Bloco ORIGINAL):**
Ao final de qualquer cópia, o sistema deve coletar todas as referências do tipo `Marca: Código` e criar um bloco consolidado:
```text
ORIGINAL:
GM  123456 - 789012
FORD  ABC-123
```

## 4. Estados de Visibilidade
Os checkboxes de visualização controlam o estado `visibleFields`. 
- Ao adicionar novos campos no Backend, eles **devem** ser incluídos neste estado no Frontend para que possam ser ocultados/mostrados seletivamente.
