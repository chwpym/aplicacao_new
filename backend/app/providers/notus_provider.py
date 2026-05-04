import httpx
import json
import os
import time
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger

class NotusProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        # URL do JSON estático da Notus
        self.url_json = "https://catalogo.notus.ind.br/conversor/produtos.json"
        # Local de cache segregado (backend/data/providers)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "providers", "notus_cache.json"))
        self.base_url = "https://catalogo.notus.ind.br/"
        
        # Garante que a pasta de dados existe
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    async def _update_cache(self):
        """Baixa o JSON se não existir ou se for antigo (24h)"""
        should_update = False
        if not os.path.exists(self.cache_path):
            should_update = True
        else:
            file_age = time.time() - os.path.getmtime(self.cache_path)
            if file_age > 86400: # 24 horas
                should_update = True
        
        if should_update:
            logger.info("NOTUS", "Atualizando cache do catálogo Notus (~8MB)...")
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(self.url_json)
                    if resp.status_code == 200:
                        with open(self.cache_path, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        logger.info("NOTUS", "Cache Notus atualizado com sucesso.")
                    else:
                        logger.error("NOTUS", f"Erro ao baixar catálogo Notus (Status {resp.status_code}) da URL: {self.url_json}")
            except Exception as e:
                logger.error("NOTUS", f"Falha na conexão ao baixar JSON de {self.url_json}: {str(e)}")

    async def buscar(self, termo: str) -> list[dict]:
        """
        Realiza a busca no arquivo JSON em memória.
        Implementa busca inteligente em códigos Notus, OEM e Referências.
        """
        await self._update_cache()
        
        if not os.path.exists(self.cache_path):
            logger.warning("NOTUS", "Cache não disponível para busca.")
            return []

        if not os.path.exists(self.cache_path):
            logger.info("NOTUS", "Cache não encontrado. Iniciando download automático...")
            await self._update_cache()
            # Se mesmo após o download não existir, aí sim retornamos vazio
            if not os.path.exists(self.cache_path):
                return []

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                produtos = json.load(f)
        except Exception as e:
            logger.error("NOTUS", f"Erro ao carregar cache Notus: {e}")
            return []

        # Gera variações do termo e garante a versão limpa (sem hifens/pontos)
        codigos_busca = self.normalizar_codigo(termo)
        termos_lower = [t.lower().replace("-", "").replace(".", "").replace(" ", "") for t in codigos_busca]
        # Remove duplicatas mantendo a ordem
        termos_lower = list(dict.fromkeys(termos_lower))
        
        resultados = []
        
        # Filtros de busca no JSON
        for p in produtos:
            # Lista dinâmica de campos de referência
            ref_keys = ["codigo", "referenciaoriginal", "crossreference", "denso", "mahle", "marelli", "valeo", "visconde", "codigodebarras"]
            campos_busca = [p.get(k) for k in ref_keys if p.get(k)]
            
            # Verifica se algum termo de busca está presente em algum campo do produto
            match = False
            for val in campos_busca:
                if not val: continue
                val_str = str(val)
                # Filtra lixo de dados (> 200 chars) para evitar falsos positivos
                if len(val_str) > 200: continue
                
                # Limpa o valor do campo para comparação (remove hifens, pontos e espaços)
                val_clean = val_str.lower().replace("-", "").replace(".", "").replace(" ", "")
                if any(t in val_clean for t in termos_lower):
                    match = True
                    break
            
            if match:
                # Legenda para A/C
                ac_raw = p.get("ac", "")
                ac_map = {
                    "+/-": "COM E SEM AR-CONDICIONADO",
                    "-": "SEM AR-CONDICIONADO",
                    "+": "COM AR-CONDICIONADO"
                }
                ac_desc = ac_map.get(ac_raw, ac_raw)

                # Legenda para Transmissão
                trans_raw = str(p.get("transmissao", "")).upper().strip()
                trans_map = {
                    "AUT": "AUTOMÁTICA",
                    "MEC": "MECÂNICA",
                    "AUT / MEC": "AUTOMÁTICA / MECÂNICA",
                    "AUT/MEC": "AUTOMÁTICA / MECÂNICA"
                }
                trans_desc = trans_map.get(trans_raw, trans_raw)

                # Mapeamento para o formato esperado pelo BaseProvider.formatar_resultado
                raw_item = {
                    "marca_peca": str(self.config.get("nome", "NOTUS")).upper(),
                    "codigo": p.get("codigo"),
                    "montadora": p.get("montadora"),
                    "modelo": p.get("modelo"),
                    "motor": p.get("litragem"),
                    "configuracao_motor": f"{p.get('tecnologia', '')} {ac_raw} {trans_raw}".strip(),
                    "ano_inicio": p.get("ano"),
                    "imagem": self._get_absolute_image_url(p.get("imagem")),
                    "referencias": self._unificar_referencias(p),
                    # Observação enriquecida com dados técnicos conforme solicitado
                    "observacao": self._formatar_observacao(p, ac_desc, trans_desc),
                    "ficha_tecnica": {
                        "ALTURA COLMEIA": p.get("alturacolmeia") or "-",
                        "COMPRIMENTO COLMEIA": p.get("comprimentocolmeia") or "-",
                        "LARGURA COLMEIA": p.get("larguracolmeia") or "-",
                        "TECNOLOGIA": p.get("tecnologia"),
                        "A/C": ac_desc,
                        "TRANSMISSÃO": trans_desc,
                        "NCM": p.get("ncm"),
                        "EAN": p.get("codigodebarras"),
                        "LINHA": p.get("linha")
                    }
                }
                
                resultados.append(self.formatar_resultado(raw_item))
                
                if len(resultados) >= 100:
                    break
                    
        return resultados

    def _formatar_observacao(self, p, ac_desc, trans_desc):
        obs = [p.get("descricao", "")]
        tecnico = []
        if p.get("tecnologia"): tecnico.append(f"TECNOLOGIA: {p.get('tecnologia')}")
        if ac_desc: tecnico.append(f"A/C: {ac_desc}")
        if trans_desc: tecnico.append(f"TRANSMISSÃO: {trans_desc}")
        
        # Dimensões da Colmeia (Sempre presentes conforme solicitado)
        tecnico.append(f"ALTURA: {p.get('alturacolmeia', '-') or '-'}")
        tecnico.append(f"COMPRIMENTO: {p.get('comprimentocolmeia', '-') or '-'}")
        tecnico.append(f"LARGURA: {p.get('larguracolmeia', '-') or '-'}")
        
        return f"{obs[0]} | {' | '.join(tecnico)}"

    def _get_absolute_image_url(self, path):
        """Converte caminhos relativos do JSON em URLs absolutas."""
        if not path:
            return ""
        if path.startswith("http"):
            return path
        clean_path = path[2:] if path.startswith("./") else path
        from urllib.parse import urljoin
        return urljoin(self.base_url, clean_path)

    def _unificar_referencias(self, p):
        """Concatena todas as referências cruzadas disponíveis de forma dinâmica."""
        refs = []
        # Campos conhecidos de referência no JSON da Notus
        ref_keys = {
            "referenciaoriginal": "OEM",
            "crossreference": "CROSS",
            "denso": "DENSO",
            "mahle": "MAHLE",
            "marelli": "MARELLI",
            "valeo": "VALEO",
            "visconde": "VISCONDE"
        }
        
        for key, label in ref_keys.items():
            val = p.get(key)
            if val and str(val).strip() not in ["", "null", "None"]:
                # Substitui ':' por '-' conforme solicitado pelo usuário
                val_clean = str(val).replace(":", " - ")
                
                # Filtro de segurança: Ignora referências gigantescas (lixo de dados do provedor)
                # Listas de códigos legítimos podem chegar a 150-180 caracteres. 200 é uma margem segura.
                if len(val_clean) < 200:
                    refs.append(f"{label}: {val_clean}")
        
        return " | ".join(refs)
