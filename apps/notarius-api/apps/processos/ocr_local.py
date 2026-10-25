"""Local Windows OCR. Recognized text is evidence to review, never a confirmed fact."""
import asyncio
import io
import sys

MAX_PIXELS = 25_000_000
MAX_DIMENSION = 3200

def preparar_imagem(data):
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(data)) as original:
        if original.width * original.height > MAX_PIXELS:
            raise ValueError('Imagem acima do limite de pixels.')
        original.seek(0)
        image = ImageOps.exif_transpose(original).convert('RGB')
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        out = io.BytesIO(); image.save(out, format='PNG')
        return out.getvalue(), image.width, image.height

def rasterizar_pagina(document, index):
    page = document[index]
    try:
        width, height = page.get_size()
        bitmap = page.render(scale=min(2.5, MAX_DIMENSION / max(width, height)))
        try:
            image = bitmap.to_pil()
            try:
                out = io.BytesIO(); image.save(out, format='PNG')
                return out.getvalue()
            finally:
                image.close()
        finally:
            bitmap.close()
    finally:
        page.close()

async def reconhecer(data):
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.globalization import Language
    from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    from winrt.windows.graphics.imaging import BitmapDecoder
    engine = OcrEngine.try_create_from_language(Language('pt-BR'))
    if engine is None:
        raise RuntimeError('Português não disponível no OCR local.')
    memory = InMemoryRandomAccessStream()
    bitmap = None
    try:
        writer = DataWriter(memory)
        writer.write_bytes(data)
        await writer.store_async()
        writer.detach_stream(); writer.close()
        memory.seek(0)
        decoder = await BitmapDecoder.create_async(memory)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        regions = []
        for line in result.lines:
            words = list(line.words)
            if not words:
                continue
            left = min(w.bounding_rect.x for w in words)
            top = min(w.bounding_rect.y for w in words)
            right = max(w.bounding_rect.x + w.bounding_rect.width for w in words)
            bottom = max(w.bounding_rect.y + w.bounding_rect.height for w in words)
            regions.append({'texto': line.text, 'x': left, 'y': top, 'largura': right-left, 'altura': bottom-top})
        full_text = '\n'.join(line.text for line in result.lines)
        return {'texto_ocr': full_text[:50000],
                'regioes_ocr': regions[:5000], 'ocr_idioma': engine.recognizer_language.language_tag,
                'limites_leitura': (['ocr_texto_50000'] if len(full_text) > 50000 else []) + (['ocr_regioes_5000'] if len(regions) > 5000 else [])}
    finally:
        if bitmap is not None:
            bitmap.close()
        memory.close()

def executar_ocr(data):
    if sys.platform != 'win32':
        return {'texto_ocr': '', 'regioes_ocr': [], 'ocr_erro': 'OCR local não configurado neste sistema.'}
    try:
        png, width, height = preparar_imagem(data)
        result = asyncio.run(asyncio.wait_for(reconhecer(png), timeout=12))
        return {**result, 'largura_imagem': width, 'altura_imagem': height,
                'ocr_erro': '' if result['texto_ocr'].strip() else 'Não reconheci texto suficiente. Confira a imagem original.'}
    except Exception:
        return {'texto_ocr': '', 'regioes_ocr': [], 'ocr_erro': 'Não consegui concluir o OCR local. Confira o original ou envie outra cópia.'}
