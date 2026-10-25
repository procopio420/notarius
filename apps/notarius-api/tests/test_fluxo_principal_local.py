from uuid import uuid4
from rest_framework.test import APITestCase
from apps.processos.models import MensagemAtendimento
from tests import test_atendimentos as helpers

class FluxoPrincipalLocalTests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case
    report = helpers.AtendimentoTests.report
    answer = helpers.AtendimentoTests.answer
    ready_for_draft = helpers.AtendimentoTests.ready_for_draft
    save_template = helpers.AtendimentoTests.save_template
    generate_draft = helpers.AtendimentoTests.generate_draft

    def send(self, case, text):
        return self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',
            {'texto': text, 'client_id': str(uuid4())}, format='json')

    def test_free_text_after_confirmations_blocks_until_explicit_review(self):
        case = self.ready_for_draft()
        self.save_template(case)
        first = self.generate_draft(case)
        self.assertEqual(first.status_code, 200)
        original = 'Talvez o comprador esteja representado. Ainda não sabemos por quem.'
        message = self.send(case, original).data
        key = 'mensagem:' + message['id']
        question = next(q for q in self.report(case)['pendencias'] if q['chave'] == key)
        self.assertEqual(question['atual'], original)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertEqual(self.answer(case, key, confirm=False)[0].status_code, 400)
        response, old = self.answer(case, key)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.generate_draft(case).status_code, 200)
        self.assertEqual(MensagemAtendimento.objects.get(pk=message['id']).texto, original)
        self.send(case, 'Não foi possível identificar a pessoa mencionada no novo documento.')
        self.assertTrue(self.report(case)['bloqueado'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        old['client_id'] = str(uuid4())
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/responder/', old, format='json').status_code, 409)

    def test_manual_correction_is_a_source_message_with_author_and_history(self):
        case = self.create_case()
        url = f'/api/v1/atendimentos/{case}/ficha/'
        payload = {'chave':'preco', 'valor':'VALOR FICTÍCIO', 'situacao':'informado',
                   'justificativa':'Informado pela escrevente no teste', 'versao_esperada':0}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        source = response.data['origem']
        self.assertEqual(source['tipo'], 'mensagem')
        self.assertEqual(source['trecho'], payload['valor'])
        message = MensagemAtendimento.objects.get(pk=source['mensagem_id'])
        self.assertEqual(message.autor, self.user)
        self.assertEqual(message.tenant, self.tenant)
        self.assertIn('preco', [q['chave'] for q in self.report(case)['pendencias']])
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 409)
        self.assertEqual(MensagemAtendimento.objects.count(), 1)

    def test_template_approval_cannot_supply_payment_query_or_signature_events(self):
        from apps.processos.redacao import BASE
        for fact in ['O preço foi pago e dou quitação.', 'A consulta foi efetuada.', 'As partes assinaram.']:
            with self.subTest(fact=fact):
                case = self.ready_for_draft()
                self.assertEqual(self.save_template(case, corpo=BASE['corpo'] + '\n' + fact).status_code, 201)
                state = self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data
                self.assertFalse(state['pronto'])
                self.assertIn('texto fixo', state['motivo_bloqueio'])
                self.assertEqual(self.generate_draft(case).status_code, 400)
