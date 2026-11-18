"""Editable Word and paginated PDF from the same saved plain text, with no rewriting."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo
import re
from rest_framework.exceptions import ValidationError
from .modelo_referencia import TITULO_REFERENCIA


def titulo_secao(line):
    """Layout only: short uppercase numbered sections and existing template labels."""
    return line in {'ESCRITURA DE COMPRA E VENDA', 'ESCRITURA PÚBLICA DE COMPRA E VENDA', 'QUALIFICAÇÃO DA PARTE VENDEDORA',
                    'QUALIFICAÇÃO DA PARTE COMPRADORA'} or bool(
        len(line) <= 160 and line.isupper() and re.match(r'^\d{1,2}\.-\s+\S', line))

def descricao(minuta):
    from django.conf import settings
    date = minuta.created_at.astimezone(ZoneInfo(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M')
    origin = 'Editada pela escrevente' if minuta.tipo == 'editada' else 'Preenchida pelo sistema'
    return f'Versão {minuta.versao} | Modelo {minuta.modelo.versao} | {origin} | {date}'


def corpo_exportado(minuta):
    text = minuta.corpo
    if getattr(minuta, 'assistencia', {}).get('simulacao') and 'SIMULAÇÃO FICTÍCIA' not in text:
        return 'SIMULAÇÃO FICTÍCIA | SEM VALIDADE | NÃO PROTOCOLAR\n\n' + text
    return text


def word(minuta):
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.5)
    section.left_margin = section.right_margin = Cm(2.5)
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    title_style = doc.styles['Title']
    title_style.font.name = 'Times New Roman'
    title_style.font.size = Pt(16)
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    for border in list(title_style.element.xpath('./w:pPr/w:pBdr')):
        border.getparent().remove(border)
    title = doc.add_paragraph('Minuta de compra e venda', style='Title')
    title.paragraph_format.space_after = Pt(8)
    for border in list(title._p.xpath('./w:pPr/w:pBdr')):
        border.getparent().remove(border)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(16)
    doc.add_paragraph('Para revisão. Não constitui documento assinado ou ato concluído.')
    doc.add_paragraph(descricao(minuta))
    # Keep each existing line, including blank lines; do not interpret markup or fields.
    for line in corpo_exportado(minuta).replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        paragraph = doc.add_paragraph(line)
        if titulo_secao(line):
            paragraph.paragraph_format.keep_with_next = True
        elif not line:
            paragraph.paragraph_format.line_spacing = Pt(6)
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.keep_with_next = True
    footer = section.footer.paragraphs[0]
    footer.add_run('Minuta para revisão | Página ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    doc.core_properties.author = 'Notarius'
    doc.core_properties.title = 'Minuta de compra e venda para revisão'
    stream = BytesIO(); doc.save(stream)
    return stream.getvalue()

def pdf(minuta, *, arquivavel=False):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from django.conf import settings
    paths = [getattr(settings, 'NOTARIUS_PDF_FONT', ''), 'C:/Windows/Fonts/times.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']
    path = next((p for p in paths if p and Path(p).is_file()), None)
    if not path:
        raise ValidationError('A fonte do PDF não está disponível. Configure NOTARIUS_PDF_FONT; o texto não foi substituído.')
    font_name = 'NotariusDocument'
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, path))
    font = pdfmetrics.getFont(font_name)
    text = minuta.corpo + descricao(minuta)
    if any(not c.isspace() and ord(c) not in font.face.charToGlyph for c in text):
        raise ValidationError('O texto contém caracteres não suportados pela fonte do PDF. Confira o texto ou use Word; nenhum caractere foi substituído.')
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, topMargin=2.5*cm, bottomMargin=2.5*cm,
                                 leftMargin=2.5*cm, rightMargin=2.5*cm, title='Minuta de compra e venda para revisão', author='Notarius',
                                 initialFontName=font_name)
    corrido = TITULO_REFERENCIA in minuta.corpo
    body = ParagraphStyle('Body', fontName=font_name, fontSize=12, leading=15, spaceAfter=6,
                          alignment=TA_JUSTIFY if corrido else TA_LEFT, splitLongWords=True)
    heading = ParagraphStyle('Heading', parent=body, fontSize=16, leading=20, spaceAfter=12)
    section_heading = ParagraphStyle('SectionHeading', parent=body, keepWithNext=True)
    small = ParagraphStyle('Small', parent=body, fontSize=9, leading=12, spaceAfter=12)
    story = [] if arquivavel else [Paragraph('Minuta de compra e venda', heading),
                                  Paragraph('Para revisão. Não constitui documento assinado ou ato concluído.', small),
                                  Paragraph(escape(descricao(minuta)), small)]
    body_text = corpo_exportado(minuta)
    for line in body_text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if line:
            style = heading if arquivavel and line.startswith(('ESCRITURA DE COMPRA E VENDA', 'ESCRITURA PÚBLICA DE COMPRA E VENDA')) else section_heading if titulo_secao(line) else body
            story.append(Paragraph(escape(line).replace('\t', '&#160;&#160;&#160;&#160;'), style))
        else:
            spacer = Spacer(1, 6)
            spacer.keepWithNext = not corrido
            story.append(spacer)
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont(font_name, 9)
        if 'SIMULAÇÃO FICTÍCIA' in body_text:
            canvas.drawString(2.5*cm, 1.5*cm, 'Simulação fictícia | Sem validade')
        elif not arquivavel:
            canvas.drawString(2.5*cm, 1.5*cm, 'Minuta para revisão')
        canvas.drawRightString(A4[0]-2.5*cm, 1.5*cm, f'Página {doc.page}')
        canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return converter_pdfa(stream) if arquivavel else stream.getvalue()


def converter_pdfa(stream):
    from PIL import ImageCms
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, TextStringObject

    stream.seek(0)
    writer = PdfWriter(clone_from=PdfReader(stream))
    writer.pdf_header = '%PDF-1.7'
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    icc = DecodedStreamObject()
    icc.set_data(profile)
    icc[NameObject('/N')] = NumberObject(3)
    intent = DictionaryObject({
        NameObject('/Type'): NameObject('/OutputIntent'),
        NameObject('/S'): NameObject('/GTS_PDFA1'),
        NameObject('/OutputConditionIdentifier'): TextStringObject('sRGB'),
        NameObject('/DestOutputProfile'): writer._add_object(icc),
    })
    writer.root_object[NameObject('/OutputIntents')] = ArrayObject([intent])
    metadata = DecodedStreamObject()
    metadata[NameObject('/Type')] = NameObject('/Metadata')
    metadata[NameObject('/Subtype')] = NameObject('/XML')
    metadata.set_data(b'''<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
<pdfaid:part>2</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>
</rdf:Description></rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>''')
    writer.root_object[NameObject('/Metadata')] = writer._add_object(metadata)
    writer.metadata = None
    target = BytesIO()
    writer.write(target)
    return target.getvalue()
