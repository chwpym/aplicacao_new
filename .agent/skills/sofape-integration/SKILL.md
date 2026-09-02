---
name: sofape-integration
description: Diretrizes técnicas e padrões para integração de catálogos do Grupo Sofape (Tecfil e Vox), abrangendo portais JSF/PrimeFaces legados e os novos portais Next.js SSR.
---

# Sofape Integration (Tecfil & Vox)

Esta skill documenta o conhecimento arquitetural necessário para dar manutenção e integrar catálogos do **Grupo Sofape** (marcas Tecfil e Vox), que utilizam dois padrões de mecânica muito distintos.

---

## 1. Catálogos Next.js SSR (Padrão Tecfil Novo)

Os portais modernos do grupo utilizam Next.js com renderização no servidor (SSR).

### Fluxo de Busca e Enriquecimento
1. **Busca Inicial (GET):** Fazer uma chamada GET para `https://<dominio>/search/{codigo_encoded}`.
   - **IMPORTANTE:** O código buscado deve ser URL-encoded (ex: `urllib.parse.quote(codigo, safe="")`). Códigos como `GI50/7` contêm uma barra `/` que, se não for encodada como `%2F` (`GI50%2F7`), quebra o roteamento do Next.js dividindo-o em múltiplos segmentos na URL, resultando em falha ou 404.
   - O Next.js envia o HTML pré-renderizado. A tabela de aplicações está localizada na estrutura do DOM usando as classes de tabela clássicas do Material UI (`MuiTable-root`).
2. **Identificação do Fabricante:** Linhas com o atributo `data-fabricante="MARCA"` marcam a montadora ativa na tabela.
3. **Extração de Aplicações:** As colunas contêm as informações do veículo estruturadas em spans específicos (`DescricaoAplicacao`, `ComplementoAplicacao3_1` para versão, `ComplementoAplicacao3_2` para motor, `ComplementoAplicacao3_5` para combustível, `ComplementoAplicacao3_3` e `3_4` para os anos).
4. **Resgate do ID do Produto:** O produto buscado é destacado com o atributo `data-rh-produto-destaque="true"`. A partir dele, extraímos o ID do produto contido no link `/produto/{id_produto}`.
5. **Enriquecimento de Detalhes (GET):** Fazer um GET para `https://<dominio>/search/{codigo_encoded}/produto/{id_produto}` (utilizando o código também encodado e sem parâmetros de query para agilizar) para obter a ficha técnica e a lista de conversões.

### Parsing de Conversões (Referências Cruzadas)
O Next.js armazena a cache de dados serializada em blocos de script `self.__next_f.push`. 
- **Extração com Brackets Matching:** Localizar a chave `"ReferenciasCruzada"` e caminhar coletando os caracteres até obter um bloco de colchetes `[...]` balanceado.
- **Deserialização:** Substituir os escapes (`\"` por `"`, `\\` por `\`) e carregar com `json.loads`. Filtrar a lista para pegar a marca alvo e obter os códigos concorrentes formatados em `MARCA: CODIGO`.

### Parsing de Ficha Técnica (Dimensões)
Para evitar conflito com os labels de filtros do cabeçalho da página, o parsing da ficha técnica (Altura, Largura, Comprimento) deve:
1. Localizar o container que contém o cabeçalho `"Especificações técnicas"`.
2. Subir no DOM até o container pai comum que contenha as strings `"Função"` e `"Elemento Filtrante"`.
3. Executar a busca de labels (`Altura (mm)`, etc.) estritamente **dentro** desse container isolado.

### Imagens do Produto
As fotos dos produtos são centralizadas no servidor expresso da C123.
- **Padrão de URL:** `https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{ArquivoFotoProduto}`
- O nome do arquivo (ex: `ACP303_A.jpg`, `ACP303_B.jpg`) é obtido via regex da chave `"ArquivoFotoProduto"` no payload serializado.

---

## 2. Catálogos PrimeFaces JSF (Padrão Vox / Tecfil Legado)

Os portais clássicos utilizam a tecnologia JavaServer Faces (JSF) com o framework de componentes PrimeFaces.

### Estado e Sessão (ViewState)
As requisições dependem de um estado persistente no servidor (`javax.faces.ViewState`).
1. **Iniciar Sessão (GET):** Acessar a página inicial do catálogo (ex: `/catalogo.xhtml`) para gerar cookies de sessão e capturar o input hidden contendo o `ViewState`.
2. **Disparar Busca (POST):** Fazer um POST para `/catalogo.xhtml` enviando o payload correspondente ao formulário de busca da marca.
   - **Vox ID:** O formulário de busca da Vox utiliza o ID `j_idt67`.
   - **Payload de Busca:**
     ```python
     payload = {
         "j_idt67": "j_idt67",
         "j_idt67:termoConsulta1": codigo_buscado,
         "j_idt67:botaoTermoConsulta1": "Search",
         "javax.faces.ViewState": view_state
     }
     ```

### Navegação de Categorias e Resultados
1. O resultado do POST de busca retorna os botões com as categorias que possuem registros (ex: `Total de Resultados [ 39 ]`).
2. Fazer um GET na página da categoria correspondente (ex: `/resultadoAutomoveis.xhtml?search-term={codigo}`) para extrair as linhas.
3. **Imagens Vox (Atenção):** Embora o catálogo seja da Vox, as imagens estão hospedadas no site corporativo da Tecfil.
   - **Padrão de URL da Imagem:** `https://www.tecfil.com.br/imagens/vox/{CODIGO}A.jpg` (retorna 404 se tentado no domínio da Vox).
