---
name: viemar-integration
description: Conhecimento técnico sobre a integração com o catálogo REST da Viemar.
---

# Integração Viemar (REST)

Este skill descreve como integrar e manter o provedor de dados da Viemar, que utiliza uma API REST baseada em POST.

## Arquitetura de Comunicação

- **Endpoint**: `https://catalogo.viemar.com.br/catalog/search/catalog/code`
- **Método**: `POST`
- **Payload**: `{"searchCode": "CÓDIGO", "cardMode": true}`
- **Headers**: Exige `Content-Type: application/json`.

## Particularidades do Parser

### 1. Tratamento de Imagens

A API da Viemar é inconsistente no retorno do campo `image` e retorna apenas o nome do arquivo (ex: `680402.jpg`).

- **Base URL**: `https://catalogo.viemar.com.br/catalog/size/normal/image/`
- **Formato A**: Lista de dicionários (ex: `[{ "value": "680402.jpg" }]`).
- **Formato B**: Dicionário direto (ex: `{ "value": "680402.jpg" }`).

O `ViemarProvider` deve concatenar a **Base URL** e verificar o tipo (`isinstance(image_data, dict)`) para evitar erros de indexação (`KeyError: 0`).

### 2. Hierarquia de Veículos

As aplicações costumam estar aninhadas no campo `application` de cada item do `catalog`. Se `application` estiver vazio, o sistema deve usar os campos de nível superior (`brand`, `model`, `year`).

### 3. Parser de Anos

A Viemar utiliza o separador `>` para intervalos de anos (ex: `08 > 13`). O código utiliza uma regex robusta para converter esses casos em `ano_inicio` e `ano_fim`.

## Depuração

- Utilize o script `backend/tools/debug_viemar_raw.py` para visualizar a resposta bruta da API antes do processamento.
