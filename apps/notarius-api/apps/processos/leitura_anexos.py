"""Literal extraction only. No model calls, inference, or automatic field confirmation."""
import io
import json
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 40
MAX_TEXT_PAGE = 50000
try:
    from .ocr_local import executar_ocr, rasterizar_pagina, preparar_imagem
except ImportError:
    from ocr_local import executar_ocr, rasterizar_pagina, preparar_imagem


def extrair_pdf(data, image=False):
    # A broken PDF must not keep a web request busy indefinitely.
    try:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--image' if image else '--worker'],
                                input=data, capture_output=True, timeout=135)
        if result.returncode:
            return {'situacao': 'revisao', 'aviso': 'Não foi possível ler este PDF. Confira o original ou envie outra cópia.', 'paginas': [], 'metadados_leitura': {'total_paginas': None, 'limites': ['falha_leitura']}}
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        return {'situacao': 'revisao', 'aviso': 'A leitura não pôde ser concluída no limite disponível. Confira o original.', 'paginas': [], 'metadados_leitura': {'total_paginas': None, 'limites': ['tempo_ou_resposta']}}


def ler_pdf(data):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        return {'situacao': 'revisao', 'aviso': 'PDF protegido por senha. Envie uma cópia desbloqueada autorizada.', 'paginas': [], 'metadados_leitura': {'total_paginas': None, 'limites': ['arquivo_protegido']}}
    if not reader.pages or len(reader.pages) > MAX_PAGES:
        return {'situacao': 'revisao', 'aviso': 'PDF vazio ou acima do limite de 40 páginas. Divida o arquivo.', 'paginas': [], 'metadados_leitura': {'total_paginas': len(reader.pages), 'limites': ['quantidade_paginas']}}
    pages = []
    rendered = None
    ocr_count = 0
    for n, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or '').replace('\x00', '').strip()
        resources = page.get('/Resources')
        resources = resources.get_object() if resources else {}
        images = bool(resources.get('/XObject'))
        bad = len(text) < 20 or '\ufffd' in text or len(text) > MAX_TEXT_PAGE
        # Presence of embedded image/form objects makes full coverage uncertain.
        review = bad or images
        note = ('Página sem texto extraível.' if not text else
                'Texto extraído, mas há imagens/formulários ou sinais de leitura incompleta. Confira a página original.' if review else
                'Texto extraído automaticamente; confira no original antes de confirmar dados.')
        info = {'numero': n, 'texto': text[:MAX_TEXT_PAGE], 'situacao': 'revisao' if review else 'extraido', 'aviso': note, 'metodo': 'texto_pdf'}
        info['limites_leitura'] = ['texto_50000'] if len(text) > MAX_TEXT_PAGE else []
        if review:
            if ocr_count >= 10:
                info['limites_leitura'].append('ocr_10_paginas')
                info['aviso'] += ' Limite de 10 páginas de OCR por arquivo atingido. Divida o PDF para ler as demais páginas.'
            else:
                ocr_count += 1
                try:
                    if rendered is None:
                        import pypdfium2 as pdfium
                        rendered = pdfium.PdfDocument(data)
                    ocr = executar_ocr(rasterizar_pagina(rendered, n-1))
                    error = ocr.pop('ocr_erro', '')
                    limits = info['limites_leitura'] + ocr.pop('limites_leitura', [])
                    info.update(ocr); info['limites_leitura'] = limits
                    info['metodo'] = 'texto_pdf_e_ocr' if text else 'ocr_local'
                    if not text:
                        info['texto'] = info.get('texto_ocr', '')
                    info['aviso'] = error or 'Texto proposto por OCR local em português. Pode conter erros ou omissões; confira o original. Nenhum dado foi confirmado.'
                except Exception:
                    info['aviso'] += ' Não consegui renderizar esta página para OCR. Confira o original.'
        if 'texto_50000' in info['limites_leitura']:
            info['aviso'] += ' Limite de 50.000 caracteres atingido; o texto nativo foi truncado. Confira o original.'
        pages.append(info)
    if rendered is not None:
        rendered.close()
    needs_review = any(p['situacao'] == 'revisao' for p in pages)
    return {'situacao': 'revisao' if needs_review else 'extraido',
            'aviso': 'Há páginas com leitura incerta ou OCR proposto. Confira o original antes de usar os dados.' if needs_review else 'Leitura de texto concluída. Não comprova exatidão, autenticidade ou validade.', 'paginas': pages,
            'metadados_leitura': {'total_paginas': len(reader.pages), 'limites': sorted({limit for p in pages for limit in p.get('limites_leitura', [])})}}

def ler_imagem(data):
    result = executar_ocr(data)
    error = result.pop('ocr_erro', '')
    note = error or 'OCR local propôs este texto. Confira a imagem, especialmente números e nomes; não houve confirmação automática.'
    page = {'numero': 1, 'texto': result.get('texto_ocr', ''), 'metodo': 'ocr_local',
            'situacao': 'revisao', 'aviso': note, **result}
    return {'situacao': 'revisao', 'aviso': note, 'paginas': [page], 'metadados_leitura': {'total_paginas': 1, 'limites': page.get('limites_leitura', [])}}

def renderizar_imagem(data, numero, image=False):
    try:
        args = [sys.executable, str(Path(__file__).resolve()), '--render', str(numero)]
        if image:
            args.append('--image-source')
        result = subprocess.run(args, input=data, capture_output=True, timeout=15)
        return result.stdout if result.returncode == 0 and result.stdout.startswith(b'\x89PNG') else None
    except subprocess.TimeoutExpired:
        return None


if __name__ == '__main__':
    try:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        if '--render' in sys.argv:
            if '--image-source' in sys.argv:
                png, _, _ = preparar_imagem(data)
            else:
                import pypdfium2 as pdfium
                with pdfium.PdfDocument(data) as document:
                    png = rasterizar_pagina(document, int(sys.argv[sys.argv.index('--render')+1])-1)
            sys.stdout.buffer.write(png)
            sys.exit(0)
        print(json.dumps(ler_imagem(data) if '--image' in sys.argv else ler_pdf(data), ensure_ascii=True))
    except Exception:
        sys.exit(1)
