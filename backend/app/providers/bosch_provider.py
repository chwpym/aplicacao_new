from app.providers.base_provider import BaseProvider
import asyncio
import httpx


class BoschProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.api_base = "https://ps.am.dxtservice.com/ps/api/pt/br"
        # Headers exatos do cURL do usuário
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://am.boschaftermarket.com",
            "Referer": "https://am.boschaftermarket.com/",
            "X-Requested-With": "XMLHttpRequest",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
        }

    async def buscar(self, part_id: str):
        # 1. Normalização do ID (Remove espaços para a URL, mantendo o original se necessário)
        clean_id = part_id.strip().upper().replace(" ", "")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                # 2. Busca de Detalhes (Endpoint validado via cURL)
                # search-details retorna dados do produto (imagens, referências, nome)
                details_url = f"{self.api_base}/search-details/{clean_id}"
                params = {
                    "queryPIM": "true",
                    "catalogId": "AA_WEBSITE_BR",
                    "pimCountry": "br",
                    "pimLanguage": "pt_br",
                }

                print(f"[BOSCH] Buscando detalhes: {details_url}")
                resp = await client.get(
                    details_url, params=params, headers=self.headers
                )

                if resp.status_code != 200:
                    print(
                        f"[BOSCH] Falha nos detalhes ({resp.status_code}). Tentando sem params..."
                    )
                    resp = await client.get(details_url, headers=self.headers)

                if resp.status_code != 200:
                    print(f"[BOSCH] Produto não encontrado ou erro de acesso.")
                    return []

                try:
                    product_data = resp.json()
                except:
                    print(f"[BOSCH] Resposta não é JSON em detalhes.")
                    return []

                prod_num = product_data.get("productNumber")
                if not prod_num:
                    print(f"[BOSCH] JSON de detalhes sem productNumber.")
                    return []

                # Agora buscamos aplicações usando o token/número do produto
                return await self._get_full_applications(client, prod_num, product_data)

            except Exception as e:
                print(f"[BOSCH] Erro na busca: {str(e)}")
                return []

    async def _get_full_applications(self, client, prod_num, product_details):
        """Coordena a busca de montadoras e veículos."""
        try:
            # 1. Busca de Fabricantes (Makers)
            makers_url = f"{self.api_base}/usage-in-vehicles/{prod_num}/makers"
            print(f"[BOSCH] Buscando montadoras: {makers_url}")
            mak_resp = await client.get(makers_url, headers=self.headers)

            if mak_resp.status_code != 200:
                # Se não houver aplicações, retorna o produto como genérico
                return [self._format_product_only(product_details)]

            makers_list = mak_resp.json().get("makers", [])
            if not makers_list:
                return [self._format_product_only(product_details)]

            # 2. Extração de Base (Imagens, Referências, Medidas)
            # Imagens
            imgs = [
                img["url"]
                for img in product_details.get("images", [])
                if img.get("url")
            ]

            # Referências OE
            refs = []
            for oe in product_details.get("oeNumbers", []):
                d = oe.get("columnData", [])
                if len(d) >= 2:
                    refs.append(f"{d[0]}: {d[1]}")
            ref_str = " | ".join(refs)

            # Medidas / Especificações
            complemento = product_details.get("name", "")
            specs = []
            for s in product_details.get("specificationTabData", []):
                col = s.get("columnData", [])
                if len(col) >= 2 and col[0] not in [
                    "Número de pedido",
                    "Designação",
                    "Estado do artigo",
                ]:
                    specs.append(f"{col[1]}")
            designacao = f"{complemento} | {' , '.join(specs)}"

            # 3. Busca de Veículos por Montadora (Paralelo)
            v_tasks = []
            for m in makers_list:
                m_id = m.get("id")
                if m_id:
                    v_url = (
                        f"{self.api_base}/usage-in-vehicles/{prod_num}/vehicles/{m_id}"
                    )
                    v_tasks.append(client.get(v_url, headers=self.headers))

            v_resps = await asyncio.gather(*v_tasks)

            final_results = []
            for vr in v_resps:
                if vr.status_code != 200:
                    continue
                v_json = vr.json()
                # Tenta encontrar o displayName para esta montadora
                maker_id = (
                    v_json.get("vehicles", [{}])[0].get("keyMakerId")
                    if v_json.get("vehicles")
                    else None
                )
                display_name = next(
                    (
                        m.get("displayName")
                        for m in makers_list
                        if m.get("id") == maker_id
                    ),
                    None,
                )

                for v in v_json.get("vehicles", []):
                    raw = {
                        "brand": "BOSCH",
                        "codigo": prod_num,
                        "veiculo": display_name or v.get("keyMakerId", "BOSCH"),
                        "modelo": v.get("type", ""),
                        "motor": v.get("motorType", ""),
                        "configuracao_motor": designacao,
                        "referencias": ref_str,
                        "imagens": imgs,
                        "ano_inicio": self._fmt_date(
                            v.get("productionPeriod", {}).get("from")
                        ),
                        "ano_fim": self._fmt_date(
                            v.get("productionPeriod", {}).get("to")
                        ),
                    }
                    # Usa o formatador da base para garantir nomes de campos canônicos
                    res = self.formatar_resultado(raw)

                    # Lógica de posição se estiver no nome do produto
                    if not res.get("posicao"):
                        lower_name = complemento.lower()
                        if "dianteiro" in lower_name:
                            res["posicao"] = "DIANTEIRO"
                        elif "traseiro" in lower_name:
                            res["posicao"] = "TRASEIRO"

                    final_results.append(res)

            return (
                final_results
                if final_results
                else [self._format_product_only(product_details)]
            )

        except Exception as e:
            print(f"[BOSCH] Erro nas aplicações: {e}")
            return [self._format_product_only(product_details)]

    def _format_product_only(self, details):
        """Formata o resultado básico quando não há aplicações de veículos."""
        imgs = [img["url"] for img in details.get("images", []) if img.get("url")]
        refs = []
        for oe in details.get("oeNumbers", []):
            d = oe.get("columnData", [])
            if len(d) >= 2:
                refs.append(f"{d[0]}: {d[1]}")

        return self.formatar_resultado(
            {
                "brand": "BOSCH",
                "codigo": details.get("productNumber", ""),
                "veiculo": "PRODUTO SEM APLICAÇÃO",
                "modelo": details.get("name", ""),
                "referencias": " | ".join(refs),
                "imagens": imgs,
            }
        )

    def _fmt_date(self, d):
        if not d:
            return ""
        # Retorna apenas o ano para evitar que o motor central de extração
        # interprete o mês (2 dígitos) como um ano curto (ex: 04 -> 2004)
        return str(d.get("year", ""))
