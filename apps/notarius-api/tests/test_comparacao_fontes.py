from uuid import uuid4
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from apps.processos.models import (Atendimento, RevisaoDadoAtendimento, PropostaDadoAtendimento,
                                  DecisaoPropostaAtendimento, PendenciaFichaAtendimento)
from apps.processos.comparacao_fontes import normalizar_campo
from tests import test_ficha_estruturada as base


def cpf_ficticio(first):
    digits = first
    for count in (9, 10):
        digits += str((sum(int(digits[i]) * (count + 1 - i) for i in range(count)) * 10 % 11) % 10)
    return digits


class ComparacaoFontesTests(APITestCase):
    setUpBase = base.FichaEstruturadaTests.setUp
    create_case = base.FichaEstruturadaTests.create_case
    get = base.FichaEstruturadaTests.get
    post = base.FichaEstruturadaTests.post
    obj = base.FichaEstruturadaTests.obj
    field = base.FichaEstruturadaTests.field

    def setUp(self):
        self.setUpBase(); self.case = self.create_case()
        self.a, self.b, self.home = self.obj(self.case), self.obj(self.case), self.obj(self.case, 'imovel')
        self.deal = self.obj(self.case, 'negociacao', imovel_id=self.home)

    def confirmed(self, obj, key, value, **kw):
        response, _ = self.field(self.case, obj, key, value, situacao='confirmado', confirmar=True, conferir_fonte=True, **kw)
        self.assertEqual(response.status_code, 201, response.data)
        return str(RevisaoDadoAtendimento.objects.filter(objeto_id=obj, chave=key).first().id)

    def proposal(self, text, owner=None, message=False):
        if message:
            source = self.client.post(f'/api/v1/atendimentos/{self.case}/mensagens/', {'client_id': str(uuid4()), 'texto': text}, format='json').data
            selector = {'mensagem_id': source['id']}
        else:
            source = self.client.post(f'/api/v1/atendimentos/{self.case}/anexos/', {'arquivo': SimpleUploadedFile(f'{uuid4()}.txt', text.encode())}, format='multipart').data
            self.classify(source['id'], owner)
            selector = {'anexo_id': source['id'], 'leitura_versao': 1}
        response = self.client.post(f'/api/v1/atendimentos/{self.case}/propostas-dados/', {'operacao': 'extrair', 'client_id': str(uuid4()), **selector}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return PropostaDadoAtendimento.objects.get(id=response.data['propostas_ids'][0]), source

    def classify(self, file, owner, expected=0):
        response = self.client.post(f'/api/v1/atendimentos/{self.case}/anexos/{file}/organizacao/', {
            'client_id': str(uuid4()), 'versao_esperada': expected, 'leitura_versao': 1, 'finalidade': 'caso',
            'tipo_documento': 'Documento FICTÍCIO', 'vinculos': [{'objeto_id': owner, 'paginas': []}],
            'conferi': True, 'motivo': 'VÍNCULO DE TESTE EXPLICITAMENTE SIMULADO'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)

    def associate(self, p, obj, key, expected=0, **kw):
        return self.client.post(f'/api/v1/atendimentos/{self.case}/propostas-dados/', {
            'operacao': 'associar', 'client_id': str(uuid4()), 'proposta_id': str(p.id), 'versao_esperada': expected,
            'objeto_id': obj, 'campo': key, 'organizacao_versao': 1, 'conferir_associacao': True,
            'justificativa': 'ASSOCIAÇÃO HUMANA SIMULADA PARA COMPARAÇÃO, SEM CONFIRMAR', **kw}, format='json')

    def comparisons(self):
        response = self.client.get(f'/api/v1/atendimentos/{self.case}/comparacao-fontes/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        return response.data

    def group(self, obj, key):
        return next(g for g in self.comparisons()['grupos'] if g['objeto_id'] == obj and g['campo'] == key)

    def issue(self, obj, key):
        response = self.client.post(f'/api/v1/atendimentos/{self.case}/pendencias-ficha/', {'operacao': 'atualizar'}, format='json')
        return next(p for p in response.data['pendencias'] if p['chave'] == f'comparacao:{obj}:{key}')

    def resolve(self, issue, rid, **kw):
        return self.client.post(f'/api/v1/atendimentos/{self.case}/pendencias-ficha/', {
            'operacao': 'resolver', 'client_id': str(uuid4()), 'pendencia_id': issue['id'],
            'assinatura': issue['assinatura'], 'versao_esperada': issue['versao'], 'acao': 'vincular',
            'revisoes_ids': [rid], 'evidencias_ids': [e['id'] for e in issue['contexto']['evidencias']],
            'confirmei_revisao': True, 'justificativa': 'DECISÃO HUMANA FICTÍCIA: conferidas todas as fontes e escolhido o dado da ficha', **kw}, format='json')

    def test_cpf_difference_and_format_are_separate_from_original_and_identity(self):
        a, b = cpf_ficticio('123456789'), cpf_ficticio('987654321')
        self.confirmed(self.a, 'cpf', a)
        p, _ = self.proposal(f'CPF: {b}', self.a)
        self.assertEqual(self.associate(p, self.a, 'cpf').status_code, 201)
        group = self.group(self.a, 'cpf')
        self.assertIn('divergencia', group['problemas']); self.assertNotIn('formato_invalido', group['problemas'])
        self.assertIn(' ' + b, [e['valor_original'] for e in group['evidencias']])
        bad, _ = self.proposal('CPF: 000.000.000-00', self.a)
        self.assertEqual(self.associate(bad, self.a, 'cpf').status_code, 201)
        self.assertIn('formato_invalido', self.group(self.a, 'cpf')['problemas'])
        self.assertEqual(RevisaoDadoAtendimento.objects.get(objeto_id=self.a).valor, a)
        formatted = a[:3] + '.' + a[3:6] + '.' + a[6:9] + '-' + a[9:]
        self.assertEqual(normalizar_campo('pessoa', 'cpf', formatted)['valor'], a)

    def test_names_never_link_by_similarity_and_accents_are_not_removed(self):
        self.confirmed(self.a, 'nome', 'JOSÉ DA SILVA')
        self.confirmed(self.b, 'nome', 'JOSE DA SILVA')
        p, _ = self.proposal('Nome: JOSE DA SILVA', self.b)
        self.assertTrue(self.comparisons()['sem_vinculo'])
        self.assertEqual(len(self.group(self.a, 'nome')['evidencias']), 1)
        self.assertEqual(self.associate(p, self.a, 'nome').status_code, 400)
        self.assertEqual(self.associate(p, self.b, 'nome').status_code, 201)
        self.assertNotIn('divergencia', self.group(self.b, 'nome')['problemas'])
        self.assertNotEqual(normalizar_campo('pessoa', 'nome', 'José')['valor'], normalizar_campo('pessoa', 'nome', 'Jose')['valor'])
        other, _ = self.proposal('Nome: OUTRO NOME FICTÍCIO', message=True)
        self.assertEqual(self.associate(other, self.a, 'nome').status_code, 201)
        self.assertIn('divergencia', self.group(self.a, 'nome')['problemas'])

    def test_identification_document_and_property_reference_keep_punctuation_and_zeroes(self):
        for obj, key, label, original, conflicting, owner in [
            (self.a, 'documento_numero', 'RG', 'AB-001', 'AB001', self.a),
            (self.home, 'matricula', 'Matrícula', '00123', '123', self.home)]:
            with self.subTest(field=key):
                self.confirmed(obj, key, original)
                p, _ = self.proposal(f'{label}: {conflicting}', owner)
                self.assertEqual(self.associate(p, obj, key).status_code, 201)
                g = self.group(obj, key)
                self.assertIn('divergencia', g['problemas'])
                self.assertEqual(RevisaoDadoAtendimento.objects.get(objeto_id=obj, chave=key).valor_original, original)

    def test_distinct_literal_excerpts_on_same_page_are_preserved_for_review(self):
        raw = b'RG: AB-001\nRG: AB-002'
        upload = self.client.post(f'/api/v1/atendimentos/{self.case}/anexos/', {
            'arquivo': SimpleUploadedFile('DUAS-LEITURAS-FICTICIAS.txt', raw)}, format='multipart').data
        self.classify(upload['id'], self.a)
        for n, value in enumerate(['AB-001', 'AB-002']):
            result = self.field(self.case, self.a, 'documento_numero', value, valor_original=value,
                origem='documento', pagina_id=upload['paginas'][0]['id'], leitura_versao=1,
                trecho_origem=f'RG: {value}', versao_esperada=n)[0]
            self.assertEqual(result.status_code, 201, result.data)
        group = self.group(self.a, 'documento_numero')
        documents = [e for e in group['evidencias'] if e['tipo_fonte'] == 'documento']
        self.assertEqual({e['valor_original'] for e in documents}, {'AB-001', 'AB-002'})
        self.assertIn('divergencia', group['problemas'])

    def test_explicit_legacy_derivation_keeps_document_page_and_reading_visible(self):
        upload = self.client.post(f'/api/v1/atendimentos/{self.case}/anexos/', {
            'arquivo': SimpleUploadedFile('FONTE-LEGADA-FICTICIA.txt', b'Nome: PESSOA FICTICIA LEGADA')}, format='multipart').data
        self.classify(upload['id'], self.a)
        old = self.client.post(f'/api/v1/atendimentos/{self.case}/ficha/', {
            'chave':'vendedores','valor':'PESSOA FICTICIA LEGADA','situacao':'informado','versao_esperada':0,
            'pagina_id':upload['paginas'][0]['id'],'trecho_origem':'Nome: PESSOA FICTICIA LEGADA',
            'organizacao_versao':1,'justificativa':'FONTE LEGADA EXPLÍCITA SIMULADA'}, format='json')
        self.assertEqual(old.status_code, 201, old.data)
        copied = self.field(self.case, self.a, 'nome', 'PESSOA FICTICIA LEGADA', origem='legado',
            revisao_origem_id=old.data['id'], trecho_origem='PESSOA FICTICIA LEGADA', organizacao_versao=1)[0]
        self.assertEqual(copied.status_code, 201, copied.data)
        source = next(e for e in self.group(self.a, 'nome')['evidencias'] if e['tipo_fonte'] == 'documento')['fonte']
        self.assertEqual(source['arquivo'], 'FONTE-LEGADA-FICTICIA.txt')
        self.assertEqual(source['pagina'], 1); self.assertEqual(source['leitura_versao'], 1)
        self.assertEqual(source['trecho'], 'Nome: PESSOA FICTICIA LEGADA')
        self.assertEqual(source['origem_legada']['revisao_id'], old.data['id'])

    def test_price_formats_currency_and_payment_negation_do_not_become_facts(self):
        self.confirmed(self.deal, 'preco', 'R$ 1.000,00')
        p, _ = self.proposal('Preço: R$ 1000,00', self.home)
        self.assertEqual(self.associate(p, self.deal, 'preco').status_code, 201)
        self.assertNotIn('divergencia', self.group(self.deal, 'preco')['problemas'])
        p2, _ = self.proposal('Preço: R$ 1.100,00', message=True)
        self.assertEqual(self.associate(p2, self.deal, 'preco').status_code, 201)
        self.assertIn('divergencia', self.group(self.deal, 'preco')['problemas'])
        self.confirmed(self.deal, 'situacao_pagamento', 'previsto')
        paid, _ = self.proposal('Situação do pagamento: declarado_realizado', message=True)
        self.assertEqual(self.associate(paid, self.deal, 'situacao_pagamento').status_code, 201)
        self.assertIn('divergencia', self.group(self.deal, 'situacao_pagamento')['problemas'])
        self.assertEqual(RevisaoDadoAtendimento.objects.get(objeto_id=self.deal, chave='situacao_pagamento').valor, 'previsto')
        self.assertNotEqual(normalizar_campo('negociacao', 'condicoes', 'não foi pago')['valor'], normalizar_campo('negociacao', 'condicoes', 'foi pago')['valor'])
        self.assertIn('formato_invalido', normalizar_campo('negociacao', 'preco', '1.234')['problemas'])

    def test_absence_uncertain_reading_and_uncertain_link_are_different_states(self):
        p, file = self.proposal('Nome: PESSOA FICTÍCIA', self.a)
        self.assertEqual(self.comparisons()['sem_vinculo'][0]['problemas'], ['vinculo_incerto'])
        self.assertEqual(self.associate(p, self.a, 'nome').status_code, 201)
        self.assertIn('ausente', self.group(self.a, 'nome')['problemas'])
        page = p.pagina; page.situacao = 'revisao'; page.save()
        self.assertIn('leitura_incerta', self.group(self.a, 'nome')['problemas'])
        self.classify(file['id'], self.b, expected=1)
        g = self.group(self.a, 'nome')
        self.assertIn('vinculo_incerto', g['problemas'])
        self.assertTrue(all(not e['comparavel'] for e in g['evidencias']))
        self.assertEqual(self.associate(p, self.b, 'nome', expected=1).status_code, 409)

    def test_human_resolution_records_all_evidence_and_new_source_reopens_same_issue(self):
        chosen = self.confirmed(self.a, 'nome', 'NOME FICTÍCIO A')
        p, _ = self.proposal('Nome: NOME FICTÍCIO B', self.a)
        self.associate(p, self.a, 'nome')
        issue = self.issue(self.a, 'nome')
        self.assertEqual(self.resolve(issue, chosen, evidencias_ids=[]).status_code, 400)
        self.assertEqual(self.resolve(issue, chosen, confirmei_revisao=False).status_code, 400)
        self.assertEqual(self.resolve(issue, chosen).status_code, 201)
        saved = PendenciaFichaAtendimento.objects.get(id=issue['id'])
        self.assertEqual(saved.situacao, 'resolvida')
        self.assertEqual(saved.resolucao['valor_escolhido'], 'NOME FICTÍCIO A')
        self.assertEqual(saved.resolucao['autor_id'], str(self.user.id))
        self.assertEqual(len(saved.resolucao['evidencias_consideradas']), 2)
        p2, _ = self.proposal('Nome: NOME FICTÍCIO C', message=True)
        self.associate(p2, self.a, 'nome')
        reopened = self.issue(self.a, 'nome')
        self.assertEqual(reopened['id'], issue['id']); self.assertEqual(reopened['situacao'], 'reaberta')
        self.assertEqual(self.resolve(issue, chosen).status_code, 409)
        self.assertEqual(self.resolve(reopened, chosen).status_code, 201)
        self.assertGreaterEqual(saved.historico.count(), 3)

    def test_association_is_separate_from_confirmation_and_isolated_and_versioned(self):
        p, _ = self.proposal('Nome: PESSOA FICTÍCIA', self.a)
        before = RevisaoDadoAtendimento.objects.count()
        response = self.associate(p, self.a, 'nome', conferir_associacao=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.associate(p, self.a, 'nome').status_code, 201)
        self.assertEqual(RevisaoDadoAtendimento.objects.count(), before)
        self.assertEqual(self.associate(p, self.a, 'nome').status_code, 409)
        other = self.create_case(); foreign = self.obj(other)
        self.assertEqual(self.associate(p, foreign, 'nome', expected=1).status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{other}/comparacao-fontes/').data['grupos'], [])
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.client.get(f'/api/v1/atendimentos/{self.case}/comparacao-fontes/').status_code, 403)

    def test_wrong_field_or_person_revision_cannot_resolve_and_bad_cpf_stays_blocked(self):
        a = self.confirmed(self.a, 'cpf', '000.000.000-00')
        b = self.confirmed(self.b, 'cpf', cpf_ficticio('123456789'))
        issue = self.issue(self.a, 'cpf')
        self.assertEqual(self.resolve(issue, b).status_code, 400)
        self.assertEqual(self.resolve(issue, a).status_code, 400)
        self.assertEqual(self.issue(self.a, 'cpf')['situacao'], 'aberta')

    def test_optional_absence_is_not_a_new_requirement_and_waiver_cannot_bypass_model(self):
        self.assertEqual(self.field(self.case, self.a, 'orgao_emissor', '', situacao='ausente')[0].status_code, 201)
        group = self.group(self.a, 'orgao_emissor')
        self.assertEqual(group['problemas'], ['ausente'])
        self.assertFalse(group['conferencia_necessaria'])
        self.confirmed(self.a, 'nome', 'NOME FICTÍCIO A')
        p, _ = self.proposal('Nome: NOME FICTÍCIO B', self.a); self.associate(p, self.a, 'nome')
        self.issue(self.a, 'nome')
        self.assertEqual(self.field(self.case, self.a, 'nome', '', situacao='ausente', versao_esperada=1)[0].status_code, 201)
        issue = self.issue(self.a, 'nome')
        self.assertIn('nao_utilizar', issue['acoes'])
        self.assertEqual(self.resolve(issue, '', acao='nao_utilizar', revisoes_ids=[]).status_code, 201)
        configured = base.FichaEstruturadaTests.save_template(self, self.case, campos_obrigatorios_ficha=[{'tipo':'pessoa', 'chave':'nome'}])
        self.assertEqual(configured.status_code, 201)
        required = self.issue(self.a, 'nome')
        self.assertTrue(required['contexto']['exigido_modelo'])
        self.assertNotIn('nao_utilizar', required['acoes'])
        self.assertEqual(required['situacao'], 'reaberta')
        self.assertEqual(self.resolve(required, '', acao='nao_utilizar', revisoes_ids=[]).status_code, 400)

    def test_rereading_reopens_conference_and_keeps_resolution_history(self):
        chosen = self.confirmed(self.a, 'nome', 'NOME FICTÍCIO A')
        p, source = self.proposal('Nome: NOME FICTÍCIO B', self.a)
        self.associate(p, self.a, 'nome')
        issue = self.issue(self.a, 'nome')
        self.assertEqual(self.resolve(issue, chosen).status_code, 201)
        # TXT has no reread endpoint; simulate the same append-only transition
        # exercised by PDF/OCR tests without changing the preserved original.
        from apps.processos.models import AnexoAtendimento, PaginaAnexoAtendimento
        file = AnexoAtendimento.objects.get(id=source['id'])
        original = bytes(file.conteudo); file.leitura_versao = 2; file.save()
        PaginaAnexoAtendimento.objects.create(tenant=self.tenant, anexo=file, numero=1, leitura_versao=2,
            texto='Nome: NOME FICTÍCIO C', situacao='extraido')
        reopened = self.issue(self.a, 'nome')
        self.assertEqual(reopened['situacao'], 'reaberta')
        self.assertIn('leitura_incerta', reopened['contexto']['problemas'])
        self.assertEqual(self.resolve(issue, chosen).status_code, 409)
        self.assertEqual(bytes(AnexoAtendimento.objects.get(id=file.id).conteudo), original)
        self.assertTrue(PendenciaFichaAtendimento.objects.get(id=issue['id']).historico.filter(resolucao__valor_escolhido='NOME FICTÍCIO A').exists())

    def test_evidence_and_decision_invalidate_draft_and_prevent_export(self):
        self.case = self.create_case(); self.a = self.obj(self.case)
        self.confirmed(self.a, 'nome', 'PESSOA FICTÍCIA ORIGINAL')
        model = base.FichaEstruturadaTests.save_template(self, self.case, corpo='EXEMPLO FICTÍCIO\n{{parte.nome}}',
            representacao='', observacoes='', registros_minuta=[{'chave': 'parte', 'rotulo': 'Parte fictícia', 'tipo': 'pessoa', 'vinculos': {}}])
        self.assertEqual(model.status_code, 201, model.data)
        state = self.client.get(f'/api/v1/atendimentos/{self.case}/vinculacao-minuta/').data
        bound = self.client.post(f'/api/v1/atendimentos/{self.case}/vinculacao-minuta/', {
            'client_id': str(uuid4()), 'modelo_id': state['modelo_id'], 'versao_esperada': 0,
            'escopo_assinatura': state['escopo_assinatura'], 'registros': {'parte': self.a}, 'exclusoes': [],
            'conferir': True, 'motivo': 'VINCULAÇÃO FICTÍCIA SIMULADA'}, format='json')
        self.assertEqual(bound.status_code, 201, bound.data)
        result = base.FichaEstruturadaTests.generate_draft(self, self.case)
        self.assertEqual(result.status_code, 200, result.data)
        draft = result.data['versoes'][0]
        review = self.client.post(f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/revisar/", {
            'versao_esperada': draft['versao'], 'motivo': 'REVISÃO FINAL FICTÍCIA SIMULADA',
            'conferi_texto': True, 'conferi_dados': True, 'conferi_fontes': True}, format='json')
        self.assertEqual(review.status_code, 201, review.data)
        export = f"/api/v1/atendimentos/{self.case}/minutas/{draft['id']}/exportar/"
        self.assertEqual(self.client.get(export, {'formato': 'docx'}).status_code, 200)
        p, _ = self.proposal('Nome: PESSOA FICTÍCIA DIVERGENTE', message=True)
        self.associate(p, self.a, 'nome')
        current = self.client.get(f'/api/v1/atendimentos/{self.case}/minuta-preparada/').data
        self.assertTrue(current['versoes'][0]['desatualizada'])
        self.assertEqual(self.client.get(export, {'formato': 'docx'}).status_code, 409)
        self.assertEqual(base.FichaEstruturadaTests.generate_draft(self, self.case).status_code, 400)
        issue = self.issue(self.a, 'nome')
        chosen = str(RevisaoDadoAtendimento.objects.get(objeto_id=self.a, chave='nome').id)
        self.assertEqual(self.resolve(issue, chosen).status_code, 201)
        self.assertEqual(self.client.get(export, {'formato': 'docx'}).status_code, 409)
