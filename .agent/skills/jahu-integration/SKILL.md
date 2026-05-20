---
name: jahu-integration
description: Diretrizes técnicas e padrões para integração de catálogos baseados na plataforma WMW e-commerce (Jahu Borrachas).
---

# Jahu Borrachas (WMW) Integration Skill

Este documento reúne o conhecimento técnico consolidado na integração do catálogo da **Jahu Borrachas** (plataforma B2B WMW). Ele serve como um guia didático para você aprender as técnicas avançadas de engenharia reversa aplicadas e replicá-las em futuros provedores que utilizem a mesma tecnologia de e-commerce.

---

## 1. Visão Geral da Plataforma WMW
A plataforma de e-commerce da Jahu (`b2b.jahu.com.br`) opera através de endpoints REST assíncronos protegidos por controle de sessão. Para realizar qualquer requisição (mesmo pública) sem sofrer bloqueios do tipo `406 Sessão Expirada`, é mandatório seguir a arquitetura de Handshake de Sessão.

### Fluxo de Comunicação:
1. **Handshake (Login Público):** Disparar requisição para obter o cookie `JSESSIONID` e o parâmetro `sessionId`.
2. **Busca por Termo:** Consultar a API de busca paginada para localizar o produto e sua chave primária (`cdProduto`).
3. **Detalhes Ricos:** Executar uma consulta direta via PrimaryKey para trazer as aplicações em HTML, NCM, códigos originais e fotos.

---

## 2. Técnicas Avançadas Implementadas

### A. Autenticação e Handshake de Sessão
Para evitar bloqueios de segurança e requisições recusadas, a classe de busca deve primeiro obter uma sessão pública válida.
* **Endpoint:** `https://b2b.jahu.com.br/server/public/service/auth/loginAcessoPublico`
* **Método:** `POST`
* **Payload Mínimo:**
  ```json
  {
    "host": "https://b2b.jahu.com.br",
    "usuario": {
      "cdSistema": 50,
      "flAtivo": "S"
    }
  }
  ```
* **Resposta:** Retorna um JSON contendo `sessionId`. O cookie `JSESSIONID` é atribuído automaticamente na resposta HTTP e deve ser persistido no cliente HTTP (`httpx.AsyncClient`).

---

### B. Galeria Concorrente Inteligente (Filtragem por Content-Type)
* **O Desafio:** A API de fotos da WMW aceita parâmetros de carrossel de index 1 a 6. Contudo, ela retorna status HTTP `200 OK` mesmo para imagens inexistentes (placeholders com texto "Sem Foto").
* **A Solução:** Realizar requisições simultâneas leves concorrentes usando `asyncio.gather` para os 6 possíveis slots e diferenciar a imagem real do placeholder pelo cabeçalho `Content-Type` retornado pelo servidor:
  * **Imagem Real (jpeg):** `Content-Type: image/jpeg;charset=utf-8` (Manter e incluir na galeria)
  * **Placeholder (png):** `Content-Type: image/png;charset=utf-8` (Descartar silenciosamente)

---

### C. Busca de Similares por Crossover (Ícone de Raio)
* **O Desafio:** Os similares da própria marca no catálogo Jahu não são listados no payload do produto detalhado.
* **A Solução:** Extrair o código original do fabricante (`AD_CODORIG`) do detalhe do produto e, em segundo plano, disparar uma nova requisição de busca paginada (`findAllByExampleByPages`) usando o código original como palavra-chave.
  * Capturar todos os SKUs da própria Jahu que compartilham desse mesmo código original de montadora.
  * Injetar os SKUs retornados na lista de referências cruzadas com o prefixo `JAHU: SKU_SIMILAR`.
  * Isso faz com que o frontend identifique as equivalências e ative a funcionalidade nativa do **raio de similares**.

---

### D. Pré-Parser de Motorização e Versão
* **O Desafio:** Na tabela HTML de aplicações (`AD_DSAPLICACAO`), a coluna `MODELO` traz dados mistos (versões como `G1 TODOS` e motores como `1.4 8V`). Se a motorização não for extraída antes de enviar os dados para a normalização central do `BaseProvider`, o motor será limpo e descartado da versão, gerando colunas de motor em branco (`---`).
* **A Solução:** Executar o pré-parser de motorização na string de modelo raw antes de chamar o formatador central:
  ```python
  motor_extraido, config_extraida, versao_limpa = normalization_service.extrair_motorizacao(modelo_raw)
  ```
  Isso garante que motores e configurações sejam devidamente identificados e mapeados para as chaves `"motor"` e `"configuracao_motor"`, enquanto a versão limpa preenche o campo `"versao"`.

---

### E. Regra Crítica de Prefixos de Referência (Clipboard & Topo)
* **Regra do Frontend:** O frontend (`clipboard.ts` e componente de caixa de originais do topo) descarta silenciosamente qualquer referência cruzada que não possua um prefixo de identificação (ex: `MARCA: CODIGO` ou `ORIGINAL: CODIGO`).
* **Padrão de Formatação:**
  * O backend deve sempre formatar códigos originais cru com o prefixo `ORIGINAL: ` (ex: `ORIGINAL: 90354836`).
  * Ao fazer isso, o serviço de normalização central (`padronizar_referencias`) traduzirá inteligentemente o prefixo `ORIGINAL` para a marca da montadora proprietária (ex: `CHEVROLET: 90354836`), mantendo a compatibilidade total com o clipboard e a caixa superior da tela.

---

## 3. Template de Provedor WMW Base (Didático)
Você pode utilizar a estrutura abaixo como ponto de partida para qualquer catálogo futuro baseado na mesma plataforma e-commerce (WMW):

```python
# Exemplo estrutural e didático de conexão WMW
import httpx
import asyncio
from app.providers.base_provider import BaseProvider
from app.services.normalization_service import normalization_service

class ExemploWmwProvider(BaseProvider):
    async def buscar(self, termo: str):
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # 1. Handshake de sessão pública
            resp_login = await client.post("URL_LOGIN", json=PAYLOAD_LOGIN)
            session_id = resp_login.json().get("sessionId")
            
            # 2. Busca paginada por termo
            resp_search = await client.post("URL_BUSCA", json=payload_busca_com_session)
            
            # 3. Detalhes ricos (PrimaryKey)
            resp_det = await client.post("URL_DETALHES", json=payload_det_com_session)
            
            # 4. Extração e normalização
            # (Aplicar Galeria Concorrente, Crossover de Similares e Pré-Parser de Motorização)
            ...
```
