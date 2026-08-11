import httpx
import json
import asyncio
from app.providers.base_provider import BaseProvider

class WegaProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        # API antiga global
        self.url_global = config.get("url", "https://wega.wedigi.com.br/api/v1/produto?cod={id}")
        # API nova com filtro (Brasil)
        self.url_ajax = "https://www.wegamotors.com/wp-admin/admin-ajax.php?action=wega_search_produto&search={id}&countrie=br&lang=PT"
        
        self.headers_ajax = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.wegamotors.com/"
        }
        
    async def buscar(self, id_peca: str):
        codigos_busca = self.normalizar_codigo(id_peca)
        
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            for cod in codigos_busca:
                print(f"[{self.config.get('nome')}] Buscando: {cod}")
                
                # 1. TENTATIVA VIA AJAX (BR)
                try:
                    url = self.url_ajax.replace("{id}", cod)
                    print(f"[{self.config.get('nome')}] Tentando Ajax BR: {url}")
                    resp = await client.get(url, headers=self.headers_ajax)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and data.get("success") and data.get("data"):
                            aplicacoes = data["data"].get("aplicacoes", [])
                            conversoes = data["data"].get("conversoes", [])
                            if aplicacoes:
                                # Sucesso no Ajax! Vamos formatar.
                                return self._formatar_ajax(aplicacoes, conversoes, cod, id_peca, data)
                            elif conversoes:
                                # Sem aplicações mas TEM conversões — retorna produto com referências e imagem
                                print(f"[{self.config.get('nome')}] Sem aplicações mas {len(conversoes)} conversões encontradas para {cod}")
                                return self._formatar_produto_sem_aplicacao(conversoes, cod, "ajax", data)
                except Exception as e:
                    print(f"[{self.config.get('nome')}] Erro na tentativa AJAX: {e}")
                    
                # 2. TENTATIVA VIA API WEDIGI (GLOBAL / FALLBACK)
                try:
                    url = self.url_global.replace("{id}", cod).replace("{codigo}", cod)
                    print(f"[{self.config.get('nome')}] Fallback Global API: {url}")
                    resp = await client.get(url)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and "Obj" in data and isinstance(data["Obj"], dict):
                            aplicacoes = data["Obj"].get("DetailApl", [])
                            conversoes = data["Obj"].get("DetailConv", [])
                            if aplicacoes:
                                return self._formatar_global(aplicacoes, conversoes, cod, id_peca, data)
                            elif conversoes:
                                # Sem aplicações mas TEM conversões — retorna produto com referências e imagem
                                print(f"[{self.config.get('nome')}] Fallback: Sem aplicações mas {len(conversoes)} conversões para {cod}")
                                return self._formatar_produto_sem_aplicacao(conversoes, cod, "global", data)
                except Exception as e:
                    print(f"[{self.config.get('nome')}] Erro na tentativa Global: {e}")
                    
        # Nenhum resultado encontrado.
        # Se o código não contém '/', pode ser um código Wega com variante omitida
        # (ex: usuário digitou "jfa04284" mas o correto é "JFA-0428/4").
        # Usamos o campo "metadados" (já existente no SearchResult schema) para
        # carregar o sinal de aviso — passa pela serialização do FastAPI sem ser descartado.
        # IMPORTANTE: Este bloco é 100% isolado neste provedor — zero impacto em outros.
        if "/" not in id_peca:
            print(f"[{self.config.get('nome')}] Nenhum resultado. Código sem '/' — sinalizando aviso ao frontend.")
            return [{
                "metadados": {
                    "_aviso_wega": True,
                    "mensagem_aviso": (
                        "Nenhuma peça encontrada no catálogo WEGA.\n\n"
                        "Se o código da embalagem contém barra (ex: JFA-0428/4 ou WR-200/3K), "
                        "tente buscar com o código completo exatamente como está impresso na embalagem."
                    ),
                },
                # Campos obrigatórios do SearchResult (todos vazios)
                "marca": "", "veiculo": "", "modelo": "", "versao": "",
                "motor": "", "configuracao_motor": "", "combustivel": "",
                "ano_inicio": None, "ano_fim": None, "codigo": id_peca,
                "referencias": "", "observacao": "", "imagem": "",
                "imagens": [], "ficha_tecnica": None,
                "provedor": self.config.get("nome", "WEGA").upper(),
            }]
        return []

    def _extrair_conversoes_ajax(self, conversoes):
        formatted = []
        for c in conversoes:
            marca = c.get("Marca", "")
            codigo = c.get("Código Concorrente", "")
            if codigo:
                formatted.append(f"{marca}: {codigo}" if marca else str(codigo))
        return " | ".join(formatted)

    def _formatar_ajax(self, aplicacoes, conversoes, cod_real, id_peca, raw_data):
        resultados = []
        refs = self._extrair_conversoes_ajax(conversoes)
        
        canonical_id = self.canonicalizar_id_para_imagem(cod_real)
        base_img = f"https://www.wegamotors.com/assets/images/{canonical_id}.jpg"
        
        for app in aplicacoes:
            res = {
                "montadora": app.get("Montadora", ""),
                "veiculo": "",  # BaseProvider vai ler montadora e veiculo
                "modelo": app.get("Modelo", ""),
                "versao": app.get("Descrição do Modelo", ""),
                "motor": app.get("Motor", ""),
                "configuracao_motor": app.get("Pos_Montagem", ""),
                "ano_inicio": app.get("Ano", ""),
                "ano_fim": app.get("Ano", ""),
                "combustivel": "",
                "observacao": "",
                "imagem": base_img,
                "imagens": [
                    base_img,
                    base_img.replace(".jpg", "B.jpg"),
                    base_img.replace(".jpg", "C.jpg")
                ],
                "referencias": refs,
                "ficha_tecnica": None,
                "codigo": cod_real,
                "provider_id": self.config.get("id"),
                "provedor": "WEGA (BR)"  # Tag visual
            }
            
            # Tratamento de anos da Wega (16 -->)
            if res["ano_inicio"] and "-->" in res["ano_inicio"]:
                res["ano_fim"] = ""
                
            formatted = self.formatar_resultado(res)
            # Salva o raw response apenas no primeiro para debug
            if not resultados:
                formatted["raw_response"] = json.dumps(raw_data, indent=2, ensure_ascii=False)
                
            resultados.append(formatted)
            
        return resultados

    def _extrair_conversoes_global(self, conversoes):
        formatted = []
        for c in conversoes:
            marca = c.get("Marca", "")
            codigo = c.get("CodigoConcorrente", "")
            if codigo:
                formatted.append(f"{marca}: {codigo}" if marca else str(codigo))
        return " | ".join(formatted)

    def _formatar_global(self, aplicacoes, conversoes, cod_real, id_peca, raw_data):
        resultados = []
        refs = self._extrair_conversoes_global(conversoes)
        
        canonical_id = self.canonicalizar_id_para_imagem(cod_real)
        base_img = f"https://www.wegamotors.com/assets/images/{canonical_id}.jpg"
        
        for app in aplicacoes:
            res = {
                "montadora": app.get("Montadora", ""),
                "veiculo": "",
                "modelo": app.get("Modelo", ""),
                "versao": app.get("DescModelo", ""),
                "motor": app.get("Motor", ""),
                "configuracao_motor": app.get("Pos_Montagem", ""),
                "ano_inicio": app.get("Ano", ""),
                "ano_fim": app.get("Ano", ""),
                "combustivel": "",
                "observacao": "",
                "imagem": base_img,
                "imagens": [
                    base_img,
                    base_img.replace(".jpg", "B.jpg"),
                    base_img.replace(".jpg", "C.jpg")
                ],
                "referencias": refs,
                "ficha_tecnica": None,
                "codigo": cod_real,
                "provider_id": self.config.get("id"),
                "provedor": "WEGA (GLOBAL)"  # Tag visual de Fallback
            }
            
            if res["ano_inicio"] and "-->" in res["ano_inicio"]:
                res["ano_fim"] = ""
                
            formatted = self.formatar_resultado(res)
            if not resultados:
                formatted["raw_response"] = json.dumps(raw_data, indent=2, ensure_ascii=False)
                
            resultados.append(formatted)
            
        return resultados

    def _formatar_produto_sem_aplicacao(self, conversoes, cod_real, fonte, raw_data):
        """Formata resultado quando há conversões mas sem aplicações de veículos."""
        # Detecta a fonte das conversões para usar o extrator correto
        if fonte == "ajax":
            refs = self._extrair_conversoes_ajax(conversoes)
        else:
            refs = self._extrair_conversoes_global(conversoes)
        
        canonical_id = self.canonicalizar_id_para_imagem(cod_real)
        base_img = f"https://www.wegamotors.com/assets/images/{canonical_id}.jpg"
        tag = "WEGA (BR)" if fonte == "ajax" else "WEGA (GLOBAL)"
        
        resultado = self.formatar_resultado({
            "marca_peca": "WEGA",
            "codigo": cod_real,
            "montadora": "",
            "veiculo": "PRODUTO SEM APLICAÇÃO",
            "modelo": "",
            "versao": "",
            "motor": "",
            "configuracao_motor": "",
            "combustivel": "",
            "ano_inicio": None,
            "ano_fim": None,
            "observacao": f"{len(conversoes)} referências cruzadas encontradas",
            "imagem": base_img,
            "imagens": [
                base_img,
                base_img.replace(".jpg", "B.jpg"),
                base_img.replace(".jpg", "C.jpg")
            ],
            "referencias": refs,
            "ficha_tecnica": None,
            "provider_id": self.config.get("id"),
            "provedor": tag
        })
        resultado["raw_response"] = json.dumps(raw_data, indent=2, ensure_ascii=False)
        return [resultado]
