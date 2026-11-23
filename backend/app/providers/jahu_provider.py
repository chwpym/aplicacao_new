import httpx
import json
import re
import logging
import asyncio
from typing import List, Dict, Any
from app.providers.base_provider import BaseProvider
from app.services.normalization_service import normalization_service

# Configura o logger para registrar eventos e erros deste provedor
logger = logging.getLogger(__name__)

class JahuProvider(BaseProvider):
    """
    Provedor nativo para extração e normalização de dados do catálogo da Jahu Borrachas.
    
    Como funciona:
    1. Realiza um handshake assíncrono para login público na API do e-commerce WMW (b2b.jahu.com.br)
       para receber o sessionId e o cookie de sessão 'JSESSIONID'.
    2. Faz a busca por código de peça na API de busca paginada da Jahu.
    3. Para o produto encontrado, consulta os detalhes ricos pela chave primária (cdProduto).
    4. Limpa e processa a tabela HTML de aplicações do veículo.
    5. Padroniza e normaliza todas as referências cruzadas e dados FIPE.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o provedor com as configurações do banco de dados.
        """
        self.config = config
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://b2b.jahu.com.br",
            "Referer": "https://b2b.jahu.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        }
        
        # URLs de serviço mapeadas durante a engenharia reversa
        self.login_url = "https://b2b.jahu.com.br/server/public/service/auth/loginAcessoPublico"
        self.search_url = "https://b2b.jahu.com.br/server/public/service/produto/findProdutoList/produtoController/findAllByExampleByPages"
        self.details_url = "https://b2b.jahu.com.br/server/public/service/query/execute/produtoController/findProdutoByPrimaryKey"

    async def buscar(self, id_peca: str) -> List[Dict[str, Any]]:
        """
        Método obrigatório do BaseProvider. Realiza a busca assíncrona por código.
        """
        if not id_peca:
            return []

        # Normaliza o código para cobrir variações de pontuação (ex: 21570-4 -> 215704)
        codigos_busca = self.normalizar_codigo(id_peca)
        resultados = []

        # Usamos o AsyncClient do httpx com cookies habilitados
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
            try:
                # ----------------------------------------------------
                # PASSO 1: Handshake de Login Público Anônimo
                # ----------------------------------------------------
                # O servidor da Jahu exige uma sessão autenticada (mesmo que pública)
                # para evitar o bloqueio de "406 Sessão expirada".
                payload_login = {
                    "host": "https://b2b.jahu.com.br",
                    "usuario": {
                        "cdSistema": 50,
                        "flAtivo": "S"
                    }
                }
                
                resp_login = await client.post(self.login_url, json=payload_login, headers=self.headers)
                if resp_login.status_code != 200:
                    logger.error(f"[Jahu] Falha no handshake de login público: {resp_login.status_code}")
                    return []
                
                login_data = resp_login.json()
                session_id = login_data.get("sessionId")
                if not session_id:
                    logger.error("[Jahu] ID de sessão não retornado pela API de login")
                    return []

                cd_empresa = str(login_data.get("empresa", {}).get("cdEmpresa") or login_data.get("cliente", {}).get("cdEmpresa") or "1")
                cd_cliente = str(login_data.get("cliente", {}).get("cdCliente") or "700000")
                cd_grupo = str(login_data.get("cliente", {}).get("cdGrupoCliente") or "101")
                
                logger.info(f"[Jahu] Handshake bem-sucedido! SessionId={session_id}, emp={cd_empresa}, grp={cd_grupo}")

                # ----------------------------------------------------
                # PASSO 2: Busca por Código (para cada variação de código)
                # ----------------------------------------------------
                for cod in codigos_busca:
                    payload_search = {
                        "cdEmpresa": cd_empresa,
                        "cdClienteFilter": cd_cliente,
                        "clienteEmpresa": {"vlIndiceCliente": 1},
                        "cdGrupoClienteFilter": cd_grupo,
                        "dsPalavraChave": cod,
                        "opcaoFiltro": "1",
                        "pageLines": 16,
                        "currentPage": 1,
                        "filtros": {},
                        "sortColumns": "2-PRODUTO-1",
                        "session": {
                            "cdSistema": 50,
                            "sessionId": session_id,
                            "isUsuarioAnomimo": True,
                            "usuario": {"cdUsuario": "PUBLICO"}
                        },
                        "flAtivo": "S"
                    }

                    resp_search = await client.post(self.search_url, json=payload_search, headers=self.headers)
                    if resp_search.status_code != 200:
                        logger.warning(f"[Jahu] Busca falhou com status {resp_search.status_code} para o código {cod}")
                        continue

                    search_data = resp_search.json()
                    collections = search_data.get("collections", [])
                    if not collections or not collections[0]:
                        # Se não encontrar resultados para essa variação, tenta a próxima
                        continue

                    products = collections[0]
                    logger.info(f"[Jahu] Encontrado(s) {len(products)} correspondente(s) para o termo '{cod}'")

                    # O OpenSearch da Jahu faz busca aproximada (fuzzy). Seleciona apenas item com correspondência real.
                    cod_clean = re.sub(r'[^A-Z0-9]', '', cod.upper())
                    prod = None
                    for candidate in products:
                        cand_cd = re.sub(r'[^A-Z0-9]', '', str(candidate.get("cdProduto", "")).upper())
                        cand_info = re.sub(r'[^A-Z0-9]', '', str(candidate.get("infoBusca", "")).upper())
                        if cand_cd == cod_clean or (cod_clean and (cod_clean in cand_cd or cod_clean in cand_info)):
                            prod = candidate
                            break

                    if not prod:
                        logger.info(f"[Jahu] Nenhum match exato encontrado para '{cod}' entre os {len(products)} retornados")
                        continue

                    cd_prod = prod.get("cdProduto")
                    ds_prod = prod.get("dsProduto")
                    brand_search = prod.get("marca", {}).get("dsMarca", "JAHU")
                    cat_list = prod.get("produtoCategoriaList") or []
                    cd_dept = (cat_list[0].get("cdDepartamento") if cat_list else None) or prod.get("cdDepartamento") or "DEPARTAMENTO"
                    cd_cat = (cat_list[0].get("cdCategoria") if cat_list else None) or prod.get("cdCategoria") or ""

                    # ----------------------------------------------------
                    # PASSO 3: Consulta de Detalhes ricos (PrimaryKey)
                    # ----------------------------------------------------
                    payload_details = {
                        "cdEmpresa": cd_empresa,
                        "cdClienteFilter": cd_cliente,
                        "cdGrupoClienteFilter": cd_grupo,
                        "cdProduto": cd_prod,
                        "cdDepartamento": cd_dept,
                        "cdCategoria": cd_cat,
                        "sortColumns": "TB.CDCATEGORIA3 DESC, TB.CDCATEGORIA2 DESC, LOCALESTOQUE.NUORDEM, LOCALESTOQUE.DSLOCALESTOQUE",
                        "session": {
                            "cdSistema": 50,
                            "sessionId": session_id,
                            "isUsuarioAnomimo": True,
                            "usuario": {"cdUsuario": "PUBLICO"}
                        },
                        "flAtivo": "S"
                    }

                    resp_det = await client.post(self.details_url, json=payload_details, headers=self.headers)
                    if resp_det.status_code != 200 or not resp_det.text.strip():
                        logger.warning(f"[Jahu] Falha ao recuperar detalhes ricos do produto {cd_prod} (status={resp_det.status_code}, len={len(resp_det.text)})")
                        continue

                    det_data = resp_det.json()
                    campos = det_data.get("camposDinamicos", {})

                    # Extrai dados estendidos do painel dinâmico da WMW
                    original_code = campos.get("AD_CODORIG", "") # Códigos originais de montadora
                    ref_forn = campos.get("AD_REFFORN", "").strip() # Referência técnica do fornecedor
                    brand_name = campos.get("AD_DSMARCA", brand_search) # Marca refinada
                    ncm = campos.get("AD_NCM", "") # NCM fiscal
                    info_ad = campos.get("AD_INFOAD", "") # Informações de fitment livre
                    applications_html = campos.get("AD_DSAPLICACAO", "") # Tabela HTML com veículos
                    conversao_html = campos.get("AD_CONVERSAO", "") # Tabela HTML de conversão/equivalências

                    # ----------------------------------------------------
                    # PASSO 4: Múltiplas Imagens (Galeria) via HEAD Concorrente
                    # ----------------------------------------------------
                    # O e-commerce da Jahu possui URLs de imagens em um carrossel de 1 a 6.
                    # Analisando as respostas: fotos válidas retornam 'image/jpeg' e placeholders
                    # de 'sem imagem' retornam 'image/png'. Usamos HEAD/GET concorrente para filtrar.
                    images_list = []
                    image_url = ""
                    fl_foto = prod.get("flFoto", "N")

                    if fl_foto == "S" and cd_prod:
                        try:
                            # Dispara requisições GET leves concorrentes para os 6 possíveis slots
                            tasks = []
                            for i in range(1, 7):
                                url_foto = f"https://b2b.jahu.com.br/server/public/service/images/get/produtoFoto/[{cd_empresa},{cd_prod},L,{i}]/false/false"
                                tasks.append(client.get(url_foto, headers=self.headers, timeout=5.0))
                            
                            # asyncio.gather executa tudo em paralelo de forma ultra ágil
                            resps = await asyncio.gather(*tasks, return_exceptions=True)
                            
                            for idx, resp in enumerate(resps):
                                if isinstance(resp, httpx.Response) and resp.status_code == 200:
                                    content_type = resp.headers.get("Content-Type", "")
                                    # Se a imagem for real do produto, ela é jpeg. Se for placeholder, é png.
                                    if "image/jpeg" in content_type:
                                        img_valida = f"https://b2b.jahu.com.br/server/public/service/images/get/produtoFoto/[{cd_empresa},{cd_prod},L,{idx+1}]/false/false"
                                        images_list.append(img_valida)
                            
                            if images_list:
                                image_url = images_list[0] # A principal é a primeira da galeria
                            else:
                                # Fallback estático caso não consiga mapear via galeria
                                image_url = f"https://b2b.jahu.com.br/server/imagens/produtos/{cd_prod}.jpg"
                                images_list = [image_url]
                        except Exception as img_err:
                            logger.warning(f"[Jahu] Falha ao verificar galeria de imagens para {cd_prod}: {img_err}")
                            image_url = f"https://b2b.jahu.com.br/server/imagens/produtos/{cd_prod}.jpg"
                            images_list = [image_url]

                    # ----------------------------------------------------
                    # PASSO 5: Busca Automática de Similares da Marca (Crossover)
                    # ----------------------------------------------------
                    # Buscamos em segundo plano todos os produtos da própria Jahu que compartilham
                    # o mesmo código original (equivalência direta do catálogo Jahu).
                    is_outra_marca = bool(brand_name and brand_name.strip().upper() != "JAHU" and ref_forn)
                    codigo_principal = ref_forn.strip().upper() if is_outra_marca else cd_prod

                    similares_encontrados = set()
                    similares_fabricantes = set()
                    if is_outra_marca and cd_prod:
                        similares_encontrados.add(cd_prod)
                    if original_code:
                        try:
                            codigos_originais_lista = [c.strip() for c in original_code.split('\n') if c.strip()]
                            for cd_orig in codigos_originais_lista:
                                cd_orig_clean = re.sub(r'[^A-Z0-9]', '', cd_orig.upper())
                                payload_similares = {
                                    "cdEmpresa": cd_empresa,
                                    "cdClienteFilter": cd_cliente,
                                    "clienteEmpresa": {"vlIndiceCliente": 1},
                                    "cdGrupoClienteFilter": cd_grupo,
                                    "dsPalavraChave": cd_orig,
                                    "opcaoFiltro": "1",
                                    "pageLines": 10,
                                    "currentPage": 1,
                                    "filtros": {},
                                    "sortColumns": "2-PRODUTO-1",
                                    "session": {
                                        "cdSistema": 50,
                                        "sessionId": session_id,
                                        "isUsuarioAnomimo": True,
                                        "usuario": {"cdUsuario": "PUBLICO"}
                                    },
                                    "flAtivo": "S"
                                }
                                resp_sim = await client.post(self.search_url, json=payload_similares, headers=self.headers, timeout=10.0)
                                if resp_sim.status_code == 200:
                                    sim_data = resp_sim.json()
                                    sim_collections = sim_data.get("collections", [])
                                    if sim_collections and sim_collections[0]:
                                        for p_sim in sim_collections[0]:
                                            cd_sim = p_sim.get("cdProduto")
                                            info_raw = str(p_sim.get("infoBusca", ""))
                                            info_sim = re.sub(r'[^A-Z0-9]', '', info_raw.upper())
                                            # Evita adicionar o próprio produto e filtra falsos positivos do OpenSearch
                                            if cd_sim and cd_sim != cd_prod and cd_orig_clean and cd_orig_clean in info_sim:
                                                similares_encontrados.add(cd_sim)
                                                info_parts = [x.strip() for x in info_raw.split("|")]
                                                marca_sim = (p_sim.get("marca", {}).get("dsMarca") or (info_parts[6] if len(info_parts) > 6 else "") or "JAHU").strip().upper()
                                                ref_forn_sim = (info_parts[3] if len(info_parts) > 3 else "").strip().upper()
                                                if ref_forn_sim and (marca_sim != "JAHU" or re.sub(r'[^A-Z0-9]', '', ref_forn_sim) != re.sub(r'[^A-Z0-9]', '', str(cd_sim).upper())):
                                                    similares_fabricantes.add(f"{marca_sim}: {ref_forn_sim}")
                        except Exception as sim_err:
                            logger.warning(f"[Jahu] Falha ao recuperar produtos similares por crossover: {sim_err}")

                    # ----------------------------------------------------
                    # PASSO 6: Consolidação de Referências Cruzadas
                    # ----------------------------------------------------
                    ref_list = det_data.get("referenciaProdutoList", [])
                    ref_str_parts = []
                    for ref in ref_list:
                        ds_ref = ref.get("dsReferencia", "")
                        ds_marca_ref = ref.get("dsMarca", "")
                        if ds_ref:
                            if ds_marca_ref:
                                ref_str_parts.append(f"{ds_marca_ref.strip().upper()}: {ds_ref.strip()}")
                            else:
                                ref_str_parts.append(f"ORIGINAL: {ds_ref.strip()}")

                    # Se o próprio produto buscado for de outra marca distribuída pela Jahu (ex: AXIOS: LT70139)
                    if ref_forn and brand_name and re.sub(r'[^A-Z0-9]', '', ref_forn.upper()) != re.sub(r'[^A-Z0-9]', '', str(cd_prod or "").upper()):
                        ref_str_parts.append(f"{brand_name.strip().upper()}: {ref_forn.strip().upper()}")

                    # Extrai referências cruzadas da tabela HTML AD_CONVERSAO (aba CONVERSÃO)
                    if conversao_html:
                        conv_trs = re.findall(r'<tr.*?>(.*?)</tr>', conversao_html, re.DOTALL | re.IGNORECASE)
                        for conv_tr in conv_trs:
                            conv_tds = re.findall(r'<td.*?>(.*?)</td>', conv_tr, re.DOTALL | re.IGNORECASE)
                            if len(conv_tds) >= 2:
                                forn_conv = re.sub(r'<[^>]+>', '', conv_tds[0]).strip().upper()
                                cod_conv = re.sub(r'<[^>]+>', '', conv_tds[1]).strip()
                                if forn_conv and cod_conv:
                                    ref_str_parts.append(f"{forn_conv}: {cod_conv}")
                    
                    # Injeta os similares da própria Jahu e fabricantes distribuídos nas referências para o frontend renderizar o 'raio'
                    for sku_sim in sorted(list(similares_encontrados)):
                        ref_str_parts.append(f"JAHU: {sku_sim}")
                    for fab_ref in sorted(list(similares_fabricantes)):
                        ref_str_parts.append(fab_ref)

                    original_lines = []
                    if original_code:
                        for line in original_code.split('\n'):
                            c_orig = line.strip()
                            if c_orig:
                                original_lines.append(f"ORIGINAL: {c_orig}")

                    all_refs = original_lines + ref_str_parts
                    references_combined = " | ".join(all_refs)

                    # Ficha técnica estendida
                    ficha_tecnica = {
                        "NCM": ncm,
                        "REF_FORNECEDOR": ref_forn,
                        "INFO_ADICIONAL": info_ad
                    }
                    unidade_list = det_data.get("produtoUnidadeList") or prod.get("produtoUnidadeList") or []
                    if unidade_list and isinstance(unidade_list, list):
                        multiplo = unidade_list[0].get("nuMultiploEspecial")
                        if multiplo is not None:
                            ficha_tecnica["MULTIPLO"] = str(multiplo)
                    nu_cd_barras = det_data.get("nuCdBarras")
                    if nu_cd_barras:
                        ficha_tecnica["CODIGO_BARRAS"] = str(nu_cd_barras).strip()

                    # ----------------------------------------------------
                    # PASSO 7: Parser e Pré-separação de Motorização/Aplicações
                    # ----------------------------------------------------
                    trs = re.findall(r'<tr.*?>(.*?)</tr>', applications_html, re.DOTALL | re.IGNORECASE)
                    
                    apps_list = []
                    if trs:
                        header_tds = re.findall(r'<th.*?>(.*?)</th>', trs[0], re.DOTALL | re.IGNORECASE)
                        if not header_tds:
                            header_tds = re.findall(r'<td.*?>(.*?)</td>', trs[0], re.DOTALL | re.IGNORECASE)
                        
                        headers_clean = [re.sub(r'<[^>]+>', '', h).strip().upper() for h in header_tds]

                        for tr in trs[1:]:
                            tds = re.findall(r'<td.*?>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
                            if tds:
                                tds_clean = [re.sub(r'<[^>]+>', '', t).strip() for t in tds]
                                app_row = dict(zip(headers_clean, tds_clean))
                                apps_list.append(app_row)

                    if not apps_list:
                        app_data = {
                            "marca": brand_name,
                            "codigo": codigo_principal,
                            "montadora": "",
                            "modelo": ds_prod,
                            "versao": "",
                            "motor": "",
                            "configuracao_motor": "",
                            "ano_inicio": "",
                            "ano_fim": "",
                            "descricao_produto": ds_prod,
                            "observacao": info_ad,
                            "imagem": image_url,
                            "imagens": images_list,
                            "referencias": references_combined,
                            "ficha_tecnica": ficha_tecnica
                        }
                        resultados.append(self.formatar_resultado(app_data))
                    else:
                        norm_cache = {}

                        for app in apps_list:
                            montadora_raw = app.get("MONTADORA", "").strip()
                            veiculo_raw = app.get("VEICULO", "").strip()
                            modelo_raw = app.get("MODELO", "").strip()
                            de_raw = app.get("DE", "").strip()
                            ate_raw = app.get("ATÉ", app.get("ATE", "")).strip()

                            if not montadora_raw and not veiculo_raw:
                                continue

                            cache_key = f"{montadora_raw}|{veiculo_raw}"

                            # Inteligência de motorização: Pré-extrai motor/versão usando o serviço oficial
                            motor_extraido = ""
                            config_extraida = ""
                            versao_limpa = modelo_raw

                            if modelo_raw:
                                try:
                                    m_p, c_p, residuo = normalization_service.extrair_motorizacao(modelo_raw)
                                    if m_p or c_p:
                                        motor_extraido = m_p
                                        config_extraida = c_p
                                        versao_limpa = residuo
                                except Exception as ext_err:
                                    logger.warning(f"[Jahu] Falha ao pré-extrair motor para '{modelo_raw}': {ext_err}")

                            app_data = {
                                "marca": brand_name,
                                "codigo": codigo_principal,
                                "montadora": montadora_raw,
                                "modelo": veiculo_raw,
                                "versao": versao_limpa,
                                "motor": motor_extraido,
                                "configuracao_motor": config_extraida,
                                "ano_inicio": de_raw,
                                "ano_fim": ate_raw,
                                "descricao_produto": ds_prod,
                                "observacao": info_ad,
                                "imagem": image_url,
                                "imagens": images_list,
                                "referencias": references_combined,
                                "ficha_tecnica": ficha_tecnica
                            }

                            if cache_key in norm_cache:
                                montadora_padronizada, modelo_fipe = norm_cache[cache_key]
                                app_data["montadora"] = montadora_padronizada
                                app_data["modelo"] = modelo_fipe
                                resultados.append(self.formatar_resultado(app_data, skip_automaker=True))
                            else:
                                res_formatado = self.formatar_resultado(app_data)
                                norm_cache[cache_key] = (res_formatado["veiculo"], res_formatado["modelo"])
                                resultados.append(res_formatado)

                    # Se já obtivemos resultados válidos para este código, podemos
                    # retornar imediatamente e evitar buscas desnecessárias nas variações secundárias
                    if resultados:
                        # Adiciona a resposta bruta completa no primeiro registro para visualização no Playground
                        resultados[0]["raw_response"] = json.dumps(det_data, indent=2, ensure_ascii=False)
                        return resultados

            except Exception as e:
                logger.error(f"[Jahu] Erro inesperado ao processar busca por '{id_peca}': {repr(e)}")
                
        return resultados
