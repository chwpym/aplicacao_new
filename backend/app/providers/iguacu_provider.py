import httpx
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider
import logging

logger = logging.getLogger(__name__)

class IguacuProvider(BaseProvider):
    def __init__(self, config):
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        self.base_url = "https://www.iguacu.ind.br/busca"

    async def buscar(self, part_id: str):
        clean_id = part_id.strip().upper()
        results = []

        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
            try:
                # 1. GET para pegar os ViewStates
                resp_get = await client.get(self.base_url, headers=self.headers)
                if resp_get.status_code != 200:
                    logger.error(f"Iguacu: Erro no GET inicial ({resp_get.status_code})")
                    return []
                
                soup_get = BeautifulSoup(resp_get.text, "html.parser")
                viewstate = soup_get.find("input", {"id": "__VIEWSTATE"})
                viewstategen = soup_get.find("input", {"id": "__VIEWSTATEGENERATOR"})
                eventval = soup_get.find("input", {"id": "__EVENTVALIDATION"})

                # Extrair todos os inputs e selects do form original
                form_data = {}
                for input_tag in soup_get.find_all("input"):
                    name = input_tag.get("name")
                    if name:
                        val = input_tag.get("value", "")
                        form_data[name] = val
                for select_tag in soup_get.find_all("select"):
                    name = select_tag.get("name")
                    if name:
                        selected = select_tag.find("option", selected=True)
                        form_data[name] = selected["value"] if selected else "-1"

                if "BtnClear" in form_data:
                    del form_data["BtnClear"]

                # 2. POST (Primeiro tenta como Iguaçu, depois como Referência se não achar)
                async def do_search(tipo_busca):
                    payload = form_data.copy()
                    payload.update({
                        "__EVENTTARGET": "",
                        "__EVENTARGUMENT": "",
                        "TxtPesquisaCatalogo": clean_id,
                        "chks": tipo_busca,
                        "BtnPesquisa": "Pesquisar"
                    })
                    
                    headers_post = self.headers.copy()
                    headers_post["Content-Type"] = "application/x-www-form-urlencoded"
                    headers_post["Origin"] = "https://www.iguacu.ind.br"
                    headers_post["Referer"] = "https://www.iguacu.ind.br/busca"
                    
                    print(f"Iguacu Debug: Enviando POST com chks={tipo_busca} e TxtPesquisaCatalogo={clean_id}")
                    return await client.post(self.base_url, data=payload, headers=headers_post)

                resp_post = await do_search("RB_Iguacu")
                print(f"Iguacu Debug: Retorno do POST RB_Iguacu status={resp_post.status_code}, tamanho={len(resp_post.text)}")
                
                # O retorno é um mix de UpdatePanel, mas podemos parsear como HTML relaxado
                if "GridReferencia" not in resp_post.text:
                    print(f"Iguacu Debug: Nao achou GridReferencia no RB_Iguacu, tentando RB_Outros...")
                    resp_post = await do_search("RB_Outros")
                    print(f"Iguacu Debug: Retorno do POST RB_Outros status={resp_post.status_code}, tamanho={len(resp_post.text)}")

                if resp_post.status_code != 200:
                    logger.error(f"Iguacu: Erro no POST ({resp_post.status_code})")
                    return []

                soup = BeautifulSoup(resp_post.text, "html.parser")
                grid = soup.find("table", {"id": "GridReferencia"})
                if not grid:
                    return []

                rows = grid.find_all("tr")
                if len(rows) <= 1:
                    return []

                # CABEÇALHOS: 0:IMAGEM | 1:MONTADORA | 2:REFERENCIA | 3:CÓD. IGUAÇU | 4:VEICULO | 5:MOTOR | 6:COMB. | 7:OBS. | 8:ANO
                for row in rows[1:]:
                    cols = row.find_all(["td", "th"])
                    if len(cols) < 9:
                        continue

                    # Extrai imagem se houver
                    img_tag = cols[0].find("img")
                    imagem = f"https://www.iguacu.ind.br/{img_tag['src']}" if img_tag and "src" in img_tag.attrs else ""

                    montadora = cols[1].text.strip()
                    referencia = cols[2].text.strip()
                    codigo_iguacu = cols[3].text.strip()
                    veiculo = cols[4].text.strip()
                    motor = cols[5].text.strip()
                    comb = cols[6].text.strip()
                    obs = cols[7].text.strip()
                    ano = cols[8].text.strip()

                    app_data = {
                        "marca": "IGUAÇU",
                        "codigo": codigo_iguacu,
                        "montadora": montadora,
                        "modelo": veiculo,
                        "motor": motor,
                        "combustivel": comb,
                        "observacao": obs,
                        "imagem": imagem,
                        "referencias": referencia
                    }

                    # Parse ano (ex: "03 03", "02 06", "15 >", "16->", "12-17", "16")
                    if ano and ano != "&nbsp;":
                        ano_clean = ano.replace("&gt;", ">").strip()
                        
                        def _format_year(val_str):
                            val_str = val_str.strip()
                            if val_str.isdigit():
                                if len(val_str) == 2:
                                    num = int(val_str)
                                    return f"20{val_str}" if num < 50 else f"19{val_str}"
                                elif len(val_str) == 4:
                                    return val_str
                            return None

                        if ">" in ano_clean:
                            # Ano inicio em diante (ex: "15 >", "16->", "2015 >")
                            start_part = ano_clean.split(">")[0].replace("->", "").replace("-", "").strip()
                            parsed_start = _format_year(start_part)
                            if parsed_start:
                                app_data["ano_inicio"] = parsed_start
                        elif "-" in ano_clean:
                            # Intervalo com hífen (ex: "12-17", "2012-2017")
                            parts = ano_clean.split("-")
                            if len(parts) == 2:
                                s_year = _format_year(parts[0])
                                e_year = _format_year(parts[1])
                                if s_year:
                                    app_data["ano_inicio"] = s_year
                                if e_year:
                                    app_data["ano_fim"] = e_year
                        else:
                            # Separado por espaço (ex: "03 03", "02 06", "2003 2006") ou ano único ("16")
                            parts = ano_clean.split()
                            if len(parts) == 2:
                                s_year = _format_year(parts[0])
                                e_year = _format_year(parts[1])
                                if s_year:
                                    app_data["ano_inicio"] = s_year
                                if e_year:
                                    app_data["ano_fim"] = e_year
                            elif len(parts) == 1:
                                s_year = _format_year(parts[0])
                                if s_year:
                                    app_data["ano_inicio"] = s_year
                                    app_data["ano_fim"] = s_year

                    results.append(self.formatar_resultado(app_data))

                return results

            except Exception as e:
                logger.error(f"Iguacu: Erro ao buscar {part_id}: {str(e)}")
                return []
