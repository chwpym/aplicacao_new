import httpx
import asyncio
from app.providers.base_provider import BaseProvider

class DaycoProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = "https://webcateu.dayco.ws/api/"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://www.dayco.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def _post(self, endpoint: str, data: dict, client: httpx.AsyncClient):
        payload = {
            "area": "area2",
            "sito": "car;moto",
            "lingua": "pt_pt",
            "richiesta": endpoint,
            **data
        }
        try:
            resp = await client.post(f"{self.url}{endpoint}", json=payload, headers=self.headers)
            if resp.status_code == 200:
                return resp.json().get("d", {})
        except Exception as e:
            print(f"[{self.config.get('nome', 'DAYCO')}] Erro na requisição {endpoint}: {e}")
        return {}

    async def buscar(self, id_peca: str) -> list[dict]:
        id_peca = id_peca.upper().strip()
        todas_aplicacoes = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Busca Inicial por Código
            print(f"[{self.config.get('nome', 'DAYCO')}] Buscando por P7CODICE: {id_peca}")
            prod_data = await self._post("ProdottiByID", {"filter": f"P7CODICE='{id_peca}'"}, client)
            results = prod_data.get("results", [])
            
            # Fallback para Oe
            if not results:
                print(f"[{self.config.get('nome', 'DAYCO')}] Não encontrou, buscando por Oe: {id_peca}")
                prod_data = await self._post("ProdottiByID", {"filter": f"Oe='{id_peca}'"}, client)
                results = prod_data.get("results", [])
                
            if not results:
                return []
                
            produto = results[0]
            codigo_dayco = produto.get("Title", id_peca)
            
            print(f"[{self.config.get('nome', 'DAYCO')}] Produto encontrado. Buscando Gamma...")

            # 2. Busca Gamma (Modelos)
            gamma_data = await self._post("Gamma", {"sito": "car", "filter": f"P7CODICE='{codigo_dayco}'"}, client)
            
            where_conditions_modello = []
            for g in gamma_data.get("results", []):
                where_conditions_modello.append(g.get("WhereCondition"))

            if not where_conditions_modello:
                print(f"[{self.config.get('nome', 'DAYCO')}] Sem aplicações no catálogo Gamma.")
                return []

            print(f"[{self.config.get('nome', 'DAYCO')}] Encontrado {len(where_conditions_modello)} modelos. Buscando Modello...")

            # 3. Busca Modello (Gerações do Modelo)
            async def fetch_modello(cond):
                return await self._post("Modello", {"sito": "car", "filter": cond}, client)
                
            modello_tasks = [fetch_modello(cond) for cond in where_conditions_modello]
            modello_results = await asyncio.gather(*modello_tasks)
            
            where_conditions_vettura = []
            for m_res in modello_results:
                for m in m_res.get("results", []):
                    where_conditions_vettura.append(m.get("WhereCondition"))

            if not where_conditions_vettura:
                return []

            print(f"[{self.config.get('nome', 'DAYCO')}] Encontrado {len(where_conditions_vettura)} gerações. Buscando VetturaProdotto...")

            # 4. Busca VetturaProdotto (Aplicações Finais)
            async def fetch_vettura(cond):
                return await self._post("VetturaProdotto", {"sito": "car", "filter": cond}, client)
                
            vettura_tasks = [fetch_vettura(cond) for cond in where_conditions_vettura]
            vettura_results = await asyncio.gather(*vettura_tasks)
            
            for v_res in vettura_results:
                for v in v_res.get("results", []):
                    app_dict = self.formatar_resultado(v, produto)
                    if app_dict:
                        todas_aplicacoes.append(app_dict)
                        
        print(f"[{self.config.get('nome', 'DAYCO')}] Finalizado. Encontradas {len(todas_aplicacoes)} aplicações.")
        return todas_aplicacoes
        
    def formatar_resultado(self, raw_data, produto) -> dict:
        """Formata os dados brutos da API Dayco para o formato do sistema."""
        montadora = raw_data.get("MarcaLang", {}).get("Title", "")
        modelo = raw_data.get("ModelloLang", {}).get("Title", "")
        versao = raw_data.get("Versione", "").strip()
        motor = raw_data.get("Motore", {}).get("Title", "")
        cilindrada = raw_data.get("Cilindrata", "")
        
        motor_completo = f"{cilindrada} {motor}".strip()
        
        # O ano vem como "01/2007 > ..."
        ano_str = raw_data.get("Generazione", "")
        ano_inicio = ""
        ano_fim = ""
        
        if ano_str:
            parts = ano_str.split(">")
            if len(parts) > 0:
                ini = parts[0].strip()
                if "/" in ini:
                    ano_inicio = ini.split("/")[1]
                else:
                    ano_inicio = ini
            if len(parts) > 1:
                fim = parts[1].strip()
                if "/" in fim:
                    ano_fim = fim.split("/")[1]
                elif fim != "...":
                    ano_fim = fim
                    
        # Montar referências
        referencias = []
        for oe in produto.get("OesAm", {}).get("results", []):
            referencias.append(f"{oe.get('Descrizione')}: {oe.get('Title')}")
        refs_str = " | ".join(referencias)
        
        # Imagem
        imagem = produto.get("ImmagineCalc", "")
        if imagem and imagem != "noimage.png":
            # API retorna apenas o nome do arquivo, ex: "6PK.jpg"
            imagem = f"https://www.dayco.com/resources/dayco/images/calc/{imagem}"
        else:
            imagem = ""

        nota = raw_data.get("Note", "").strip()
        funcoes = raw_data.get("Funzione", "").strip()
        
        observacao_final = []
        if nota:
            observacao_final.append(nota)
        if funcoes:
            observacao_final.append(f"Funções: {funcoes}")
            
        dados_base = {
            "provedor": self.config.get("nome", "DAYCO"),
            "codigo": produto.get("Title", ""),
            "marca_veiculo": montadora,
            "veiculo": modelo,
            "versao": versao,
            "motor": motor_completo,
            "ano_inicio": ano_inicio,
            "ano_fim": ano_fim,
            "observacao": " | ".join(observacao_final),
            "imagem": imagem,
            "referencias": refs_str,
            "descricao_comercial": produto.get("DescrizioneProdotto", "")
        }
        
        return super().formatar_resultado(dados_base)
