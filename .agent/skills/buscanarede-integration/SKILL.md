---
name: buscanarede-integration
description: Diretrizes técnicas para integração com a plataforma Busca na Rede (TC Chicotes, Tuba, Sampel, etc.).
---

# Busca na Rede Platform Integration

Este guia documenta os padrões de engenharia para extrair dados da plataforma **Busca na Rede**, garantindo alta fidelidade e evitando poluição de SEO.

## 1. Estratégia de Extração (Hydration)
A plataforma gera metadados `og:description` automaticamente que costumam ser poluídos com repetições de palavras-chave.
- **Prioridade:** Sempre buscar pela tabela HTML estruturada (`table#aplicacoes` ou `.table-aplicacoes`).
- **Fallback:** Usar o `og:description` apenas se a tabela não estiver presente ou estiver vazia.
- **Diferenciação:** A tabela usa o separador `|` entre colunas, enquanto o metadado usa espaços múltiplos ou hífens.

## 2. Referências Cruzadas via AJAX
Muitas marcas (como Tuba Cabos) carregam referências em abas separadas via AJAX.
- **Padrão:** Procurar por links `<a>` com o atributo `data-remote`.
- **Endpoints Comuns:**
    - `/equivalences` (Referências de outras marcas)
    - `/oem` (Números originais da montadora)
- **Implementação:** Usar `asyncio.gather` para disparar as requisições para esses endpoints em paralelo e enriquecer o objeto `referencias`.

## 3. Limpeza de SEO e Repetições
A plataforma frequentemente repete a montadora e o modelo (ex: "FIAT FIAT FIAT PALIO PALIO").
- **Técnica:** Implementar deduplicação de palavras adjacentes idênticas no `_parse_application_block`.
- **Hífens:** Ignorar hífens soltos (`-`) que a plataforma usa como separadores visuais no texto corrido.

## 4. Normalização de Anos
- **Termo "TODOS":** Comum em marcas de chicotes e componentes universais. Deve ser mapeado para um intervalo amplo (ex: `1940` a `2026`) para garantir a exibição correta na grade.
- **Intervalos:** A plataforma usa `...` ou hífens para intervalos. Use o `NormalizationService.extrair_anos` para padronizar.

## 5. Formatação de Termos de Busca
Algumas marcas possuem padrões rígidos de código que o usuário pode ignorar ao digitar.
- **TC Chicotes:** O site exige o ponto (ex: `102.1021`). Se o usuário digitar `1021021`, o provedor deve injetar o ponto automaticamente antes da requisição.
- **Dica:** Sempre limpe caracteres especiais do termo de busca original para identificar o padrão numérico real antes de aplicar a máscara da marca.

## 6. Clipboard e Referências
- **Prefixação:** Referências extraídas das abas AJAX já costumam vir com a marca (ex: `CABOVEL: 123`).
- **Regra:** Não adicione o prefixo `ORIGINAL: ` se o código já possuir um separador de marca (`:`). Isso evita resultados confusos como `FIAT: CABOVEL: 123`.
