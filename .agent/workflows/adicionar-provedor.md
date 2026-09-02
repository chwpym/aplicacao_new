# 📚 Manual Completo de Cadastro de Provedores

Este guia explica como cadastrar qualquer tipo de catálogo no sistema. Escolha a categoria que se encaixa na marca que você quer adicionar.

---

## 1. 🌐 Busca na Rede (Tuba, Sampel, TC Chicotes)
*Ideal para marcas que estão no portal buscanarede.com.br.*

*   **Tipo:** Escolha `Busca na Rede`.
*   **Nome:** Nome da marca (Ex: `SAMPEL`).
*   **URL:** `https://buscanarede.com.br/apelido-da-marca`
*   **Mapeamento (JSON):**
    ```json
    { "brand_slug": "apelido-da-marca" }
    ```

---

## 2. 🧬 Fraga / Cofap (GraphQL)
*Para marcas que usam a tecnologia da Fraga (Cofap, Monroe, Magneti Marelli).*

*   **Tipo:** Escolha `Cofap (Fraga)` ou `GraphQL Fraga`.
*   **URL:** `https://bff.catalogofraga.com.br/gateway/graphql`
*   **Headers (Cabeçalhos):**
    ```json
    {
      "Origin": "https://marca.catalogofraga.com.br",
      "Referer": "https://marca.catalogofraga.com.br/"
    }
    ```

---

## 3. 🛠️ Viemar (API Própria)
*Específico para o catálogo da Viemar.*

*   **Tipo:** Escolha `Viemar`.
*   **URL:** `https://catalogo.viemar.com.br/catalog/search/catalog/code`

---

## 4. 🤖 DS (Robô Scraper)
*Para o site da DS que exige leitura visual da página.*

*   **Tipo:** Escolha `Robô Scraper (Site DS)`.
*   **URL:** `https://www.ds.ind.br/pt/busca-full?q={id}`

---

## 5. 🔌 REST API / ERP (Avançado)
*Para conectar diretamente no banco de dados de um fornecedor via JSON.*

*   **Tipo:** Escolha `REST API / ERP`.

---

## 6. 🕸️ Scraper Genérico (Universal - Muito Avançado)
*Para sites que não têm API.*

*   **Tipo:** Escolha `Scraper Genérico`.

---

## 7. 🚀 Provedores Nativos e Específicos
Essas marcas possuem integrações dedicadas no sistema. Geralmente você só precisa cadastrar o **Nome**, a **URL** correta e **Ativar**.

**Marcas Suportadas:**
*   **AutoExperts / ATE**
*   **Bosch**
*   **MTE Thomson**
*   **Tecfil**
*   **IMA**
*   **TSA**
*   **Dayco**
*   **Hipper Freios**
*   **Notus**
*   **Nakata**

---

### 💡 Dicas Gerais:
1.  **Sempre Teste:** Use o botão **"Testar no Playground"** para validar.
2.  **Ativo:** Deixe a chavinha **"Provedor Ativo"** ligada.
3.  **Maiúsculas:** Use nomes em MAIÚSCULAS para manter o padrão.

---
*Manual atualizado em: 05/05/2026*
