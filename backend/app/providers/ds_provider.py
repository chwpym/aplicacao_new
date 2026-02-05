import httpx
import json
from app.providers.base_provider import BaseProvider
from bs4 import BeautifulSoup


class DSProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.url = config.get("url", "https://www.ds.ind.br/pt/busca-full?q={id}")
        self.headers = config.get(
            "headers",
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )

    def parse_year(self, year_str: str):
        """Converte anos de 2 dígitos para 4 dígitos."""
        if not year_str or year_str == "-":
            return None
        try:
            # Remove caracteres não numéricos
            clean_year = "".join(filter(str.isdigit, year_str))
            if not clean_year:
                return None

            year = int(clean_year)
            if year < 100:
                # Lógica simples: > 40 assume 1900, <= 40 assume 2000
                if year > 40:
                    return 1900 + year
                else:
                    return 2000 + year
            return year
        except Exception:
            return None

    async def buscar(self, id_peca: str):
        # Gera variações do ID (ex: WO545 -> WO-545)
        codigos_busca = self.normalizar_codigo(id_peca)

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for cod in codigos_busca:
                search_urls = [
                    f"https://www.ds.ind.br/pt/busca-full?q={cod}",
                    self.url.replace("{id}", cod),
                ]

                # Categorias comuns
                categorias = [
                    "kit-de-filtros-para-bico-injetor",
                    "valvula-solenoide-de-partida-a-frio",
                    "sensor-de-nivel-de-combustivel",
                    "regulador-de-pressao",
                    "sensor-map",
                    "sensor-de-velocidade",
                ]
                base_url = "https://www.ds.ind.br/pt/produtos"
                for cat in categorias:
                    search_urls.append(f"{base_url}/{cat}/{cod}")

                for url in search_urls:
                    try:
                        print(f"[DS] Tentando URL: {url} (ID: {cod})")
                        response = await client.get(url, headers=self.headers)

                        if response.status_code != 200:
                            print(
                                f"[DS] Falha na requisição ({response.status_code}): {url}"
                            )
                            continue

                        if "Produto não encontrado" in response.text:
                            print(f"[DS] Produto não encontrado na página: {url}")
                            continue

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Se caiu em uma página de busca (múltiplos resultados)
                        # Procura pelo primeiro link de produto na lista de resultados
                        is_search_page = (
                            "busca-full" in str(response.url)
                            or "busca?" in str(response.url)
                            or bool(soup.select(".resultado-itens"))
                        )
                        if is_search_page:
                            print(f"[DS] Página de busca detectada: {response.url}")
                            product_link = soup.select_one(
                                '.resultado-itens a[href*="/produtos/"]'
                            ) or soup.select_one('a[href*="/produtos/"]')
                            if product_link:
                                new_url = product_link["href"]
                                if not new_url.startswith("http"):
                                    new_url = "https://www.ds.ind.br" + new_url

                                print(f"[DS] Link de produto encontrado: {new_url}")
                                # Evita looping se o link for a própria página de busca (improvável mas seguro)
                                if (
                                    "busca-full" not in new_url
                                    and "busca?" not in new_url
                                ):
                                    response = await client.get(
                                        new_url, headers=self.headers
                                    )
                                    if response.status_code == 200:
                                        soup = BeautifulSoup(
                                            response.text, "html.parser"
                                        )
                                        print(
                                            f"[DS] Navegação para produto bem-sucedida: {new_url}"
                                        )
                                    else:
                                        print(
                                            f"[DS] Erro ao navegar para o produto ({response.status_code}): {new_url}"
                                        )
                                        continue
                            else:
                                print(
                                    f"[DS] Nenhum link de produto encontrado na página de busca."
                                )

                        # Agora estamos na página do produto (ou tentamos estar)
                        map_config = {}
                        if self.config.get("mapeamento"):
                            try:
                                map_config = json.loads(self.config["mapeamento"])
                            except Exception as e:
                                print(f"[DS] Erro ao carregar mapeamento JSON: {e}")

                        print(f"[DS] Mapeamento atual: {map_config}")

                        # Extração de Referências (Original e Similar)
                        referencias = []
                        ref_selectors = [
                            map_config.get("referencias"),
                            ".jq-codes tr",
                            ".jq-refs tr",
                            ".tabela-referencias tr",
                        ]
                        for sel in ref_selectors:
                            if not sel:
                                continue
                            ref_els = soup.select(sel)
                            if ref_els:
                                print(
                                    f"[DS] Referências encontradas com seletor '{sel}': {len(ref_els)}"
                                )
                            for ref_el in ref_els:
                                cols = ref_el.find_all("td")
                                if len(cols) >= 2:
                                    # Formato padronizado Marca: Código
                                    brand_ref = cols[0].get_text(strip=True)
                                    code_ref = cols[1].get_text(strip=True)
                                    txt = f"{brand_ref}: {code_ref}"
                                elif cols:
                                    txt = " ".join(
                                        [c.get_text(strip=True) for c in cols]
                                    )
                                else:
                                    txt = ref_el.get_text(strip=True, separator=" ")

                                if txt and txt not in referencias:
                                    referencias.append(txt)

                        # Extração de Múltiplas Imagens
                        imagens = []
                        img_selectors = [
                            map_config.get("imagem"),
                            ".pgwSlider img",
                            ".img-produto",
                            ".gallery img",
                        ]
                        for sel in img_selectors:
                            if not sel:
                                continue
                            img_els = soup.select(sel)
                            if img_els:
                                print(
                                    f"[DS] Imagens encontradas com seletor '{sel}': {len(img_els)}"
                                )
                            for img_el in img_els:
                                src = img_el.get("src") or img_el.get("data-src")
                                if src:
                                    if not src.startswith("http"):
                                        src = "https://www.ds.ind.br" + src
                                    if src not in imagens:
                                        imagens.append(src)

                        resultados = []
                        # Força mapeamento padrão se o usuário não definiu nada ou se está incompleto
                        if not map_config or not map_config.get("container"):
                            print(
                                f"[DS] Usando Mapeamento Padrão (Container não definido na config)"
                            )
                            map_config = {
                                "container": ".jq-apps tr, table.table-aplicacao tr",
                                "marca": "td.montadora",
                                "veiculo": "td.modelo",
                                "modelo": "td.modelo",  # Fallback
                                "motor": "td.motor",
                                "configuracao_motor": "td.complemento",
                                "observacao": "td.observacoes",
                                "ano_inicio": "td.ano",
                                "imagem": ".pgwSlider img",
                                "referencias": ".jq-codes tr",
                            }
                        container_sel = map_config.get("container", "table tr")
                        container_els = soup.select(container_sel)
                        print(
                            f"[DS] Itens encontrados pelo seletor de container '{container_sel}': {len(container_els)}"
                        )

                        for item in container_els:
                            try:
                                # Tenta extrair cada campo baseado no mapeamento
                                brand = (
                                    item.select_one(map_config["marca"]).get_text(
                                        strip=True
                                    )
                                    if map_config.get("marca")
                                    and item.select_one(map_config["marca"])
                                    else ""
                                )
                                name = (
                                    item.select_one(map_config["veiculo"]).get_text(
                                        strip=True
                                    )
                                    if map_config.get("veiculo")
                                    and item.select_one(map_config["veiculo"])
                                    else ""
                                )
                                model = (
                                    item.select_one(
                                        map_config.get("modelo", "")
                                    ).get_text(strip=True)
                                    if map_config.get("modelo")
                                    and item.select_one(map_config["modelo"])
                                    else ""
                                )
                                engine = (
                                    item.select_one(
                                        map_config.get("motor", "")
                                    ).get_text(strip=True)
                                    if map_config.get("motor")
                                    and item.select_one(map_config["motor"])
                                    else ""
                                )
                                fuel = (
                                    item.select_one("td.complemento").get_text(
                                        strip=True
                                    )
                                    if item.select_one("td.complemento")
                                    else ""
                                )
                                obs = (
                                    item.select_one("td.observacoes").get_text(
                                        strip=True
                                    )
                                    if item.select_one("td.observacoes")
                                    else ""
                                )

                                ano_text = (
                                    item.select_one(
                                        map_config.get("ano_inicio", "")
                                    ).get_text(strip=True)
                                    if map_config.get("ano_inicio")
                                    and item.select_one(map_config["ano_inicio"])
                                    else ""
                                )

                                start_year = None
                                end_year = None

                                if ano_text:
                                    years = [y.strip() for y in ano_text.split(">")]
                                    if len(years) >= 1 and years[0] and years[0] != "-":
                                        start_year = self.parse_year(years[0])
                                    if len(years) >= 2 and years[1] and years[1] != "-":
                                        end_year = self.parse_year(years[1])

                                res = {
                                    "brand": brand,
                                    "name": name,
                                    "model": model,
                                    "engineName": engine,
                                    "engineConfiguration": fuel,
                                    "note": obs,
                                    "startYear": start_year,
                                    "endYear": end_year,
                                    "image": imagens[0] if imagens else None,
                                    "imageUrl": imagens[0] if imagens else None,
                                    "images": imagens,
                                    "originalNumbers": " | ".join(referencias),
                                    "crossReferences": " | ".join(referencias),
                                }

                                if res["brand"] or res["name"]:
                                    resultados.append(res)
                            except Exception as inner_e:
                                print(f"[DS] Erro ao processar linha: {inner_e}")
                                pass  # Linha inválida ou cabeçalho

                        if resultados:
                            print(
                                f"[DS] Sucesso! Extraídos {len(resultados)} itens de: {url}"
                            )
                            return [self.formatar_resultado(r) for r in resultados]
                        else:
                            print(f"[DS] Fim da tentativa para {url}. Itens válidos: 0")

                    except Exception as e:
                        print(f"[DS] Erro fatal ao tentar URL {url}: {e}")
                        import traceback

                        traceback.print_exc()
                        continue

            return []
