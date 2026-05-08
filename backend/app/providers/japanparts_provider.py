import httpx
import re
import asyncio
from typing import List, Dict, Any, Optional
from app.providers.base_provider import BaseProvider
from app.services.logging_service import logger


class JapanpartsProvider(BaseProvider):
    """
    Provedor para o catálogo Japanparts.
    Usa a API REST pública em api.japanparts.com.br.
    
    Arquitetura: Discovery → Hydration (4 chamadas paralelas)
    1. Discovery: Resolve código da peça → part_id interno
    2. Hydration (todas em paralelo, sem impacto na performance):
       a) Veículos (aplicações) — fonte primária
       b) Equivalências (referências cruzadas) — fonte primária
       c) Dimensões (ficha técnica) — enriquecimento/fallback
       d) Imagens extras — enriquecimento/fallback
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base = "https://api.japanparts.com.br/api"
        self.img_base = "https://static.japanparts.com.br"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=utf-8",
            "Origin": "https://japanparts.com.br",
            "Referer": "https://japanparts.com.br/",
        }

    async def buscar(self, termo: str) -> List[Dict[str, Any]]:
        """
        Busca aplicações no catálogo Japanparts.
        
        Fluxo:
        1. Discovery: GET /api/parts?filter[where][code]={termo} → part_id
        2. Hydration paralela:
           - GET /api/vehicles/findByPartId?partId={id} → aplicações
           - GET /api/part_equivalences/findall?partId={id} → referências cruzadas
        """
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            try:
                # --- FASE 1: DISCOVERY ---
                part_info = await self._discover_part(client, termo)
                if not part_info:
                    logger.warning("JAPANPARTS", f"Peça não encontrada: {termo}")
                    return []

                part_id = part_info["id"]
                logger.info("JAPANPARTS", f"Descoberto part_id={part_id} para código={termo}")

                # --- FASE 2: HYDRATION (4 chamadas paralelas) ---
                vehicles_task = self._fetch_vehicles(client, part_id)
                equivalences_task = self._fetch_equivalences(client, part_id)
                dimensions_task = self._fetch_dimensions(client, part_id)
                images_task = self._fetch_images(client, part_id)

                vehicles_data, equivalences_data, dimensions_data, images_data = await asyncio.gather(
                    vehicles_task, equivalences_task, dimensions_task, images_task
                )

                # --- FASE 3: MONTAGEM DOS RESULTADOS ---
                return self._build_results(
                    termo=termo,
                    part_info=part_info,
                    vehicles=vehicles_data,
                    equivalences=equivalences_data,
                    dimensions=dimensions_data,
                    images=images_data,
                )

            except Exception as e:
                logger.error("JAPANPARTS", f"Erro ao buscar '{termo}': {str(e)}")
                return []

    # ─── Discovery ────────────────────────────────────────────────────

    async def _discover_part(self, client: httpx.AsyncClient, code: str) -> Optional[Dict]:
        """
        Resolve o código da peça para o part_id interno.
        Tenta variações do código (com/sem hífen) se a primeira falhar.
        """
        variacoes = self.normalizar_codigo(code)

        for variacao in variacoes:
            try:
                url = f"{self.api_base}/parts?filter[where][code]={variacao}"
                response = await client.get(url, headers=self.headers)

                if response.status_code == 200:
                    parts = response.json()
                    if parts and isinstance(parts, list) and len(parts) > 0:
                        return parts[0]
            except Exception as e:
                logger.warning("JAPANPARTS", f"Erro no discovery ({variacao}): {str(e)}")
                continue

        return None

    # ─── Hydration: Veículos ──────────────────────────────────────────

    async def _fetch_vehicles(self, client: httpx.AsyncClient, part_id: int) -> List[Dict]:
        """Busca as aplicações (veículos) para a peça."""
        try:
            url = f"{self.api_base}/vehicles/findByPartId?partId={part_id}"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error("JAPANPARTS", f"Erro ao buscar veículos (part_id={part_id}): {str(e)}")

        return []

    # ─── Hydration: Equivalências ─────────────────────────────────────

    async def _fetch_equivalences(self, client: httpx.AsyncClient, part_id: int) -> List[Dict]:
        """Busca as referências cruzadas (equivalências) da peça."""
        try:
            url = f"{self.api_base}/part_equivalences/findall?partId={part_id}"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error("JAPANPARTS", f"Erro ao buscar equivalências (part_id={part_id}): {str(e)}")

        return []

    # ─── Hydration: Dimensões (Fallback/Enriquecimento) ───────────────

    async def _fetch_dimensions(self, client: httpx.AsyncClient, part_id: int) -> Dict:
        """Busca dimensões físicas da peça (peso, altura, diâmetro, rosca). Enriquece a ficha técnica."""
        try:
            url = f"{self.api_base}/part_dimensions?filter[where][part_id]={part_id}"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
        except Exception as e:
            logger.warning("JAPANPARTS", f"Fallback dimensões falhou (part_id={part_id}): {str(e)}")

        return {}

    # ─── Hydration: Imagens Extras (Fallback/Enriquecimento) ──────────

    async def _fetch_images(self, client: httpx.AsyncClient, part_id: int) -> List[Dict]:
        """Busca imagens adicionais da peça. Complementa a imagem do discovery."""
        try:
            url = f"{self.api_base}/part_images?filter[where][part_id]={part_id}"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning("JAPANPARTS", f"Fallback imagens falhou (part_id={part_id}): {str(e)}")

        return []

    # ─── Montagem dos Resultados ──────────────────────────────────────

    def _build_results(
        self,
        termo: str,
        part_info: Dict,
        vehicles: List[Dict],
        equivalences: List[Dict],
        dimensions: Dict = None,
        images: List[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Monta a lista de resultados formatados para o BaseProvider.
        Cada veículo vira uma linha na tabela.
        Usa dimensões e imagens extras como fallback de enriquecimento.
        """
        items = []

        # Marca da peça — extraída dinamicamente do config (nunca chumbada)
        marca_peca = str(self.config.get("nome", "JAPANPARTS")).upper()

        # Subcategoria da peça (ex: "Filtro de Óleo") — útil como descrição
        subcategoria = part_info.get("part_subcategory_name", "")

        # Imagem principal da peça (discovery)
        thumb = part_info.get("thumb", "")
        imagem = f"{self.img_base}{thumb}" if thumb and not thumb.startswith("http") else thumb

        # Imagens extras (fallback do endpoint de imagens)
        imagens_extras = []
        if images:
            for img in images:
                img_path = img.get("thumb", "")
                if img_path:
                    full_url = f"{self.img_base}{img_path}" if not img_path.startswith("http") else img_path
                    if full_url != imagem:  # Evita duplicata com a imagem principal
                        imagens_extras.append(full_url)

        # Se o discovery não trouxe imagem, tenta usar a primeira do fallback
        if not imagem and imagens_extras:
            imagem = imagens_extras.pop(0)

        # Referências cruzadas — montadas uma única vez (são globais para o código)
        referencias = self._format_equivalences(equivalences)

        # Ficha técnica — começa com dados do discovery + enriquece com dimensões
        ficha_tecnica = {}
        if subcategoria:
            ficha_tecnica["TIPO"] = subcategoria.upper()
        bar_code = part_info.get("bar_code", "")
        if bar_code:
            ficha_tecnica["CÓDIGO DE BARRAS"] = bar_code

        # Enriquecimento: dimensões físicas (fallback do endpoint de dimensões)
        if dimensions:
            dim_labels = {
                "weight": "PESO (g)",
                "height": "ALTURA (mm)",
                "length": "COMPRIMENTO (mm)",
                "width": "LARGURA (mm)",
                "external_diam": "DIÂMETRO EXTERNO (mm)",
                "internal_diam": "DIÂMETRO INTERNO (mm)",
                "screw_in": "ROSCA ENTRADA (mm)",
                "screw_out": "ROSCA SAÍDA (mm)",
            }
            for key, label in dim_labels.items():
                val = dimensions.get(key)
                if val and str(val).strip() != "0" and str(val).strip() != "":
                    ficha_tecnica[label] = str(val).strip()

        if not vehicles:
            # Sem veículos, retorna ao menos a peça com as referências
            raw = {
                "marca_peca": marca_peca,
                "codigo": termo.upper(),
                "referencias": referencias,
                "imagem": imagem,
                "imagens": imagens_extras,
                "ficha_tecnica": ficha_tecnica,
            }
            items.append(self.formatar_resultado(raw))
            return items

        for vehicle in vehicles:
            # Extrair montadora dinamicamente
            manufacturer = vehicle.get("vehicleManufacturers", {})
            montadora = manufacturer.get("name", "") if manufacturer else ""

            # Modelo do veículo
            modelo = (vehicle.get("model") or "").strip()

            # Motor — na API da Japanparts, "version" contém a motorização real
            # Ex: "1.0 12V TURBO FLEX" (é o que aparece na coluna Motor no site deles)
            motor = (vehicle.get("version") or "").strip()

            # Configuração do motor — "engine" na API é a plataforma/família do motor
            # Ex: "CSS PRIME" (aparece na coluna Config. Motor)
            config_motor = (vehicle.get("engine") or "").strip()

            # Anos
            ano_inicio = ""
            ano_fim = ""
            year_from = vehicle.get("year_from")
            year_to = vehicle.get("year_to")
            if year_from:
                ano_inicio = year_from[:4]  # "2019-01-01T00:00:00.000Z" → "2019"
            if year_to:
                ano_fim = year_to[:4]

            raw = {
                "marca_peca": marca_peca,
                "codigo": termo.upper(),
                "montadora": montadora,
                "modelo": modelo,
                "motor": motor,
                "configuracao_motor": config_motor,
                "ano_inicio": ano_inicio,
                "ano_fim": ano_fim,
                "referencias": referencias,
                "imagem": imagem,
                "imagens": imagens_extras,
                "ficha_tecnica": ficha_tecnica,
            }

            items.append(self.formatar_resultado(raw))

        return items

    # ─── Helpers ──────────────────────────────────────────────────────

    def _format_equivalences(self, equivalences: List[Dict]) -> List[str]:
        """
        Formata as equivalências como lista de strings para o BaseProvider.
        Marca original (OE) vem primeiro.
        
        Formato: ["GM: 55509268", "TECFIL: PSL612", "MANN: W7056/1"]
        """
        if not equivalences:
            return []

        # Separa originais dos aftermarket
        originals = []
        aftermarket = []

        for eq in equivalences:
            marca = (eq.get("name") or "").strip()
            codigo = (eq.get("equivalence_code") or "").strip()
            if not marca or not codigo:
                continue

            entry = f"{marca}: {codigo}"
            if eq.get("original") == 1:
                originals.append(entry)
            else:
                aftermarket.append(entry)

        # Originais primeiro, depois aftermarket
        return originals + aftermarket
