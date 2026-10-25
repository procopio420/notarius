from uuid import uuid4
from collections import defaultdict
from io import BytesIO
from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from apps.processos.cenarios_homologacao import preparar, especificacao
from apps.processos.models import Atendimento, RevisaoDadoAtendimento, PropostaDadoAtendimento
from tests import test_atendimentos as helpers


class CenariosHomologacaoTests(APITestCase):
    def setUp(self):
        helpers.AtendimentoTests.setUp(self)
        self.tenant.nome = 'Cartório FICTÍCIO QA'; self.tenant.save()

    def post(self, case, action, data):
        if action == 'ficha-detalhada':
            from tests.fontes_ficticias import preparar_campos
            preparar_campos(self, case, data)
            opened = self.client.get(f'/api/v1/atendimentos/{case}/ficha-detalhada/').data
            contexts = {f['chave']: f['contexto_assinatura'] for o in opened['objetos'] if o['id'] == data.get('objeto_id') for f in o['campos']}
            for field in data.get('campos', []):
                field.setdefault('contexto_assinatura', contexts[field['chave']])
        response = self.client.post(f'/api/v1/atendimentos/{case}/{action}/', data, format='json')
        self.assertIn(response.status_code, [200, 201], response.data)
        return response.data

    def seed(self, variant):
        result, created = preparar(self.tenant, self.user, variant)
        self.assertTrue(created)
        return result

    def simulate_review(self, manifest, omit=None):
        """Test-only explicit answers. Never called by preparation command or UI."""
        case = manifest['atendimento_id']; groups = defaultdict(list)
        proposals = {p['id']: p for p in self.client.get(f'/api/v1/atendimentos/{case}/propostas-dados/').data['propostas']}
        for expected in manifest['resultado_esperado_proposto']:
            p = proposals[expected['proposta_id']]; source = p['origem']
            confirm = (expected['alias'], expected['chave']) != omit
            groups[expected['objeto_id']].append({'chave': expected['chave'], 'valor': expected['valor_revisado_ficticio'],
                'valor_original': p['valor_original'], 'situacao': 'confirmado' if confirm else 'informado',
                'origem': source['tipo'], 'versao_esperada': 0, 'proposta_id': p['id'], 'versao_proposta': 0,
                'conferir_associacao': True, 'confirmar': confirm, 'conferir_fonte': confirm, 'trecho_origem': p['trecho'],
                **({'pagina_id': source['pagina_id'], 'leitura_versao': source['leitura_versao']} if source['tipo'] == 'documento' else {'mensagem_id': source['mensagem_id']})})
        for oid, fields in groups.items():
            self.post(case, 'ficha-detalhada', {'client_id': str(uuid4()), 'modelo_id': manifest['modelo_id'],
                'operacao': 'salvar', 'objeto_id': oid, 'campos': fields,
                'justificativa': 'RESPOSTAS HUMANAS SIMULADAS EM TESTE AUTOMATIZADO, SEM HOMOLOGAÇÃO'})
        issues = self.post(case, 'pendencias-ficha', {'operacao': 'atualizar'})['pendencias']
        for page in [p for p in issues if p['tipo'] == 'pagina']:
            if any(p['situacao'] not in ['aceita', 'rejeitada', 'substituida'] for p in page['contexto']['propostas']):
                continue
            self.post(case, 'pendencias-ficha', {'operacao': 'resolver', 'client_id': str(uuid4()), 'pendencia_id': page['id'],
                'assinatura': page['assinatura'], 'versao_esperada': page['versao'], 'acao': 'vincular',
                'revisoes_ids': page['contexto']['usos_atuais'], 'confirmei_revisao': True,
                'justificativa': 'REVISÃO DE FONTE SIMULADA EM TESTE, SEM CONFIRMAR AUTENTICIDADE'})
        spec = especificacao(manifest['variante'])
        model = self.post(case, 'modelo-minuta', {**spec['modelo'], 'aprovado': True, 'versao_esperada': 1,
            'justificativa': 'APROVAÇÃO SIMULADA NO BANCO DE TESTE; NÃO É HOMOLOGAÇÃO PROFISSIONAL'})
        state = self.client.get(f'/api/v1/atendimentos/{case}/vinculacao-minuta/').data
        self.post(case, 'vinculacao-minuta', {'client_id': str(uuid4()), 'modelo_id': model['id'], 'versao_esperada': 0,
            'escopo_assinatura': state['escopo_assinatura'], 'registros': manifest['registros'], 'exclusoes': [], 'conferir': True,
            'motivo': 'VINCULAÇÃO EXPLÍCITA SIMULADA DOS OBJETOS FICTÍCIOS'})

    def generate(self, case):
        url = f'/api/v1/atendimentos/{case}/minuta-preparada/'
        state = self.client.get(url).data
        return self.client.post(url, {'assinatura_esperada': state['assinatura']}, format='json')

    def test_preparation_never_approves_or_confirms_and_retry_does_not_reset_review(self):
        with patch('openai.OpenAI') as provider:
            manifest = self.seed('direta')
        provider.assert_not_called()
        case = Atendimento.objects.get(pk=manifest['atendimento_id'])
        self.assertFalse(case.modelos_minuta.first().aprovado)
        self.assertFalse(case.revisoes.exists()); self.assertFalse(case.vinculacoes_minuta.exists())
        self.assertFalse(case.minutas_preparadas.exists())
        self.assertFalse(case.propostas_dados.filter(decisoes__isnull=False).exists())
        self.assertEqual(self.generate(case.id).status_code, 400)
        self.simulate_review(manifest)
        count = case.revisoes.count(); model_id = case.modelos_minuta.first().id
        repeated, created = preparar(self.tenant, self.user, 'direta')
        self.assertFalse(created); self.assertEqual(repeated, manifest)
        self.assertEqual(case.revisoes.count(), count); self.assertEqual(case.modelos_minuta.first().id, model_id)

    def test_both_variants_full_flow_and_export_without_mixing_people_or_facts(self):
        texts = {}
        for variant in ['direta', 'procuracao']:
            manifest = self.seed(variant); case = manifest['atendimento_id']
            self.simulate_review(manifest)
            with patch('openai.OpenAI') as provider:
                result = self.generate(case)
            provider.assert_not_called(); self.assertEqual(result.status_code, 200, result.data)
            draft = result.data['versoes'][0]; texts[variant] = draft['corpo']
            self.assertIn('PREVISÃO FICTÍCIA DE PAGAMENTO FUTURO', draft['corpo'])
            self.assertNotIn('pagamento realizado', draft['corpo'].lower()); self.assertNotIn('assinaram', draft['corpo'].lower())
            self.assertEqual(draft['dados']['vendedor.nome']['objeto_id'], manifest['registros']['vendedor'])
            for datum in draft['dados'].values():
                self.assertTrue(datum['origem']['trecho']); self.assertTrue(datum['confirmacao'])
                for occurrence in datum['ocorrencias']:
                    self.assertEqual(draft['corpo'][occurrence['inicio']:occurrence['fim']], datum['valor'])
            self.post(case, f"minutas/{draft['id']}/revisar", {'versao_esperada': draft['versao'],
                'motivo': 'REVISÃO FINAL SIMULADA EM TESTE', 'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True})
            from docx import Document
            from pypdf import PdfReader
            for fmt in ['docx', 'pdf']:
                export = self.client.get(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/", {'formato': fmt})
                self.assertEqual(export.status_code, 200, getattr(export, 'data', None))
                if fmt == 'docx':
                    self.assertEqual('\n'.join(p.text for p in Document(BytesIO(export.content)).paragraphs[3:]), draft['corpo'])
                else:
                    text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(export.content)).pages)
                    self.assertIn('PESSOA VENDEDORA FICTÍCIA ALFA', text)
        self.assertNotIn('PROCURADORA', texts['direta']); self.assertNotIn('INSTRUMENTO-FICTICIO', texts['direta'])
        self.assertIn('PESSOA PROCURADORA FICTÍCIA GAMA', texts['procuracao'])
        self.assertIn('INSTRUMENTO-FICTICIO-PROC-001', texts['procuracao'])

    def test_unconfirmed_instrument_blocks_proxy_case(self):
        manifest = self.seed('procuracao'); self.simulate_review(manifest, omit=('representacao', 'instrumento'))
        case = manifest['atendimento_id']
        self.assertEqual(self.generate(case).status_code, 400)
        report = self.client.get(f'/api/v1/atendimentos/{case}/conferencia/').data
        self.assertIn(f"dado:{manifest['registros']['representacao']}:instrumento", [p['chave'] for p in report['pendencias']])

    def test_preparation_refuses_non_fictional_tenant_and_unauthorized_user(self):
        self.tenant.nome = 'Cartório de uso real'; self.tenant.save()
        with self.assertRaises(ValidationError): preparar(self.tenant, self.user, 'direta')
        self.other.nome = 'Cartório FICTÍCIO sem acesso'; self.other.save()
        with self.assertRaises(ValidationError): preparar(self.other, self.user, 'direta')
        self.assertFalse(Atendimento.objects.exists())

    def test_preparation_failure_rolls_back_case_documents_and_proposals(self):
        from apps.processos import cenarios_homologacao as service
        with patch.object(service, 'alterar', side_effect=ValidationError('Falha simulada')):
            with self.assertRaises(ValidationError): preparar(self.tenant, self.user, 'direta')
        self.assertFalse(Atendimento.objects.exists()); self.assertFalse(PropostaDadoAtendimento.objects.exists())

    def test_identical_fictional_names_in_two_cases_do_not_merge_sources(self):
        direct = self.seed('direta'); proxy = self.seed('procuracao')
        self.assertNotEqual(direct['registros']['vendedor'], proxy['registros']['vendedor'])
        expected = next(p for p in proxy['resultado_esperado_proposto'] if p['alias'] == 'vendedor' and p['chave'] == 'nome')
        proposal = PropostaDadoAtendimento.objects.get(id=expected['proposta_id'])
        response = self.client.post(f"/api/v1/atendimentos/{direct['atendimento_id']}/ficha-detalhada/", {
            'client_id': str(uuid4()), 'modelo_id': direct['modelo_id'], 'operacao': 'salvar',
            'objeto_id': direct['registros']['vendedor'], 'justificativa': 'TESTE DE ISOLAMENTO FICTÍCIO',
            'campos': [{'chave': 'nome', 'valor': expected['valor_revisado_ficticio'], 'valor_original': proposal.valor_original,
                'situacao': 'confirmado', 'origem': 'documento', 'versao_esperada': 0, 'confirmar': True, 'conferir_fonte': True,
                'proposta_id': str(proposal.id), 'versao_proposta': 0, 'conferir_associacao': True,
                'pagina_id': str(proposal.pagina_id), 'leitura_versao': 1, 'trecho_origem': proposal.trecho}]}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())

    def test_new_conflicting_price_blocks_without_overwriting_old_confirmation(self):
        manifest = self.seed('direta'); self.simulate_review(manifest); case = manifest['atendimento_id']
        self.assertEqual(self.generate(case).status_code, 200)
        old = RevisaoDadoAtendimento.objects.get(objeto_id=manifest['registros']['negocio'], chave='preco')
        message = self.post(case, 'mensagens', {'client_id': str(uuid4()), 'texto': 'Preço de venda: R$ 250.000,00 — NOVO VALOR FICTÍCIO DIVERGENTE'})
        self.post(case, 'propostas-dados', {'client_id': str(uuid4()), 'operacao': 'extrair', 'mensagem_id': message['id']})
        self.assertEqual(self.generate(case).status_code, 400)
        old.refresh_from_db(); self.assertEqual(old.valor, 'R$ 200.000,00 — VALOR FICTÍCIO')
        self.assertEqual(old.situacao, 'confirmado')
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(objeto=old.objeto, chave='preco').count(), 1)

    def test_command_preserves_prepared_cases_and_material_edited_for_review(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from io import StringIO
        from django.core.management import call_command, CommandError
        with TemporaryDirectory() as folder:
            options = {'cartorio_id': str(self.tenant.id), 'usuario_id': str(self.user.id), 'saida': folder, 'stdout': StringIO()}
            call_command('preparar_homologacao_compra_venda', **options)
            self.assertEqual(Atendimento.objects.count(), 2)
            first = (Path(folder) / 'manifesto-ficticio.json').read_text(encoding='utf-8')
            call_command('preparar_homologacao_compra_venda', **options)
            self.assertEqual(Atendimento.objects.count(), 2)
            self.assertEqual((Path(folder) / 'manifesto-ficticio.json').read_text(encoding='utf-8'), first)
            changed = Path(folder) / 'direta' / 'FICTICIO-vendedor.txt'
            changed.write_text('ANOTAÇÃO FICTÍCIA PARA REVISÃO', encoding='utf-8')
            with self.assertRaises(CommandError):
                call_command('preparar_homologacao_compra_venda', **options)
            self.assertEqual(changed.read_text(encoding='utf-8'), 'ANOTAÇÃO FICTÍCIA PARA REVISÃO')
            self.assertFalse(RevisaoDadoAtendimento.objects.exists())
