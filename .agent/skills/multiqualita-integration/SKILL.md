---
name: multiqualita-integration
description: Conhecimento técnico especializado na extração resiliente de dados do catálogo Multiqualità e similares baseados em labels.
---

# Multiqualità Integration Patterns

Este guia documenta as estratégias de engenharia utilizadas para integrar o provedor Multiqualità, focando em resiliência e fidelidade de dados.

## 1. Parsing Baseado em Labels (Resiliência)
Em sites com estrutura DOM instável ou IDs dinâmicos, deve-se utilizar a técnica de **Ancoragem por Labels Textuais**.
- **Problema:** O elemento com o código pode estar em um ID que muda.
- **Solução:** Localizar o elemento de título (ex: "Características", "Referências") e navegar até o seu container irmão ou pai para extrair os valores.

```python
# Exemplo de busca por label
labels = soup.select(".label-class")
for label in labels:
    text = label.get_text().upper()
    if "REFER" in text:
        # Extrai os dados do container vizinho
        data = label.parent.select(".value-class")
```

## 2. Tratamento de Anos e Setas Unicode
Catálogos automotivos frequentemente utilizam caracteres unicode como setas (`→`, `⇾`, `➜`) para indicar intervalos de anos.
- **Regex Recomendado:** `r"(\d{4})\s*[^\d\s]{1,3}\s*(\d{4})?"`
- Este regex captura o ano inicial, ignora qualquer símbolo separador não-numérico de até 3 caracteres, e captura o ano final se existir.

## 3. Lógica de Motorização para Itens Técnicos
Para itens que não possuem motorização óbvia (Sensores, Bicos, Componentes Elétricos):
- **Política:** Manter a coluna `Motor` vazia (ou com traços) se o catálogo original não trouxer cilindradas (ex: 1.0, 2.0).
- **Evitar Fallbacks Abusivos:** Não preencher o campo `Motor` com a descrição da peça, a menos que seja estritamente necessário para diferenciação de aplicação.

## 4. Metadados e Ficha Técnica
- **Deduplicação de Labels:** Se uma característica não possui um par `Chave: Valor` (ex: apenas "115 AMPERES"), use o próprio texto como chave e um valor nulo ou "-" para manter a integridade da grade de resultados.
- **EAN:** Sempre buscar por labels como "BARRA" ou "CÓDIGO DE BARRAS" para popular a ficha técnica.

## 5. Padrões de Cópia (Clipboard)
Para garantir uma experiência premium, a Ficha Técnica deve ser anexada ao final do clipboard em um bloco separado:
- **Trigger:** Filtrar resultados pelo ID do provedor ou Marca Peça.
- **Formato:**
  ```text
  ...
  FICHA TÉCNICA (MARCA):
  Atributo 1: Valor
  Atributo 2: Valor
  ```

## 6. Referências Cruzadas (Similares)
- **Normalização:** Caso o catálogo forneça apenas o código sem a marca, prefixar como `SIMILAR: CÓDIGO`.
- Isso garante que o motor de unificação do Frontend consiga agrupar essas referências no resumo superior da tabela.
