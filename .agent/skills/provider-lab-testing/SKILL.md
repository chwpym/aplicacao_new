---
name: provider-lab-testing
description: Diretrizes e arquitetura para utilização do Provedor Laboratório isolado (ID 70 - TECFIL LAB) para testes seguros de novos algoritmos de extração e suporte a múltiplos provedores sem poluição do banco de dados.
---

# Provider Lab Testing Architecture

Esta skill define a metodologia para testar e validar novos algoritmos de extração, motores de busca e estratégias de scraping sem correr o risco de alterar ou desestabilizar os provedores oficiais em produção.

---

## 1. Conceito do Provedor Laboratório Único (`TECFIL LAB`)

Para evitar a poluição do Banco de Dados Central (`backend/catalogo.db`) com um "monte de provedores de teste", foi padronizado o **Provedor Laboratório Central (ID: 70)**:

- **ID no Banco**: `70`
- **Nome Exibido**: `TECFIL LAB (TESTES)`
- **Tipo de Provedor**: `tecfil_lab`
- **Arquivo Físico**: [`backend/app/providers/tecfil_lab_provider.py`](file:///d:/Dev/aplicacao_new/backend/app/providers/tecfil_lab_provider.py)

---

## 2. Como Usar o Provedor Laboratório para Testar Qualquer Provedor

Você **não precisa registrar novos provedores no banco de dados** para testar modelos ou marcas diferentes.

Basta modificar o arquivo de laboratório [`tecfil_lab_provider.py`](file:///d:/Dev/aplicacao_new/backend/app/providers/tecfil_lab_provider.py):

### Estrutura de Alternância/Testes no Laboratório:

```python
class TecfilLabProvider(BaseProvider):
    async def buscar(self, codigo: str) -> List[Dict[str, Any]]:
        # ALERTA DE TESTE: Alterne aqui o modo ou o fabricante que deseja testar
        
        # Modo A: Teste Tecfil (RSC JSON x HTML)
        return await self._testar_tecfil(codigo)

        # Modo B: Teste de outro provedor (ex: Bosch / Wega / Schaeffler)
        # return await self._testar_outro_provedor(codigo)
```

Ao selecionar **TECFIL LAB (TESTES)** no seletor de provedores da interface, o sistema executará o código que estiver no arquivo de laboratório, permitindo testes isolados, inspeção de logs e validação no frontend.

---

## 3. Fluxo Seguro de Promoção (Laboratório → Produção)

1. **Desenvolvimento**: Faça os ajustes e testes no arquivo [`tecfil_lab_provider.py`](file:///d:/Dev/aplicacao_new/backend/app/providers/tecfil_lab_provider.py).
2. **Validação**: Teste no frontend selecionando o provedor `TECFIL LAB (TESTES)` até obter 100% de satisfação.
3. **Promoção**: Copie a função aprovada do laboratório para o provedor oficial correspondente em `backend/app/providers/` (ex: `tecfil_provider.py`).
4. **Resguardo**: O laboratório permanece disponível para o próximo teste sem afetar a produção.
