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

---

## 7. Lógica Avançada de Cópia Alinhada (`clipboardTable.ts`)

Para atender às necessidades de colagem milimétrica em memos de sistemas ERP e Whatsapp com fontes proporcionais (onde um espaço `" "` ou hífen `"-"` tem tamanho físico diferente de uma letra `"M"` ou `"W"`), implementamos a engenharia proporcional de medição física no utilitário [clipboardTable.ts](file:///d:/Dev/aplicacao_new/frontend_new/src/utils/clipboardTable.ts).

### A. O Motor de Medição por HTML Canvas (2D Context)
Em vez de contar caracteres simples (que entorta fontes como *Segoe UI*, *Calibri*, *Tahoma* ou *Microsoft Sans Serif*), o sistema cria um elemento Canvas em memória e mede o tamanho em pixels dos blocos:
```typescript
const getProportionalWidth = (text: string, fontName: string, fontSize: number): number => {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return text.length * 8; // Fallback monoespaçado
  ctx.font = `${fontSize}pt "${fontName}"`;
  return ctx.measureText(text).width;
};
```

### B. Preenchimento de Espaços Físicos (`padProportional`)
Calcula dinamicamente a largura física que falta para atingir a coluna desejada e a preenche com o número exato de espaços proporcionalmente necessários para aquela fonte e tamanho:
```typescript
const padProportional = (
  text: string,
  targetPhysicalWidth: number,
  fontName: string,
  fontSize: number
): string => {
  // 1. Limpa o valor original
  // 2. Mede a largura em pixels do texto
  // 3. Se for maior que o limite da coluna, corta caractere por caractere
  // 4. Mede a largura física do caractere de espaço (" ") na mesma fonte/tamanho
  // 5. Divide a largura restante pela largura física do espaço
  // 6. Preenche com a quantidade calculada de caracteres de espaço
};
```

### C. Suporte a Múltiplos Formatos Simultâneos (Rich Clipboard)
O utilitário não copia apenas texto cru. Ele gera simultaneamente dois formatos e os insere na área de transferência através da API moderna `ClipboardItem`:
* **`text/plain`**: O texto estruturado com barras verticais `|`, medido pelo Canvas proporcional ou no padrão monoespaçado (conforme a configuração da fonte do ERP do usuário).
* **`text/html`**: Uma tabela HTML5 completa com estilos CSS inline (calibri, bordas suaves `#cbd5e1`, listras alternadas nas linhas com `#f8fafc`, cabeçalho destacado e espaçamentos internos). Ao ser colado em editores como Excel, Google Sheets, Outlook ou Word, o resultado vira uma tabela reativa com células nativas perfeitas.

### D. Regras Especiais da Tabela
1. **Deduplicação e Consolidação de Anos no Agrupamento**:
   Quando a opção "Agrupar" está ativada, a tabela condensa múltiplos anos de aplicação de um mesmo veículo e motor. Ela busca automaticamente o ano inicial mínimo (`Math.min(...starts)`) e o final máximo (`Math.max(...ends)`) e formata como `ano_inicio...ano_fim`, garantindo que não existam linhas duplicadas.
2. **Oclusão de Hifens (`hideDashesRow`)**:
   Devido ao fato de o caractere de hífen `-` ser extremamente fino em fontes do sistema Windows (como Segoe UI), a linha divisória horizontal `|---|---|` costuma quebrar e desalinhá-la visualmente. Quando `hideDashesRow` está ativa (`true` por padrão na produção), a linha de divisórias horizontais é omitida da saída em texto, mantendo apenas o cabeçalho e os dados perfeitamente retos.
3. **Consolidação Inteligente de Similares**:
   * Prioriza marcas montadoras conhecidas (ex: `VOLKSWAGEN`, `FORD`, `FIAT`) e chaves `ORIGINAL` / `OEM` no topo do bloco de referências.
   * Ordena marcas secundárias em ordem alfabética abaixo.
   * Remove códigos redundantes aplicando normalização de caracteres (excluindo pontos, traços e espaços).
4. **Indexação Integrada (IDX)**:
   * Gera um bloco `IDX:` no final do texto para mecanismos de indexação e buscas rápidas, incluindo marcas, motores, referências de montadoras e marcas técnicas de reposição de forma organizada.


