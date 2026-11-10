---
name: sofape-integration
description: Diretrizes técnicas e padrões para integração de catálogos do Grupo Sofape (Tecfil e Vox), abrangendo portais JSF/PrimeFaces legados e os novos portais Next.js SSR com suporte a RSC JSON.
---

# Sofape Integration (Tecfil & Vox)

Esta skill documenta o conhecimento arquitetural necessário para dar manutenção e integrar catálogos do **Grupo Sofape** (marcas Tecfil e Vox), que utilizam dois padrões de mecânica muito distintos.

---

## 1. Catálogos Next.js SSR (Padrão Tecfil Novo)

Os portais modernos do grupo utilizam Next.js com renderização no servidor (SSR).

### Modos de Extração e Tags de Marca (Dual-Engine)

1. **Modo Preferencial (RSC JSON - Header `rsc: 1`):**
   - **Tag Visual no Sistema:** `TECFIL (JSON)`
   - **Endpoint:** GET `https://catalogo.tecfil.com.br/search/{codigo_encoded}` enviando o cabeçalho `"rsc": "1"`.
   - **Payload:** Stream serializado de componentes React (RSC).
   - **Processamento:** Extrai a lista inteira de `aplicacoes` devolvida no JSON pelo servidor do Next.js. Isso garante que todos os veículos exibidos no catálogo oficial da Tecfil (Audi, GM, Volkswagen, etc.) sejam capturados com 100% de integridade.
   
2. **Modo Fallback (HTML Table Parsing):**
   - **Tag Visual no Sistema:** `TECFIL (HTML)`
   - **Endpoint:** GET simples `https://catalogo.tecfil.com.br/search/{codigo_encoded}` sem o header `rsc`.
   - **Processamento:** Parseia a estrutura de tabelas com a classe `MuiTable-root`.

### Fluxo de Busca e Enriquecimento
1. **URL Encoding Obrigatório:** O código buscado deve ser URL-encoded (ex: `urllib.parse.quote(codigo, safe="")`). Códigos com barra como `GI50/7` se tornam `GI50%2F7`.
2. **Extração de Aplicações:** 
   - `DescricaoFabricante`: Montadora (ex: AUDI, GENERAL MOTORS, VOLKSWAGEN)
   - `DescricaoAplicacao`: Modelo (ex: A3, Passat, Jetta, Vectra)
   - `ComplementoAplicacao3_1`: Versão
   - `ComplementoAplicacao3_2`: Motor
   - `ComplementoAplicacao3_5`: Combustível
   - `ComplementoAplicacao3_3` e `3_4`: Anos início e fim
3. **ID do Produto e Ficha Técnica:**
   - Link de detalhe: `/produto/{id_produto}`.
   - GET em `https://catalogo.tecfil.com.br/search/{codigo_encoded}/produto/{id_produto}`.
   - **Ficha Técnica (Dimensões/Mecânica):** Extrai campos como `FUNÇÃO`, `ELEMENTO`, `ALTURA`, `Ø INT. LARG.`, `Ø EXT. COMP.`, `VÁLVULA ANTI-RETORNO`, `VÁLVULA ALÍVIO`, `PESO BRUTO`, `PESO LÍQUIDO`, `OBSERVAÇÃO`.
   - **Conversões (ReferenciasCruzadas):** Extrai o bloco de array balanceado `"ReferenciasCruzada"` e converte em string formatada `MARCA: CODIGO`.

### Imagens do Produto
As fotos dos produtos são hospedadas no servidor expresso da C123.
- **Padrão de URL:** `https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{ArquivoFotoProduto}`
- **Fallback de URL:** `https://www.c123.com.br/CatalogoExpresso/133/FotoProdWeb/{CODIGO}_A.jpg`

---

## 2. Catálogos PrimeFaces JSF (Padrão Vox / Tecfil Legado)

Os portais clássicos utilizam a tecnologia JavaServer Faces (JSF) com o framework de componentes PrimeFaces.

### Estado e Sessão (ViewState)
As requisições dependem de um estado persistente no servidor (`javax.faces.ViewState`).
1. **Iniciar Sessão (GET):** Acessar a página inicial do catálogo (`/catalogo.xhtml`) para capturar o `ViewState`.
2. **Disparar Busca (POST):** POST para `/catalogo.xhtml` com o payload de busca.
   - **Vox ID:** Formulário `j_idt67`.
   - **Payload de Busca:**
     ```python
     payload = {
         "j_idt67": "j_idt67",
         "j_idt67:termoConsulta1": codigo_buscado,
         "j_idt67:botaoTermoConsulta1": "Search",
         "javax.faces.ViewState": view_state
     }
     ```

### Navegação e Imagens Vox
- **Imagens Vox:** Hospedadas no site corporativo da Tecfil: `https://www.tecfil.com.br/imagens/vox/{CODIGO}A.jpg`.
