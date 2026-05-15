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

## 6. Ficha Técnica na Cópia (Clipboard)

Quando um provedor backend retorna dados em `ficha_tecnica` (dicionário chave/valor), o frontend deve exibir esses dados como um bloco de texto na cópia, **após a REFERÊNCIA DE SIMILARES**.

### Estrutura do Bloco
Cada provedor tem seu próprio bloco no final da função `copyToClipboard` em `clipboard.ts`. A ordem dos blocos é:

1. Texto dos resultados (linhas de aplicação)
2. `REFERÊNCIA DE SIMILARES :` (referências cruzadas agrupadas)
3. **Blocos de Ficha Técnica** (um por provedor, se houver dados)

### Provedores Já Registrados
| Provedor | Filtro | Título do Bloco |
|---|---|---|
| HIPPER FREIOS | `r.provedor === "HIPPER FREIOS"` | `MEDIDAS TÉCNICAS (HIPPER FREIOS):` |
| NOTUS | `r.provedor === "NOTUS"` | `FICHA TÉCNICA (NOTUS):` |
| MULTIQUALITÀ | `r.provedor === "MULTIQUALITA" \|\| r.marca_peca === "MULTIQUALITÀ"` | `FICHA TÉCNICA (MULTIQUALITÀ):` |
| AUTAFASTAR | `r.provedor === "AUTAFASTAR" \|\| r.marca === "AUTAFASTAR"` | `FICHA TÉCNICA (AUTAFASTAR):` |
| JAPANPARTS | `r.provedor === "JAPANPARTS" \|\| r.marca === "JAPANPARTS"` | `FICHA TÉCNICA (JAPANPARTS):` |
| LUK / FAG / INA | `schaefflerBrands.includes(r.provedor) \|\| .includes(r.marca)` | `FICHA TÉCNICA (LUK):` (dinâmico) |

### Template para Adicionar Novo Provedor
Inserir **ANTES** da linha `navigator.clipboard.writeText(text.trim());` no final da função:

```typescript
// Bloco de Ficha Técnica (Específico NOME_PROVEDOR)
const nomeResults = results.filter(r => 
  r.provedor?.toUpperCase() === "NOME_PROVEDOR" && r.ficha_tecnica
);
if (nomeResults.length > 0) {
  const ficha = nomeResults[0].ficha_tecnica;
  if (Object.keys(ficha).length > 0) {
    text += "\n\n...\nFICHA TÉCNICA (NOME_PROVEDOR):\n";
    Object.entries(ficha).forEach(([nome, valor]) => {
      if (valor === "-") {
        text += `${nome}\n`;
      } else {
        text += `${nome}: ${valor}\n`;
      }
    });
  }
}
```

### Regras Importantes
- O separador `\n\n...\n` é **obrigatório** antes do título. Ele é usado pelo sistema receptor para identificar seções.
- O valor `"-"` significa "sem valor" e deve ser renderizado **apenas como o nome** (sem os dois pontos).
- Se o provedor tem múltiplas marcas (ex: Schaeffler = LUK + FAG + INA), usar um array de brands e filtrar com `.includes()`.
- Sempre usar `.find()` ou `[0]` para pegar **apenas a primeira** ficha_tecnica (evita duplicatas na cópia).
- O título do bloco pode ser **dinâmico** (ex: `FICHA TÉCNICA (${brandLabel}):`) se o provedor tem múltiplas marcas.

### Checklist para Novo Provedor com Ficha Técnica
1. ✅ Backend retorna `ficha_tecnica: { "CAMPO": "VALOR" }` no resultado
2. ✅ Adicionar bloco no `clipboard.ts` antes do `navigator.clipboard.writeText`
3. ✅ Filtrar por `provedor` e/ou `marca` (case insensitive com `.toUpperCase()`)
4. ✅ Usar o template acima como base
5. ✅ Testar a cópia para garantir que o bloco aparece após os similares

