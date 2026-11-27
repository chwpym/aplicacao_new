import httpx
import json
import os
import time
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger

class NotusProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        # Nova URL da API REST da Notus (substituiu o antigo conversor/produtos.json do subdomínio catalogo)
        self.url_json = "https://notus.ind.br/notus-backend/api/catalogo/produtos"
        # Local de cache segregado (backend/data/providers)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "providers", "notus_cache.json"))
        self.base_url = "https://notus.ind.br/Catalogo/"
        
        # Garante que a pasta de dados existe
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    async def _update_cache(self):
        """Baixa o JSON se não existir ou se for antigo (24h)"""
        should_update = False
        if not os.path.exists(self.cache_path) or os.path.getsize(self.cache_path) < 1000:
            should_update = True
        else:
            file_age = time.time() - os.path.getmtime(self.cache_path)
            if file_age > 86400: # 24 horas
                should_update = True
        
        if should_update:
            logger.info("NOTUS", "Atualizando cache do catálogo Notus (~8MB)...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://notus.ind.br/Catalogo/todosprodutos.html"
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(self.url_json, headers=headers)
                    if resp.status_code == 200:
                        with open(self.cache_path, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        logger.info("NOTUS", f"Cache Notus atualizado com sucesso ({len(resp.text)} bytes).")
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
        
        if not os.path.exists(self.cache_path) or os.path.getsize(self.cache_path) < 1000:
            logger.warning("NOTUS", "Cache não disponível para busca.")
            return []

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                produtos = json.load(f)
        except Exception as e:
            logger.error("NOTUS", f"Erro ao carregar cache Notus: {e}")
            return []

        # Gera variações do termo e garante a versão limpa (sem hifens/pontos/espaços/underscores)
        codigos_busca = self.normalizar_codigo(termo)
        termos_lower = [t.lower().replace("-", "").replace(".", "").replace(" ", "").replace("_", "") for t in codigos_busca]
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
                
                # Limpa o valor do campo para comparação (remove hifens, pontos, espaços e underscores)
                val_clean = val_str.lower().replace("-", "").replace(".", "").replace(" ", "").replace("_", "")
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

                prod_id = p.get("id")
                link_produto = f"https://notus.ind.br/Catalogo/ficha-produto.html?id={prod_id}" if prod_id else f"https://notus.ind.br/Catalogo/todosprodutos.html?search={p.get('codigo', '')}"
                
                imagens = self._extract_images(p)

                # Mapeamento para o formato esperado pelo BaseProvider.formatar_resultado
                raw_item = {
                    "marca_peca": str(self.config.get("nome", "NOTUS")).upper(),
                    "codigo": p.get("codigo"),
                    "descricao_produto": p.get("descricao") or p.get("nome"),
                    "montadora": p.get("montadora"),
                    "modelo": p.get("modelo"),
                    "motor": p.get("litragem"),
                    "configuracao_motor": f"{p.get('tecnologia', '')} {ac_raw} {trans_raw}".strip(),
                    "ano_inicio": p.get("ano"),
                    "imagem": imagens[0] if imagens else "",
                    "imagens": imagens,
                    "link": link_produto,
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
                        "LINHA": p.get("linha"),
                        "CATEGORIA": p.get("categoria"),
                        "GRUPO": p.get("grupo"),
                        "LINK CATÁLOGO": link_produto
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

    def _extract_images(self, p: dict) -> list[str]:
        """Extrai todas as imagens válidas do produto (imagem, imagem2..imagem12)."""
        imagens = []
        keys = ["imagem"] + [f"imagem{i}" for i in range(2, 13)]
        for k in keys:
            val = p.get(k)
            if val:
                abs_url = self._get_absolute_image_url(val)
                if abs_url and abs_url not in imagens:
                    imagens.append(abs_url)
        return imagens

    def _get_absolute_image_url(self, path):
        """Converte caminhos relativos ou protocol-relative em URLs absolutas HTTPS."""
        if not path:
            return ""
        path = str(path).strip()
        if path.startswith("//"):
            return f"https:{path}"
        if path.startswith("http://") or path.startswith("https://"):
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

