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

                    # Parse ano (ex: 16->, 12-17)
                    if ano and ano != "&nbsp;":
                        if "->" in ano or "-" in ano and ">" in ano:
                            start_str = ano.replace("->", "").replace(">", "").replace("-", "").strip()
                            if len(start_str) == 2 and start_str.isdigit():
                                app_data["ano_inicio"] = f"20{start_str}" if int(start_str) < 50 else f"19{start_str}"
                        elif "-" in ano:
                            parts = ano.split("-")
                            if len(parts) == 2:
                                start_str = parts[0].strip()
                                end_str = parts[1].strip()
                                if len(start_str) == 2 and start_str.isdigit():
                                    app_data["ano_inicio"] = f"20{start_str}" if int(start_str) < 50 else f"19{start_str}"
                                if len(end_str) == 2 and end_str.isdigit():
                                    app_data["ano_fim"] = f"20{end_str}" if int(end_str) < 50 else f"19{end_str}"
                        else:
                            # Ano unico ex: "16"
                            if len(ano) == 2 and ano.isdigit():
                                app_data["ano_inicio"] = f"20{ano}" if int(ano) < 50 else f"19{ano}"
                                app_data["ano_fim"] = app_data["ano_inicio"]

                    results.append(self.formatar_resultado(app_data))

                return results

            except Exception as e:
                logger.error(f"Iguacu: Erro ao buscar {part_id}: {str(e)}")
                return []
