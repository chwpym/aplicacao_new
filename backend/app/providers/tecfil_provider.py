from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
from .base_provider import BaseProvider


class TecfilProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://tecfil-catalago.gruposofape.com.br/CatalogoTecfil"
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            verify=False,
            timeout=15.0,
            follow_redirects=True,
        )

    async def fechar(self):
        await self.client.aclose()

    async def buscar(self, codigo: str) -> List[Dict[str, Any]]:
        resultados = []
        codigo_buscado = codigo.strip().upper()

        endpoints_map = {
            "Automóveis": "resultadoAutomoveis.xhtml",
            "Caminhões": "resultadoCaminhoes.xhtml",
            "Ônibus": "resultadoOnibus.xhtml",
            "Tratores": "resultadoTratores.xhtml",
            "Colheitadeiras": "resultadoColheitadeiras.xhtml",
            "Motocicletas": "resultadoMotocicletas.xhtml",
            "Máquinas e Equipamentos": "resultadoMaquinasEquipamentos.xhtml",
            "Marítima": "resultadoMaritima.xhtml",
        }

        try:
            # 1. Start Session & POST
            res_index = await self.client.get(f"{self.base_url}/index.xhtml")
            soup_index = BeautifulSoup(res_index.text, "html.parser")

            form_index = soup_index.find("form", id="j_idt94") or soup_index.find(
                "form"
            )
            vs_input = (
                form_index.find("input", {"name": "javax.faces.ViewState"})
                if form_index
                else None
            )
            view_state_index = vs_input["value"] if vs_input else ""

            data_index = {
                "j_idt94": "j_idt94",
                "j_idt94:termoConsulta1": codigo_buscado,
                "j_idt94:botaoTermoConsulta1": "Search",
                "javax.faces.ViewState": view_state_index,
            }
            res_search = await self.client.post(
                f"{self.base_url}/index.xhtml", data=data_index
            )

            # 2. Get Categories to know which endpoints to visit
            soup = BeautifulSoup(res_search.text, "html.parser")
            buttons = soup.find_all("input", type="submit")
            categories_to_fetch = []

            for btn in buttons:
                val = btn.get("value", "")
                match = re.search(r"Total Resultados\s*\[\s*(\d+)\s*\]", val)
                if match and int(match.group(1)) > 0:
                    row = btn.find_parent("div", class_="row")
                    label = (
                        row.find("label").text.strip().replace(":", "")
                        if row and row.find("label")
                        else ""
                    )

                    if label in endpoints_map:
                        categories_to_fetch.append(
                            {"label": label, "endpoint": endpoints_map[label]}
                        )

            print(
                f"[TECFIL] Categorias ativas para {codigo_buscado}: {[c['label'] for c in categories_to_fetch]}"
            )

            if not categories_to_fetch:
                return []

            # 3. Handle data extraction using pure HTTP and overriding PrimeFaces pagination limits
            for cat in categories_to_fetch:
                print(
                    f"[TECFIL] Extraindo {cat['label']} via POST Pagination Override..."
                )

                # Fetch first page to grab ViewState and set session context
                res_cat = await self.client.get(
                    f"{self.base_url}/{cat['endpoint']}?search-term={codigo_buscado}"
                )

                if res_cat.status_code != 200:
                    print(f"  -> Falha {res_cat.status_code}")
                    continue

                soup_cat = BeautifulSoup(res_cat.text, "html.parser")
                vs_input = soup_cat.find("input", {"name": "javax.faces.ViewState"})
                current_vs = vs_input["value"] if vs_input else view_state_index

                # Serialize the full form to ensure PrimeFaces accepts our AJAX request
                form = soup_cat.find("form")
                payload = {}
                if form:
                    for inp in form.find_all(["input", "select"]):
                        name = inp.get("name")
                        if name:
                            value = inp.get("value", "")
                            if inp.name == "select":
                                selected = inp.find("option", selected=True)
                                if selected:
                                    value = selected.get("value", "")
                            payload[name] = value

                def parse_table_rows(html_content, is_soup=False):
                    if is_soup:
                        frag_soup = html_content
                    else:
                        frag_soup = BeautifulSoup(html_content, "html.parser")

                    # O PrimeFaces pode retornar <tbody> direto, ou <table>, ou nada (apenas <tr...>)
                    # Vamos varrer a string inteira em busca de <tr> que contenham a classe da matriz
                    trows = frag_soup.find_all(
                        "tr",
                        class_=lambda c: c
                        and "ui-widget-content" in c
                        and "ui-datatable-empty-message" not in c,
                    )

                    for r in trows:
                        cells = r.find_all("td")
                        if len(cells) >= 7:
                            montadora = cells[0].text.strip()
                            modelo = cells[1].text.strip()
                            motor = cells[2].text.strip()
                            ano_ini = cells[3].text.strip()
                            ano_fim = cells[4].text.strip()
                            desc = cells[5].text.strip()
                            combustivel = cells[6].text.strip()
                            config_motor = combustivel if combustivel else motor
                            observacao = f"Categoria: {cat['label']}"
                            imagem_url = f"https://www.tecfil.com.br/imagens/tecfil/{codigo_buscado}A.jpg"

                            raw = {
                                "brand": "TECFIL",
                                "codigo": codigo_buscado,
                                "veiculo": montadora,
                                "modelo": modelo,
                                "versao": desc,
                                "motor": motor,
                                "configuracao_motor": config_motor,
                                "ano_inicio": ano_ini,
                                "ano_fim": ano_fim,
                                "observacao": observacao,
                                "imagem": imagem_url,
                            }
                            resultados.append(self.formatar_resultado(raw))

                # Extrair página 1 direto do GET
                parse_table_rows(soup_cat, is_soup=True)

                # Detectar paginador
                paginator_current = soup_cat.find("span", class_="ui-paginator-current")
                total_pages = 1
                if paginator_current:
                    match = re.search(r"\(1 of (\d+)\)", paginator_current.text)
                    if match:
                        total_pages = int(match.group(1))

                if total_pages > 1:
                    print(
                        f"    -> Paginador detectado: {total_pages} páginas em {cat['label']}."
                    )
                    for page_num in range(1, total_pages):
                        first_index = page_num * 20

                        # Re-extrair inputs da página mais recente a cada loop (importante para manter ViewState dinâmico)
                        page_payload = {}
                        if form:
                            for inp in form.find_all(["input", "select"]):
                                name = inp.get("name")
                                if name:
                                    value = inp.get("value", "")
                                    if inp.name == "select":
                                        selected = inp.find("option", selected=True)
                                        if selected:
                                            value = selected.get("value", "")
                                    page_payload[name] = value

                        page_payload.update(
                            {
                                "javax.faces.ViewState": current_vs,
                                "javax.faces.partial.ajax": "true",
                                "javax.faces.source": "form:aplicacao",
                                "javax.faces.partial.execute": "form:aplicacao",
                                "javax.faces.partial.render": "form:aplicacao",
                                "form:aplicacao": "form:aplicacao",
                                "form:aplicacao_pagination": "true",
                                "form:aplicacao_first": str(first_index),
                                "form:aplicacao_rows": "20",
                                "form:aplicacao_skipChildren": "true",
                                "form:aplicacao_encodeFeature": "true",
                                "javax.faces.behavior.event": "page",
                            }
                        )

                        res_ajax = await self.client.post(
                            f"{self.base_url}/{cat['endpoint']}",
                            data=page_payload,
                            headers={
                                "Faces-Request": "partial/ajax",
                                "X-Requested-With": "XMLHttpRequest",
                            },
                        )

                        if res_ajax.status_code == 200:
                            # Update ViewState se o JSF responder com um novo
                            vs_match = re.search(
                                r'<update id="[^"]*javax\.faces\.ViewState[^"]*"><!\[CDATA\[(.*?)\]\]></update>',
                                res_ajax.text,
                            )
                            if vs_match:
                                current_vs = vs_match.group(1)

                            update_match = re.search(
                                r'<update id="form:aplicacao"><!\[CDATA\[(.*?)\]\]></update>',
                                res_ajax.text,
                                re.DOTALL,
                            )
                            if update_match:
                                xml_str = update_match.group(1)
                                parse_table_rows(xml_str, is_soup=False)
                            else:
                                print(
                                    f"    -> falha ao isolar XML da página {page_num + 1}"
                                )
                        else:
                            print(
                                f"    -> requisição da página {page_num + 1} falhou com status {res_ajax.status_code}"
                            )

            # Deduplicate
            resultados_unicos = []
            vistos = set()
            for r in resultados:
                chave = f"{r['veiculo']}|{r['modelo']}|{r.get('versao', '')}|{r['motor']}|{r.get('ano_inicio', '')}|{r.get('ano_fim', '')}|{r['configuracao_motor']}|{r.get('observacao', '')}"
                if chave not in vistos:
                    vistos.add(chave)
                    resultados_unicos.append(r)

            return resultados_unicos

        except Exception as e:
            print(f"[TECFIL] Erro crítico no provider: {str(e)}")
            return []
