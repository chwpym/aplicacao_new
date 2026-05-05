import httpx
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.providers.base_provider import BaseProvider

class MultiqualitaProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://multiqualita.com.br",
            "Referer": "https://multiqualita.com.br/"
        }

    async def buscar(self, part_id: str) -> List[Dict[str, Any]]:
        """
        Realiza a busca no catálogo Multiqualità via POST.
        """
        url = "https://multiqualita.com.br/MULTIQUALITA/sessioncode/?SESSION=WEB_LISTAPRODUTOS"
        payload = f"BUSCA_ALL={part_id}"

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.post(url, content=payload, headers=self.headers)
                if response.status_code != 200:
                    print(f"Erro Multiqualita: Status {response.status_code}")
                    return []

                return self._parse_html(response.text, part_id)
            except Exception as e:
                print(f"Erro ao buscar na Multiqualita: {e}")
                return []

    def _parse_html(self, html: str, part_id: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # Cada produto fica em um container .CADAPRODUTOX
        product_containers = soup.select(".CADAPRODUTOX")

        for container in product_containers:
            # Código da peça
            codigo_elem = container.select_one(".CODMULTIQUALITA")
            codigo = codigo_elem.text.strip() if codigo_elem else part_id

            # Descrição básica
            descricao_elem = container.select_one(".FIX_DESCRICAO")
            descricao = descricao_elem.text.strip() if descricao_elem else ""

            # Imagem
            img_elem = container.select_one("img[src*='/PRODS/medium/']")
            image_url = ""
            if img_elem and 'style' in img_elem.attrs:
                # Extrai a URL do background-image: url(...)
                match = re.search(r"url\('(.+?)'\)", img_elem['style'])
                if match:
                    image_url = f"https://multiqualita.com.br{match.group(1)}"
            elif codigo:
                 image_url = f"https://multiqualita.com.br/MULTIQUALITA/PRODS/medium/{codigo}_1.jpg"

            # Características e Referências via Labels (mais resiliente que IDs)
            caracteristicas = {}
            referencias = []
            
            labels = container.select(".TOR_ETIQ_ARTE")
            for label in labels:
                label_text = label.get_text(strip=True).upper()
                parent = label.find_parent("div")
                if not parent: continue
                
                if "CARACTER" in label_text:
                    char_items = parent.select(".NIGs")
                    for i, char in enumerate(char_items):
                        text = char.get_text(strip=True)
                        if text:
                            if ":" in text:
                                k, v = text.split(":", 1)
                                caracteristicas[k.strip().upper()] = v.strip().upper()
                            else:
                                # Usa o próprio texto como chave para aparecer limpo na tabela
                                # O valor "-" indica que a informação é o rótulo em si
                                caracteristicas[text.upper()] = "-"
                
                elif "REFER" in label_text:
                    ref_items = parent.select(".NIGs")
                    for ref in ref_items:
                        text = ref.get_text(strip=True)
                        if text:
                            # Adiciona prefixo SIMILAR para o frontend conseguir processar como par Marca: Código
                            referencias.append(f"SIMILAR: {text}")
                
                elif "BARRA" in label_text:
                    ean_item = parent.select_one(".NIGs")
                    if ean_item:
                        caracteristicas["EAN"] = ean_item.get_text(strip=True)

            # Aplicações (Veículos)
            aplicacoes_container = container.select_one(".FIX_APLICACOES")
            current_montadora = ""
            
            if aplicacoes_container:
                for child in aplicacoes_container.find_all('div', recursive=False):
                    classes = child.get('class', [])
                    text = child.get_text(strip=True)
                    if not text: continue
                    
                    if 'TOR_ETIQ_ARTE' in classes:
                        current_montadora = text
                    elif 'NIGs' in classes and current_montadora:
                        modelo = text
                        motor = ""
                        ano_inicio = ""
                        ano_fim = ""
                        
                        # Regex mais flexível para anos (pega qualquer seta unicode ou texto como ATÉ)
                        anos_match = re.search(r"(\d{4})\s*[^\d\s]{1,3}\s*(\d{4})?", text)
                        if anos_match:
                            ano_inicio = anos_match.group(1)
                            if anos_match.group(2):
                                ano_fim = anos_match.group(2)
                            text_sem_ano = text.replace(anos_match.group(0), "").strip()
                        else:
                            text_sem_ano = text
                            
                        motor_match = re.search(r"(\d\.\d.*)", text_sem_ano)
                        if motor_match:
                            motor = motor_match.group(1).strip()
                            modelo = text_sem_ano.replace(motor, "").strip()
                        else:
                            modelo = text_sem_ano
                        
                        res = {
                            "marca_peca": "MULTIQUALITÀ",
                            "codigo": codigo,
                            "montadora": current_montadora,
                            "modelo": modelo,
                            "motor": motor,
                            "motor_original": motor,
                            "ano_inicio": ano_inicio,
                            "ano_fim": ano_fim,
                            "imagem": image_url,
                            "referencias": referencias,
                            "ficha_tecnica": caracteristicas,
                            "observacao": descricao
                        }
                        items.append(self.formatar_resultado(res))
            
            if not items:
                items.append(self.formatar_resultado({
                    "marca_peca": "MULTIQUALITÀ",
                    "codigo": codigo,
                    "veiculo": descricao,
                    "imagem": image_url,
                    "referencias": referencias,
                    "ficha_tecnica": caracteristicas
                }))

        return items

    def formatar_resultado(self, raw_data, skip_automaker=False):
        res = super().formatar_resultado(raw_data, skip_automaker)
        
        if raw_data.get("motor_original"):
            res["motor"] = raw_data["motor_original"]
            
            if res["configuracao_motor"]:
                motor_original_upper = str(raw_data["motor_original"]).upper()
                config_upper = str(res["configuracao_motor"]).upper()
                
                if config_upper in motor_original_upper or motor_original_upper in config_upper:
                    res["configuracao_motor"] = ""
                else:
                    partes_motor = [p.strip() for p in motor_original_upper.split('/')]
                    nova_config = res["configuracao_motor"]
                    for p in partes_motor:
                        if len(p) > 1:
                            nova_config = nova_config.replace(p, "").strip()
                    res["configuracao_motor"] = nova_config

        return res
