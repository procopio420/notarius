from uuid import uuid4
from rest_framework.test import APITestCase
from apps.processos.models import Atendimento, MinutaAtendimento, RevisaoFinalMinuta
from tests import test_atendimentos as helpers

class RevisaoFinalTests(APITestCase):
    setUp=helpers.AtendimentoTests.setUp
    create_case=helpers.AtendimentoTests.create_case
    report=helpers.AtendimentoTests.report
    answer=helpers.AtendimentoTests.answer
    ready_for_draft=helpers.AtendimentoTests.ready_for_draft
    save_template=helpers.AtendimentoTests.save_template
    generate_draft=helpers.AtendimentoTests.generate_draft
    draft_for_editing=helpers.AtendimentoTests.draft_for_editing
    edit_draft=helpers.AtendimentoTests.edit_draft
    review_draft=helpers.AtendimentoTests.review_draft

    def export(self,case,draft):
        return self.client.get(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/exportar/",{'formato':'docx'})

    def test_explicit_review_required_and_retry_is_idempotent(self):
        case,draft=self.draft_for_editing()
        self.assertEqual(self.export(case,draft).status_code,409)
        url=f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/"
        payload={'versao_esperada':draft['versao'],'motivo':'Teste fictício','conferi_texto':True,'conferi_dados':True}
        self.assertEqual(self.client.post(url,payload,format='json').status_code,400)
        review=self.review_draft(case,draft)
        self.assertTrue(review.data['texto_corresponde'])
        self.review_draft(case,draft)
        self.assertEqual(RevisaoFinalMinuta.objects.count(),1)
        self.assertEqual(self.export(case,draft).status_code,200)
        payload.update(conferi_fontes=True)
        self.assertEqual(self.client.post(url,payload,format='json').status_code,409)

    def test_new_edit_does_not_inherit_review_and_old_version_stays_blocked(self):
        case,draft=self.draft_for_editing()
        self.review_draft(case,draft)
        edited,_=self.edit_draft(case,draft,draft['corpo']+'\nAjuste fictício')
        self.assertEqual(edited.status_code,201)
        self.assertEqual(self.export(case,edited.data).status_code,409)
        self.assertEqual(self.export(case,draft).status_code,409)
        state=self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data
        self.assertIsNone(state['versoes'][0]['revisao_final'])
        self.assertIsNotNone(state['versoes'][1]['revisao_final'])
        self.review_draft(case,edited.data)
        self.assertEqual(self.export(case,edited.data).status_code,200)

    def test_new_evidence_invalidates_export_even_after_review(self):
        case,draft=self.draft_for_editing()
        self.review_draft(case,draft)
        self.client.post(f'/api/v1/atendimentos/{case}/mensagens/',{'texto':'Nova informação fictícia','client_id':str(uuid4())},format='json')
        self.assertEqual(self.export(case,draft).status_code,409)
        self.assertEqual(RevisaoFinalMinuta.objects.count(),1)
        response=self.client.post(f"/api/v1/atendimentos/{case}/minutas/{draft['id']}/revisar/",{'versao_esperada':draft['versao'],'motivo':'Não ignorar mudança','conferi_texto':True,'conferi_dados':True,'conferi_fontes':True},format='json')
        self.assertEqual(response.status_code,409)

    def test_review_is_case_scoped_and_bound_to_saved_text_hash(self):
        case,draft=self.draft_for_editing()
        other=Atendimento.objects.create(tenant=self.other,criado_por=self.user,titulo='Outro cartório')
        payload={'versao_esperada':draft['versao'],'motivo':'Teste','conferi_texto':True,'conferi_dados':True,'conferi_fontes':True}
        self.assertEqual(self.client.post(f"/api/v1/atendimentos/{other.id}/minutas/{draft['id']}/revisar/",payload,format='json').status_code,404)
        self.review_draft(case,draft)
        # Simulate out-of-band corruption: a prior review must not cover different bytes.
        MinutaAtendimento.objects.filter(pk=draft['id']).update(corpo=draft['corpo']+'\nTexto alterado diretamente')
        self.assertEqual(self.export(case,draft).status_code,409)
        latest=self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['versoes'][0]
        self.assertFalse(latest['revisao_final']['texto_corresponde'])
