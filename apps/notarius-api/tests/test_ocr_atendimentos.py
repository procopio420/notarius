from io import BytesIO
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch
import sys
import subprocess

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from pypdf import PdfWriter, PdfReader
from apps.tenancy.models import Tenant
from apps.profiles.models import UserProfile
from apps.processos.models import AnexoAtendimento, PaginaAnexoAtendimento, RevisaoDadoAtendimento
from tests.test_atendimentos import pdf_fixture

def native_available():
    try:
        if sys.platform != 'win32' or not Path('C:/Windows/Fonts/arial.ttf').is_file():
            return False
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.globalization import Language
        return OcrEngine.try_create_from_language(Language('pt-BR')) is not None
    except Exception:
        return False

def image_fixture(format='PNG'):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB', (1600, 800), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 44)
    draw.multiline_text((70, 70), 'DOCUMENTO FICTÍCIO DE TESTE\nVendedores: PESSOA DE TESTE\nPreço: R$ 100.000,00\nNenhum dado real.', font=font, fill='black', spacing=25)
    result = BytesIO(); image.save(result, format=format); image.close()
    return result.getvalue()

class OcrAtendimentoTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('qa_ocr', password='test-only')
        self.tenant = Tenant.objects.create(nome='Cartório OCR fictício', uf='RJ')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.tenants.add(self.tenant); profile.default_tenant = self.tenant; profile.save()
        self.client.force_authenticate(self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        self.case = self.client.post('/api/v1/atendimentos/', {'titulo': 'OCR FICTICIO'}, format='json').data['id']
        self.prefix = f'/api/v1/atendimentos/{self.case}'

    @skipUnless(native_available(), 'OCR pt-BR local não disponível neste ambiente')
    def test_png_jpg_extract_text_positions_and_keep_review_required(self):
        from PIL import Image
        for format, ext in [('PNG', 'png'), ('JPEG', 'jpg')]:
            data = image_fixture(format)
            response = self.client.post(self.prefix+'/anexos/', {'arquivo': SimpleUploadedFile('ficticio.'+ext, data)}, format='multipart')
            self.assertEqual(response.status_code, 201)
            page = response.data['paginas'][0]
            self.assertEqual(response.data['situacao'], 'revisao')
            self.assertEqual(page['metodo'], 'ocr_local')
            self.assertIn('100.000,00', page['texto_ocr'])
            self.assertIn('PESSOA DE TESTE', page['texto_ocr'])
            self.assertGreaterEqual(len(page['regioes_ocr']), 3)
            for region in page['regioes_ocr']:
                self.assertGreaterEqual(region['x'], 0)
                self.assertLessEqual(region['x']+region['largura'], page['largura_imagem'])
                self.assertLessEqual(region['y']+region['altura'], page['altura_imagem'])
            url = self.prefix+f"/anexos/{response.data['id']}/paginas/{page['id']}/imagem/"
            preview = self.client.get(url)
            self.assertEqual(preview.status_code, 200)
            im = Image.open(BytesIO(preview.content))
            self.assertEqual(im.size, (page['largura_imagem'], page['altura_imagem']))
            self.assertEqual(preview['Cache-Control'], 'no-store')
            self.client.force_authenticate(None)
            self.assertIn(self.client.get(url).status_code, [401, 403])
            self.client.force_authenticate(self.user)
            self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertTrue(self.client.get(self.prefix+'/conferencia/').data['bloqueado'])

    @skipUnless(native_available(), 'OCR pt-BR local não disponível neste ambiente')
    def test_mixed_pdf_preserves_native_page_and_ocr_page_number(self):
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        stream = BytesIO(); document = canvas.Canvas(stream)
        document.drawImage(ImageReader(BytesIO(image_fixture())), 30, 500, width=535, height=267)
        document.showPage(); document.save()
        writer = PdfWriter()
        writer.append(PdfReader(BytesIO(pdf_fixture())))
        writer.append(PdfReader(BytesIO(stream.getvalue())))
        output = BytesIO(); writer.write(output)
        response = self.client.post(self.prefix+'/anexos/', {'arquivo': SimpleUploadedFile('misto.pdf', output.getvalue())}, format='multipart')
        self.assertEqual(response.status_code, 201)
        pages = response.data['paginas']
        self.assertEqual([p['numero'] for p in pages], [1, 2])
        self.assertEqual(pages[0]['metodo'], 'texto_pdf')
        self.assertEqual(pages[0]['texto_ocr'], '')
        self.assertIn('100.000,00', pages[1]['texto_ocr'])
        self.assertEqual(pages[1]['situacao'], 'revisao')

    def test_engine_unavailable_and_timeout_do_not_invent_text(self):
        from apps.processos.ocr_local import executar_ocr
        from apps.processos.leitura_anexos import extrair_pdf
        with patch('apps.processos.ocr_local.sys.platform', 'linux'):
            result = executar_ocr(b'unknown')
        self.assertEqual(result['texto_ocr'], '')
        self.assertTrue(result['ocr_erro'])
        with patch('apps.processos.leitura_anexos.subprocess.run', side_effect=subprocess.TimeoutExpired('worker', 1)):
            result = extrair_pdf(b'%PDF-1.4')
        self.assertEqual(result['situacao'], 'revisao')
        self.assertEqual(result['paginas'], [])

    def test_ocr_and_native_disagreement_stays_visible_and_origin_is_validated(self):
        from apps.processos.models import Atendimento
        attachment = AnexoAtendimento.objects.create(tenant=self.tenant, atendimento_id=self.case,
            autor=self.user, nome='ficticio.pdf', mime='application/pdf', tamanho=1, sha256='a'*64,
            conteudo=b'x', situacao='revisao', aviso='Teste')
        page = PaginaAnexoAtendimento.objects.create(tenant=self.tenant, anexo=attachment, numero=1,
            texto='Preço: R$ 100.000,00', texto_ocr='Preço: R$ 200.000,00', metodo='texto_pdf_e_ocr', situacao='revisao')
        report = self.client.get(self.prefix+'/conferencia/').data
        question = next(q for q in report['pendencias'] if q['chave']=='preco')
        self.assertEqual(question['tipo'], 'divergencia')
        self.assertEqual({c['canal'] for c in question['candidatos']}, {'texto', 'ocr'})
        payload = {'chave':'preco','valor':'R$ 200.000,00','situacao':'informado','justificativa':'Transcrição fictícia sem confirmação',
            'organizacao_versao':0,'versao_esperada':0,'pagina_id':str(page.id),'trecho_origem':'Preço: R$ 200.000,00','canal_origem':'texto'}
        self.assertEqual(self.client.post(self.prefix+'/ficha/',payload,format='json').status_code,400)
        payload['canal_origem']='ocr'
        saved=self.client.post(self.prefix+'/ficha/',payload,format='json')
        self.assertEqual(saved.status_code,201)
        self.assertEqual(saved.data['origem']['canal'],'ocr')
        self.assertEqual(saved.data['situacao'],'informado')
        other=Atendimento.objects.create(tenant=self.tenant,criado_por=self.user,titulo='Outro fictício')
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{other.id}/anexos/{attachment.id}/paginas/{page.id}/imagem/').status_code,404)

    def test_pdf_ocr_page_limit_is_explicit(self):
        from apps.processos.leitura_anexos import ler_pdf
        writer = PdfWriter()
        for _ in range(11): writer.add_blank_page(width=100,height=100)
        stream=BytesIO(); writer.write(stream)
        with patch('apps.processos.leitura_anexos.rasterizar_pagina',return_value=b'image'), patch('apps.processos.leitura_anexos.executar_ocr',return_value={'texto_ocr':'TEXTO FICTICIO','regioes_ocr':[],'ocr_erro':''}) as engine:
            result=ler_pdf(stream.getvalue())
        self.assertEqual(engine.call_count,10)
        self.assertEqual(len(result['paginas']),11)
        self.assertIn('Limite de 10',result['paginas'][-1]['aviso'])
        self.assertEqual(result['paginas'][-1]['texto'],'')

    def test_rereading_preserves_history_and_rejects_old_source(self):
        attachment = AnexoAtendimento.objects.create(tenant=self.tenant, atendimento_id=self.case,
            autor=self.user, nome='ficticio.pdf', mime='application/pdf', tamanho=1,
            sha256='b'*64, conteudo=b'x', situacao='revisao')
        page = PaginaAnexoAtendimento.objects.create(tenant=self.tenant, anexo=attachment,
            numero=1, texto='Preço: R$ 100.000,00', situacao='revisao')
        payload = {'chave':'preco','valor':'R$ 100.000,00','situacao':'informado',
            'justificativa':'Dado fictício para verificar histórico', 'versao_esperada':0,
            'organizacao_versao':0,'pagina_id':str(page.id),'trecho_origem':page.texto,'canal_origem':'texto'}
        self.assertEqual(self.client.post(self.prefix+'/ficha/',payload,format='json').status_code,201)
        result = {'situacao':'revisao','aviso':'Nova leitura fictícia','paginas':[
            {'numero':1,'texto':'Preço: R$ 200.000,00','situacao':'revisao','aviso':'Conferir'}]}
        url = self.prefix+f'/anexos/{attachment.id}/reler/'
        with patch('apps.processos.views.extrair_pdf',return_value=result):
            response = self.client.post(url,{'leitura_versao':1},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['leitura_versao'],2)
        self.assertEqual(len(response.data['paginas']),1)
        self.assertEqual(response.data['paginas'][0]['texto'],'Preço: R$ 200.000,00')
        self.assertTrue(PaginaAnexoAtendimento.objects.filter(pk=page.id).exists())
        self.assertEqual(RevisaoDadoAtendimento.objects.get().pagina_origem_id,page.id)
        payload['versao_esperada']=1
        self.assertEqual(self.client.post(self.prefix+'/ficha/',payload,format='json').status_code,400)
        self.assertEqual(self.client.post(url,{'leitura_versao':1},format='json').status_code,409)
