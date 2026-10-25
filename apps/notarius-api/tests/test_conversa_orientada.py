from uuid import uuid4
from unittest.mock import patch
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from apps.processos.models import MensagemAtendimento, RevisaoDadoAtendimento
from apps.processos.dependencias_ficha import fonte_atual
from tests import test_ficha_estruturada as base
from tests import test_analise_documental as documental


class ConversaOrientadaTests(APITestCase):
    setUp = base.FichaEstruturadaTests.setUp
    create_case = base.FichaEstruturadaTests.create_case
    get = base.FichaEstruturadaTests.get
    post = base.FichaEstruturadaTests.post
    obj = base.FichaEstruturadaTests.obj
    field = base.FichaEstruturadaTests.field

    def send(self, case, text):
        return self.client.post(f'/api/v1/atendimentos/{case}/mensagens/', {'texto': text, 'client_id': str(uuid4())}, format='json')

    def correction(self, case, message, **kw):
        data = {'texto': 'RESPOSTA FICTÍCIA CORRIGIDA', 'justificativa': 'CORREÇÃO HUMANA SIMULADA', 'client_id': str(uuid4()), **kw}
        return self.client.post(f'/api/v1/atendimentos/{case}/mensagens/{message}/corrigir/', data, format='json'), data

    def test_received_counts_explicit_person_and_manual_uncertainty(self):
        case = self.create_case(); a = self.obj(case); b = self.obj(case)
        raw = '  Talvez seja representante; não foi possível identificar.  '
        message = self.send(case, raw)
        self.assertEqual(message.data['texto'], raw)
        response = self.client.get(f'/api/v1/atendimentos/{case}/roteiro-conversa/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        guide = response.data
        self.assertEqual(guide['modo'], 'orientacao_local_sem_ia')
        self.assertEqual(guide['recebido']['pessoas'], 2)
        self.assertEqual(guide['recebido']['mensagens'], 1)
        self.assertEqual(guide['total_pendencias'], len(guide['pendencias']))
        empty = [q for q in guide['pendencias'] if q.get('destino', {}).get('subtipo') == 'registro_vazio']
        self.assertEqual({q['destino']['objeto_id'] for q in empty}, {a,b})
        self.assertTrue(all(q['destino']['campo'] == 'nome' for q in empty))
        self.assertTrue(any(raw.strip() in str(q) for q in guide['pendencias']))
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())

    def test_append_only_idempotency_and_competing_correction(self):
        case = self.create_case(); old = self.send(case, '  TEXTO ORIGINAL FICTÍCIO  ').data
        corrected, data = self.correction(case, old['id'])
        self.assertEqual(corrected.status_code, 201, corrected.data)
        replay, _ = self.correction(case, old['id'], **data)
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(replay.data['id'], corrected.data['id'])
        conflict, _ = self.correction(case, old['id'])
        self.assertEqual(conflict.status_code, 409, conflict.data)
        self.assertEqual(MensagemAtendimento.objects.get(pk=old['id']).texto, old['texto'])
        self.assertEqual(MensagemAtendimento.objects.count(), 2)
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        self.assertEqual(str(corrected.data['correcao_de']), old['id'])
        self.assertEqual(self.correction(case, corrected.data['id'])[0].status_code, 201)

    def test_correction_invalidates_confirmed_source_without_rewriting_field(self):
        case = self.create_case(); person = self.obj(case)
        saved, _ = self.field(case, person, 'nome', 'PESSOA FICTÍCIA', situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.assertEqual(saved.status_code, 201, saved.data)
        revision = RevisaoDadoAtendimento.objects.get(objeto_id=person, chave='nome')
        self.assertTrue(fonte_atual(revision))
        count = RevisaoDadoAtendimento.objects.count()
        correction, _ = self.correction(case, str(revision.mensagem_id))
        self.assertEqual(correction.status_code, 201, correction.data)
        revision.refresh_from_db()
        self.assertFalse(fonte_atual(revision))
        self.assertEqual(revision.valor, 'PESSOA FICTÍCIA')
        self.assertEqual(RevisaoDadoAtendimento.objects.count(), count)
        guide = self.client.get(f'/api/v1/atendimentos/{case}/roteiro-conversa/').data
        self.assertTrue(guide['bloqueado'])
        self.assertTrue(any(q.get('destino',{}).get('objeto_id') == person for q in guide['pendencias']))
        reused, _ = self.field(case, person, 'nome', revision.valor, origem='mensagem', mensagem_id=str(revision.mensagem_id), trecho_origem=revision.valor, versao_esperada=1)
        self.assertEqual(reused.status_code, 409, reused.data)

    def test_other_case_cannot_correct_and_reloaded_client_keeps_server_history(self):
        case = self.create_case(); other = self.create_case()
        old = self.send(case, 'FICTÍCIO').data
        self.assertEqual(self.correction(other, old['id'])[0].status_code, 404)
        self.assertEqual(self.correction(case, old['id'], texto='   ')[0].status_code, 400)
        new, _ = self.correction(case, old['id'])
        fresh = APIClient(); fresh.force_authenticate(self.user)
        fresh.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        messages = fresh.get(f'/api/v1/atendimentos/{case}/mensagens/').data
        self.assertEqual(len(messages), 2)
        self.assertEqual(str(new.data['correcao_de']), old['id'])
        self.user.profile.tenants.add(self.other)
        fresh.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(fresh.get(f'/api/v1/atendimentos/{case}/roteiro-conversa/').status_code, 404)
        cross_tenant = fresh.post(f"/api/v1/atendimentos/{case}/mensagens/{new.data['id']}/corrigir/", {
            'texto': 'TENTATIVA FICTÍCIA ENTRE CARTÓRIOS', 'justificativa': 'TESTE DE ISOLAMENTO', 'client_id': str(uuid4())}, format='json')
        self.assertEqual(cross_tenant.status_code, 404)

    def test_corrected_message_proposal_stays_historical_and_cannot_fill_a_field(self):
        from tests import test_propostas_dados as proposals
        case = self.create_case(); person = self.obj(case)
        original = self.send(case, 'Nome: PESSOA FICTICIA ORIGINAL').data
        requested, _ = proposals.PropostasDadosTests.request_proposals(self, case, mensagem_id=original['id'])
        self.assertEqual(requested.status_code, 201, requested.data)
        proposal = proposals.PropostasDadosTests.proposals(self, case)[0]
        self.assertEqual(self.correction(case, original['id'])[0].status_code, 201)
        obsolete = proposals.PropostasDadosTests.proposals(self, case)[0]
        self.assertEqual(obsolete['situacao'], 'mensagem_corrigida')
        self.assertEqual(obsolete['trecho'], proposal['trecho'])
        repeated, _ = proposals.PropostasDadosTests.request_proposals(self, case, mensagem_id=original['id'])
        self.assertEqual(repeated.status_code, 409, repeated.data)
        refused = proposals.PropostasDadosTests.apply(self, case, person, obsolete)
        self.assertEqual(refused.status_code, 409, refused.data)
        self.assertFalse(RevisaoDadoAtendimento.objects.exists())


@override_settings(NOTARIUS_TESTE_ANALISE_DOCUMENTAL=True)
class ConversaProvedorSimuladoTests(APITestCase):
    setUp = documental.AnaliseDocumentalTests.setUp
    setUpBase = documental.AnaliseDocumentalTests.setUpBase
    create_case = documental.AnaliseDocumentalTests.create_case
    get = documental.AnaliseDocumentalTests.get
    post = documental.AnaliseDocumentalTests.post
    obj = documental.AnaliseDocumentalTests.obj
    field = documental.AnaliseDocumentalTests.field
    document = documental.AnaliseDocumentalTests.document
    classify = documental.AnaliseDocumentalTests.classify
    analyse = documental.AnaliseDocumentalTests.analyse

    def test_correction_during_simulated_analysis_refuses_every_result(self):
        from apps.processos.models import AnaliseDocumentalAtendimento, PropostaDadoAtendimento
        old = self.client.post(f'/api/v1/atendimentos/{self.case}/mensagens/', {'texto': 'TEXTO FICTÍCIO ORIGINAL', 'client_id': str(uuid4())}, format='json').data
        def change(data, entry):
            corrected, _ = ConversaOrientadaTests.correction(self, self.case, old['id'])
            self.assertEqual(corrected.status_code, 201, corrected.data)
            return data
        result, _ = self.analyse(change)
        self.assertEqual(result.status_code, 409, result.data)
        self.assertFalse(AnaliseDocumentalAtendimento.objects.exists())
        self.assertFalse(PropostaDadoAtendimento.objects.exists())

    def test_document_test_proposals_and_precise_manual_task_survive_reload(self):
        with patch('openai.OpenAI') as external:
            result, _ = self.analyse()
            self.assertEqual(result.status_code, 201, result.data)
            self.assertTrue(result.data['simulado'])
            url = f'/api/v1/atendimentos/{self.case}/roteiro-conversa/'
            before = self.client.get(url).data
            self.assertEqual(before['recebido']['documentos'], 1)
            self.assertGreater(before['recebido']['propostas'], 0)
            tasks = [q['destino'] for q in before['pendencias'] if q.get('destino',{}).get('subtipo') == 'analise_documental']
            self.assertTrue(tasks, before)
            self.assertTrue(any(t.get('trecho') or t.get('tarefa') for t in tasks), tasks)
            fresh = APIClient(); fresh.force_authenticate(self.user); fresh.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
            after = fresh.get(url).data
            self.assertEqual(before['recebido'], after['recebido'])
            self.assertEqual([q['chave'] for q in before['pendencias']], [q['chave'] for q in after['pendencias']])
            self.assertFalse(RevisaoDadoAtendimento.objects.exists())
        external.assert_not_called()

    def test_full_simulated_document_conversation_review_draft_and_export(self):
        from io import BytesIO
        from docx import Document
        from tests import test_redacao_estruturada as reda
        from tests import test_pendencias_ficha as pending
        # Every decision and model below exists exclusively in the isolated test DB.
        self.assertEqual(self.analyse()[0].status_code, 201)
        proposal = self.client.get(f'/api/v1/atendimentos/{self.case}/propostas-dados/').data['propostas'][0]
        response, _ = self.field(self.case, self.a, 'nome', proposal['valor_original'],
            origem='documento', pagina_id=proposal['origem']['pagina_id'], leitura_versao=1,
            trecho_origem=proposal['trecho'], proposta_id=proposal['id'], versao_proposta=0,
            conferir_associacao=True, situacao='confirmado', confirmar=True, conferir_fonte=True)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.field(self.case, self.b, 'nome', 'PESSOA FICTICIA BETA', situacao='confirmado', confirmar=True, conferir_fonte=True)[0].status_code, 201)
        # An uninterpreted task cannot disappear just because a name was accepted.
        rows = pending.PendenciasFichaTests.issues(self, self.case)
        for issue in rows:
            if issue['situacao'] == 'resolvida':
                continue
            if issue['tipo'] == 'analise_documental':
                r = pending.PendenciasFichaTests.decide(self, self.case, issue, acao='nao_utilizar')
                self.assertEqual(r.status_code, 201, r.data)
            elif issue['tipo'] == 'pagina':
                r = pending.PendenciasFichaTests.decide(self, self.case, issue, revisoes_ids=issue['contexto']['usos_atuais'])
                self.assertEqual(r.status_code, 201, r.data)
        positions = [{'chave': key, 'rotulo': 'POSIÇÃO FICTÍCIA '+key, 'tipo': 'pessoa', 'vinculos': {}} for key in ['parte1','parte2']]
        model = base.FichaEstruturadaTests.save_template(self, self.case, corpo='TESTE SIMULADO SEM VALIDADE\n{{parte1.nome}}\n{{parte2.nome}}', representacao='', observacoes='', registros_minuta=positions)
        self.assertEqual(model.status_code, 201, model.data)
        linked, _ = reda.RedacaoEstruturadaTests.binding(self, self.case, {'parte1': self.a, 'parte2': self.b})
        self.assertEqual(linked.status_code, 201, linked.data)
        guide = self.client.get(f'/api/v1/atendimentos/{self.case}/roteiro-conversa/').data
        self.assertEqual(guide['pendencias'], [], guide)
        fresh = APIClient(); fresh.force_authenticate(self.user); fresh.credentials(HTTP_X_TENANT_ID=str(self.tenant.id)); self.client = fresh
        with patch('openai.OpenAI') as external:
            draft_response = base.FichaEstruturadaTests.generate_draft(self, self.case)
            self.assertEqual(draft_response.status_code, 200, draft_response.data)
            draft = draft_response.data['versoes'][0]
            self.assertIn('PESSOA FICTICIA ALFA', draft['corpo'])
            self.assertIn('PESSOA FICTICIA BETA', draft['corpo'])
            r = self.client.post(f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/revisar/", {
                'versao_esperada': draft['versao'], 'motivo': 'REVISÃO FINAL SIMULADA EXCLUSIVA DE TESTE',
                'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, format='json')
            self.assertEqual(r.status_code, 201, r.data)
            export = self.client.get(f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/exportar/", {'formato':'docx'})
            self.assertEqual(export.status_code, 200)
            self.assertIn(draft['corpo'], '\n'.join(p.text for p in Document(BytesIO(export.content)).paragraphs))
        external.assert_not_called()
