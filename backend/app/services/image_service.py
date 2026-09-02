import io
from PIL import Image
from typing import Tuple, Optional
import httpx

class ImageProcessor:
    """
    Serviço para processamento de imagens sob demanda usando Pillow.
    Implementa redimensionamento, mudança de formato e adição de cor de fundo
    para compatibilidade com ERPs.
    """

    @staticmethod
    def process_image(
        image_bytes: bytes,
        formato_saida: str = "ORIGINAL",
        qualidade: int = 85,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        min_width: Optional[int] = 500,
        min_height: Optional[int] = 500,
        manter_proporcao: bool = True,
        cor_fundo_jpg: str = "#FFFFFF"
    ) -> Tuple[bytes, str]:
        """
        Processa os bytes de uma imagem aplicando as configurações de conversão.
        Retorna uma tupla (bytes_processados, media_type).
        """
        # Se for ORIGINAL, apenas retorna sem processar
        if formato_saida.upper() == "ORIGINAL":
            # Para retornar o media type correto, poderíamos ler o formato original,
            # mas vamos deixar o chamador resolver ou extrair básico do Pillow.
            try:
                with Image.open(io.BytesIO(image_bytes)) as img:
                    format_lower = img.format.lower() if img.format else "jpeg"
                    media_type = f"image/{format_lower}"
                    if format_lower == "jpg":
                        media_type = "image/jpeg"
            except Exception:
                media_type = "application/octet-stream"
            return image_bytes, media_type

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # 1. Aplicar Conversão de Cor de Fundo se o destino for JPG e a imagem tiver alpha/transparência
                if formato_saida.upper() in ["JPG", "JPEG"]:
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        # Cria um canvas na cor escolhida e cola a imagem por cima
                        background = Image.new("RGB", img.size, cor_fundo_jpg)
                        # Se for P (Palette) com transparência, precisa converter pra RGBA primeiro
                        img_rgba = img.convert("RGBA")
                        background.paste(img_rgba, mask=img_rgba.split()[3]) # Usa o canal Alpha como máscara
                        img = background
                    else:
                        img = img.convert("RGB") # Garante compatibilidade
                
                # 2. Redimensionamento
                if max_width or max_height:
                    orig_w, orig_h = img.size
                    target_w = max_width or orig_w
                    target_h = max_height or orig_h

                    if manter_proporcao:
                        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    else:
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 2.1 Preenchimento (Padding) para tamanho mínimo
                if min_width or min_height:
                    orig_w, orig_h = img.size
                    target_min_w = min_width or orig_w
                    target_min_h = min_height or orig_h

                    if orig_w < target_min_w or orig_h < target_min_h:
                        new_w = max(orig_w, target_min_w)
                        new_h = max(orig_h, target_min_h)
                        # Cria novo fundo
                        background = Image.new("RGB" if img.mode == "RGB" else "RGBA", (new_w, new_h), cor_fundo_jpg)
                        # Cola no centro
                        offset_x = (new_w - orig_w) // 2
                        offset_y = (new_h - orig_h) // 2
                        background.paste(img, (offset_x, offset_y))
                        if formato_saida.upper() in ["JPG", "JPEG"]:
                            img = background.convert("RGB")
                        else:
                            img = background

                # 3. Salvar no novo formato
                output_buffer = io.BytesIO()
                target_format = "JPEG" if formato_saida.upper() == "JPG" else formato_saida.upper()
                
                # O Pillow entende formatos como JPEG, PNG, WEBP.
                # Parâmetros de salvamento
                save_kwargs = {}
                if target_format in ["JPEG", "WEBP"]:
                    save_kwargs["quality"] = qualidade
                if target_format == "PNG":
                    # PNG não usa "quality" no Pillow da mesma forma (usa optimize e compress_level)
                    save_kwargs["optimize"] = True

                img.save(output_buffer, format=target_format, **save_kwargs)
                
                processed_bytes = output_buffer.getvalue()
                
                # Definir media type de saída
                media_type_map = {
                    "JPEG": "image/jpeg",
                    "PNG": "image/png",
                    "WEBP": "image/webp"
                }
                out_media_type = media_type_map.get(target_format, "image/jpeg")

                return processed_bytes, out_media_type
        except Exception as e:
            print(f"[ImageProcessor] Erro no processamento: {e}")
            # Em caso de erro severo com Pillow, devolve o original como fallback seguro
            return image_bytes, "application/octet-stream"

    @staticmethod
    async def download_image(url: str, timeout: float = 10.0) -> Tuple[Optional[bytes], bool]:
        """
        Faz o download utilitário de uma imagem.
        Retorna (content_bytes, teve_aviso_ssl).
        """
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        # 1. Tenta com verificação SSL estrita
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=True) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    return resp.content, False
        except Exception:
            pass

        # 2. Fallback com verify=False se o servidor do fabricante tiver SSL inválido/incompleto
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    print(f"[ImageProcessor] Download concluído via fallback SSL ignorado para: {url}")
                    return resp.content, True
                return None, False
        except Exception as e:
            print(f"[ImageProcessor] Erro ao baixar {url}: {e}")
            return None, False

image_service = ImageProcessor()
