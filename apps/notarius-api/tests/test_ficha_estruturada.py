from uuid import uuid4
from threading import Event, Thread
from unittest.mock import patch
from django.db import connection, close_old_connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APITransactionTestCase
from apps.processos.models import (Atendimento, ObjetoFichaAtendimento, RevisaoDadoAtendimento,
                                   MensagemAtendimento, PaginaAnexoAtendimento)
from apps.processos.ficha_estruturada import alterar, FichaAlterada
from apps.processos.ficha_estruturada_schema import verificar_cpf
from tests import test_atendimentos as helpers


class FichaEstruturadaTests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case
    save_template = helpers.AtendimentoTests.save_template
    ready_for_draft = helpers.AtendimentoTests.ready_for_draft
    answer = helpers.AtendimentoTests.answer
    report = helpers.AtendimentoTests.report
    generate_draft = helpers.AtendimentoTests.generate_draft

    def get(self, case):
        return self.client.get(f'/api/v1/atendimentos/{case}/ficha-detalhada/')

    def post(self, case, payload):
        from tests.fontes_ficticias import preparar_campos
        preparar_campos(self, case, payload)
        opened = self.get(case).data
        data = {'client_id': str(uuid4()), 'modelo_id': opened.get('modelo_id'),
                'justificativa': 'TESTE FICTÍCIO: decisão humana explícita', **payload}
        contexts = {f['chave']: f['contexto_assinatura'] for o in opened.get('objetos', []) if o['id'] == data.get('objeto_id') for f in o['campos']}
        for field in data.get('campos', []):
            if field['chave'] in contexts:
                field.setdefault('contexto_assinatura', contexts[field['chave']])
        return self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', data, format='json'), data

    def obj(self, case, tipo='pessoa', **links):
        response, _ = self.post(case, {'operacao': 'criar', 'tipo': tipo, **links})
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['objeto_id']

    def field(self, case, obj, key, value, **overrides):
        item = {'chave': key, 'valor': value, 'valor_original': value, 'situacao': 'informado',
                'versao_esperada': 0, 'origem': 'manual', **overrides}
        return self.post(case, {'operacao': 'salvar', 'objeto_id': obj, 'campos': [item]})

    def test_multiple_people_same_name_own_ids_roles_and_no_inferred_relations(self):
        case = self.create_case()
        a, b = self.obj(case), self.obj(case)
        self.assertNotEqual(a, b)
        for person in [a, b]:
            self.assertEqual(self.field(case, person, 'nome', 'PESSOA FICTÍCIA HOMÔNIMA')[0].status_code, 201)
        self.field(case, a, 'estado_civil', 'casada')
        seller = self.obj(case, 'papel', pessoa_a_id=a)
        buyer = self.obj(case, 'papel', pessoa_a_id=b)
        additional = self.obj(case, 'papel', pessoa_a_id=a)
        for obj, role in [(seller, 'vendedor'), (buyer, 'comprador'), (additional, 'interveniente')]:
            self.assertEqual(self.field(case, obj, 'tipo_papel', role)[0].status_code, 201)
        self.assertEqual(ObjetoFichaAtendimento.objects.filter(tipo='relacao').count(), 0)
        data = self.get(case).data['objetos']
        self.assertEqual(len([o for o in data if o['tipo'] == 'pessoa']), 2)
        self.assertEqual(len([o for o in data if o['tipo'] == 'papel' and o['pessoa_a_id'] == a]), 2)

    def test_explicit_spouse_and_representative_links_are_directional_and_separate(self):
        case = self.create_case()
        a, b, c = self.obj(case), self.obj(case), self.obj(case)
        spouse = self.obj(case, 'relacao', pessoa_a_id=a, pessoa_b_id=b)
        rep = self.obj(case, 'relacao', pessoa_a_id=c, pessoa_b_id=a)
        self.field(case, spouse, 'tipo_relacao', 'conjuge_de')
        self.field(case, rep, 'tipo_relacao', 'representante_de')
        self.assertEqual(ObjetoFichaAtendimento.objects.filter(tipo='relacao').count(), 2)
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'relacao', 'pessoa_a_id': a, 'pessoa_b_id': a})[0].status_code, 400)
        self.assertEqual(self.post(case, {'operacao': 'criar', 'tipo': 'papel'})[0].status_code, 400)

    def test_property_price_conditions_and_payment_status_do_not_copy_into_each_other(self):
        case = self.create_case()
        home = self.obj(case, 'imovel')
        negotiation = self.obj(case, 'negociacao', imovel_id=home)
        for key, value in [('preco', 'VALOR FICTÍCIO'), ('condicoes', 'Pagamento futuro conforme ajuste fictício'), ('situacao_pagamento', 'previsto')]:
            self.assertEqual(self.field(case, negotiation, key, value)[0].status_code, 201)
        fields = next(o for o in self.get(case).data['objetos'] if o['id'] == negotiation)['campos']
        self.assertIsNone(next(f for f in fields if f['chave'] == 'quitacao')['atual'])
        self.assertIsNone(next(f for f in fields if f['chave'] == 'comprovante')['atual'])
        self.assertEqual(self.field(case, home, 'preco', 'ERRO DE OBJETO')[0].status_code, 400)

    def test_raw_values_history_human_confirmation_and_stale_write(self):
        case = self.create_case(); person = self.obj(case)
        raw = '  PESSOA FICTÍCIA COM ESPAÇOS  '
        response, payload = self.field(case, person, 'nome', raw)
        self.assertEqual(response.status_code, 201)
        revised = self.field(case, person, 'nome', 'PESSOA FICTÍCIA CORRIGIDA', versao_esperada=1,
                             situacao='confirmado', confirmar=True, conferir_fonte=True)[0]
        self.assertEqual(revised.status_code, 201)
        field = self.get(case).data['objetos'][0]['campos'][0]
        self.assertEqual(self.report(case)['orientacao']['nao_interpretados'], [])
        self.assertEqual([r['versao'] for r in field['historico']], [2, 1])
        self.assertEqual(field['historico'][1]['valor_original'], raw)
        self.assertIsNone(field['historico'][1]['confirmacao'])
        self.assertEqual(field['atual']['confirmacao']['autor_id'], str(self.user.id))
        self.assertEqual(self.field(case, person, 'nome', 'SOBRESCRITA', versao_esperada=1)[0].status_code, 409)
        self.assertEqual(MensagemAtendimento.objects.filter(texto='SOBRESCRITA').count(), 0)

    def test_confirmation_never_inferred_and_cpf_math_does_not_prove_identity(self):
        case = self.create_case(); person = self.obj(case)
        self.assertEqual(self.field(case, person, 'cpf', '000.000.000-00', situacao='confirmado')[0].status_code, 400)
        self.assertEqual(self.field(case, person, 'cpf', '000.000.000-00')[0].status_code, 201)
        field = next(f for f in self.get(case).data['objetos'][0]['campos'] if f['chave'] == 'cpf')
        self.assertFalse(field['atual']['validacao_formato']['digitos_consistentes'])
        self.assertFalse(field['atual']['validacao_formato']['identidade_comprovada'])
        self.assertEqual(field['atual']['situacao'], 'informado')
        # Algorithm-generated number only for mathematical test; no person attached.
        digits = '123456789'
        for count in (9, 10):
            digits += str((sum(int(digits[i]) * (count + 1 - i) for i in range(count)) * 10 % 11) % 10)
        self.assertTrue(verificar_cpf(digits)['digitos_consistentes'])
        self.assertFalse(verificar_cpf(digits)['identidade_comprovada'])

    def test_document_literal_original_correction_and_replaced_reading(self):
        case = self.create_case(); person = self.obj(case)
        upload = self.client.post(f'/api/v1/atendimentos/{case}/anexos/',
            {'arquivo': SimpleUploadedFile('ficticio.txt', b'Nome: PESSOA FICTICIA ORIGINAL')}, format='multipart')
        page = upload.data['paginas'][0]
        source = dict(origem='documento', pagina_id=page['id'], leitura_versao=1,
                      trecho_origem='Nome: PESSOA FICTICIA ORIGINAL', valor_original='PESSOA FICTICIA ORIGINAL')
        first = self.field(case, person, 'nome', 'PESSOA FICTICIA ORIGINAL', situacao='extraido', **source)[0]
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.field(case, person, 'nome', 'CORREÇÃO HUMANA', versao_esperada=1,
            situacao='confirmado', confirmar=True, conferir_fonte=True, **source)[0].status_code, 201)
        current = self.get(case).data['objetos'][0]['campos'][0]['atual']
        self.assertEqual(current['valor_original'], 'PESSOA FICTICIA ORIGINAL')
        self.assertEqual(current['valor'], 'CORREÇÃO HUMANA')
        self.assertEqual(current['origem']['pagina'], 1)
        self.assertEqual(current['origem']['leitura_versao'], 1)
        attachment = PaginaAnexoAtendimento.objects.get(id=page['id']).anexo
        attachment.leitura_versao = 2; attachment.save()
        self.assertFalse(self.get(case).data['objetos'][0]['campos'][0]['atual']['fonte_atual'])
        self.assertFalse(self.get(case).data['objetos'][0]['campos'][0]['atual']['confirmacao_atual'])
        self.assertEqual(self.get(case).data['objetos'][0]['campos'][0]['atual']['situacao_efetiva'], 'reaberta')
        self.assertEqual(self.field(case, person, 'nome', 'OUTRA', versao_esperada=2, **source)[0].status_code, 409)

    def test_sources_and_links_are_scoped_to_case_and_tenant(self):
        case = self.create_case(); other = self.create_case()
        a, b = self.obj(case), self.obj(other)
        self.assertEqual(self.post(case, {'operacao':'criar', 'tipo':'papel', 'pessoa_a_id':b})[0].status_code, 404)
        self.assertEqual(self.field(case, b, 'nome', 'ERRO')[0].status_code, 404)
        message = self.client.post(f'/api/v1/atendimentos/{other}/mensagens/', {'texto':'FONTE FICTÍCIA', 'client_id':str(uuid4())}, format='json').data
        self.assertEqual(self.field(case, a, 'nome', 'FONTE FICTÍCIA', origem='mensagem', mensagem_id=message['id'], trecho_origem='FONTE FICTÍCIA')[0].status_code, 404)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.other.id))
        self.assertEqual(self.get(case).status_code, 403)
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', {}, format='json').status_code, 403)

    def test_literal_message_source_is_retained_and_wrong_excerpt_rejected(self):
        case = self.create_case(); a = self.obj(case)
        message = self.client.post(f'/api/v1/atendimentos/{case}/mensagens/', {'texto':'Nome: PESSOA FICTÍCIA', 'client_id':str(uuid4())}, format='json').data
        source = dict(origem='mensagem', mensagem_id=message['id'], trecho_origem='Nome: PESSOA FICTÍCIA')
        self.assertEqual(self.field(case, a, 'nome', 'PESSOA FICTÍCIA', **source)[0].status_code, 201)
        current = self.get(case).data['objetos'][0]['campos'][0]['atual']
        self.assertEqual(current['origem']['mensagem_id'], message['id'])
        self.assertEqual(current['origem']['trecho'], source['trecho_origem'])
        self.assertEqual(self.field(case, a, 'cpf', 'ERRO', origem='mensagem', mensagem_id=message['id'], trecho_origem='INVENTADO')[0].status_code, 400)

    def test_legacy_text_not_split_and_explicit_derivation_keeps_old_revisions(self):
        case = self.create_case()
        old = self.client.post(f'/api/v1/atendimentos/{case}/ficha/', {'chave':'vendedores',
            'valor':'PESSOA ALFA e PESSOA BETA, qualificação a esclarecer', 'situacao':'informado',
            'justificativa':'LEGADO FICTÍCIO', 'versao_esperada':0}, format='json').data
        self.assertEqual(self.get(case).data['objetos'], [])
        self.assertEqual(self.get(case).data['legado'][0]['valor'], old['valor'])
        person = self.obj(case)
        response = self.field(case, person, 'nome', 'PESSOA ALFA', origem='legado',
            revisao_origem_id=old['id'], trecho_origem='PESSOA ALFA e PESSOA BETA', valor_original='PESSOA ALFA')[0]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.get(case).data['objetos'][0]['campos'][0]['atual']['origem']['revisao_id'], old['id'])
        legacy = RevisaoDadoAtendimento.objects.get(id=old['id'])
        self.assertIsNone(legacy.objeto_id)
        self.assertEqual(legacy.valor, old['valor'])
        self.assertEqual(ObjetoFichaAtendimento.objects.filter(tipo='pessoa').count(), 1)

    def test_group_is_atomic_and_retry_does_not_duplicate(self):
        case = self.create_case(); a = self.obj(case)
        response, payload = self.field(case, a, 'nome', 'PESSOA FICTÍCIA')
        again = self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', payload, format='json')
        self.assertEqual(again.status_code, 200)
        self.assertEqual(response.data, again.data)
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(objeto_id=a).count(), 1)
        payload['campos'][0]['valor'] = 'ALTERADO'
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', payload, format='json').status_code, 400)
        fields = [{'chave':'cpf', 'valor':'FICTÍCIO', 'situacao':'informado', 'origem':'manual', 'versao_esperada':0},
                  {'chave':'nome', 'valor':'OUTRO', 'situacao':'informado', 'origem':'manual', 'versao_esperada':0}]
        self.assertEqual(self.post(case, {'operacao':'salvar', 'objeto_id':a, 'campos':fields})[0].status_code, 409)
        self.assertFalse(RevisaoDadoAtendimento.objects.filter(objeto_id=a, chave='cpf').exists())
        self.assertFalse(MensagemAtendimento.objects.filter(texto='FICTÍCIO').exists())

    def test_creation_retry_and_no_link_type_coercion(self):
        case = self.create_case()
        response, payload = self.post(case, {'operacao':'criar', 'tipo':'pessoa'})
        again = self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', payload, format='json')
        self.assertEqual(response.data, again.data)
        self.assertEqual(ObjetoFichaAtendimento.objects.count(), 1)
        home = self.obj(case, 'imovel')
        self.assertEqual(self.post(case, {'operacao':'criar', 'tipo':'papel', 'pessoa_a_id':home})[0].status_code, 404)
        self.assertEqual(self.post(case, {'operacao':'criar', 'tipo':'pessoa', 'pessoa_a_id':response.data['objeto_id']})[0].status_code, 400)

    def test_configured_qualification_is_versioned_and_removal_keeps_history(self):
        case = self.create_case()
        config = [{'chave':'extra_domicilio', 'rotulo':'Domicílio informado no modelo', 'grupo':'Qualificação'}]
        first = self.save_template(case, campos_qualificacao=config)
        self.assertEqual(first.status_code, 201)
        person = self.obj(case)
        response, payload = self.field(case, person, 'extra_domicilio', 'LOCAL FICTÍCIO')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.save_template(case, expected=1, campos_qualificacao=[]).status_code, 201)
        payload['client_id'] = str(uuid4()); payload['campos'][0]['versao_esperada'] = 1
        self.assertEqual(self.client.post(f'/api/v1/atendimentos/{case}/ficha-detalhada/', payload, format='json').status_code, 409)
        field = next(f for f in self.get(case).data['objetos'][0]['campos'] if f['chave']=='extra_domicilio')
        self.assertEqual(field['atual']['valor'], 'LOCAL FICTÍCIO')
        self.assertEqual(field['atual']['rotulo_original'], config[0]['rotulo'])
        self.assertEqual(field['grupo'], 'Histórico do modelo')
        self.assertEqual(self.field(case, person, 'campo_nao_configurado', 'SEM CAMPO')[0].status_code, 400)

    def test_invalid_qualification_config_and_cross_case_legacy_source_rejected(self):
        case = self.create_case(); other = self.create_case()
        self.assertEqual(self.save_template(case, campos_qualificacao=[{'chave':'nome','rotulo':'Troca de significado','grupo':'Qualificação'}]).status_code, 400)
        old = self.client.post(f'/api/v1/atendimentos/{other}/ficha/', {'chave':'imovel','valor':'IMÓVEL FICTÍCIO','situacao':'informado','justificativa':'teste','versao_esperada':0}, format='json').data
        person = self.obj(case)
        self.assertEqual(self.field(case, person, 'nome', 'IMÓVEL FICTÍCIO', origem='legado', revisao_origem_id=old['id'], trecho_origem='IMÓVEL FICTÍCIO')[0].status_code, 404)

    def test_structured_data_invalidates_old_draft_without_silent_aggregation(self):
        case = self.ready_for_draft(); self.save_template(case)
        self.assertEqual(self.generate_draft(case).status_code, 200)
        person = self.obj(case)
        self.field(case, person, 'nome', 'PESSOA DETALHADA')
        legacy = self.client.get(f'/api/v1/atendimentos/{case}/ficha/').data['campos']
        self.assertNotIn('nome', [f['chave'] for f in legacy])
        self.assertNotEqual(next(f for f in legacy if f['chave']=='vendedores')['atual']['valor'], 'PESSOA DETALHADA')
        question = self.report(case)['pendencias'][0]
        self.assertEqual(question['tipo'], 'pendencia_ficha')
        self.assertIn('ficha_estruturada', [q['chave'] for q in self.report(case)['pendencias']])
        self.assertEqual(self.answer(case, 'ficha_estruturada', 'IGNORAR DADOS')[0].status_code, 400)
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertTrue(self.client.get(f'/api/v1/atendimentos/{case}/minuta-preparada/').data['versoes'][0]['desatualizada'])


class ConcorrenciaFichaTests(APITransactionTestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case

    def test_overlapping_sqlite_writers_preserve_one_version_and_rollback_loser(self):
        if connection.vendor != 'sqlite':
            self.skipTest('Teste de sobreposição do escritor SQLite; PostgreSQL requer seu ambiente próprio.')
        from apps.processos import ficha_estruturada as service
        case = Atendimento.objects.get(pk=self.create_case())
        result, _ = alterar(case, self.user, {'client_id':str(uuid4()), 'modelo_id':None,
            'operacao':'criar', 'tipo':'pessoa', 'justificativa':'TESTE FICTÍCIO'})
        payload = {'client_id':str(uuid4()), 'modelo_id':None, 'operacao':'salvar', 'objeto_id':result['objeto_id'],
                   'justificativa':'ESCRITOR FICTÍCIO', 'campos':[{'chave':'nome','valor':'PRIMEIRO FICTÍCIO','situacao':'informado','origem':'manual','versao_esperada':0}]}
        entered, release = Event(), Event()
        real_source = service._source
        outcome = []
        def hold_source(*args):
            entered.set()
            if not release.wait(10):
                raise RuntimeError('Teste não liberou o escritor.')
            return real_source(*args)
        def worker():
            close_old_connections()
            try:
                outcome.append(alterar(case, self.user, payload))
            except Exception as error:
                outcome.append(error)
            finally:
                close_old_connections()
        with patch.object(service, '_source', side_effect=hold_source):
            thread = Thread(target=worker); thread.start()
            try:
                self.assertTrue(entered.wait(10))
                second = {**payload, 'client_id':str(uuid4())}
                with self.assertRaises(FichaAlterada):
                    alterar(case, self.user, second)
            finally:
                release.set(); thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(outcome), 1)
        self.assertIsInstance(outcome[0], tuple, outcome)
        self.assertEqual(RevisaoDadoAtendimento.objects.filter(objeto_id=result['objeto_id']).count(), 1)
        with self.assertRaises(FichaAlterada):
            alterar(case, self.user, {**payload, 'client_id':str(uuid4())})


class MigracaoFichaTests(TransactionTestCase):
    def test_old_ambiguous_text_keeps_ids_values_versions_sources_and_confirmation(self):
        before = [('processos', '0013_feedbacktesteatendimento')]
        after = [('processos', '0024_mensagematendimento_correcao_de_and_more')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            state = executor.loader.project_state(before).apps
            user = state.get_model('auth','User').objects.create(username='migracao_ficticia')
            tenant = state.get_model('tenancy','Tenant').objects.create(nome='CARTÓRIO FICTÍCIO MIGRAÇÃO',uf='RJ')
            case = state.get_model('processos','Atendimento').objects.create(tenant_id=tenant.id, criado_por_id=user.id, titulo='LEGADO FICTÍCIO')
            message = state.get_model('processos','MensagemAtendimento').objects.create(tenant_id=tenant.id, atendimento_id=case.id,
                autor_id=user.id, client_id=uuid4(), texto='FONTE LEGADA FICTÍCIA')
            old = state.get_model('processos','RevisaoDadoAtendimento').objects.create(tenant_id=tenant.id, atendimento_id=case.id,
                autor_id=user.id, mensagem_id=message.id, chave='vendedores',valor='PESSOA ALFA / PESSOA BETA: vínculo desconhecido',situacao='confirmado',justificativa='CONFIRMAÇÃO ANTIGA',versao=3)
            from apps.processos.redacao import BASE
            from apps.processos.conferencia import assinatura
            model = state.get_model('processos','ModeloAtendimento').objects.create(tenant_id=tenant.id, atendimento_id=case.id,
                autor_id=user.id, versao=1, aprovado=True, justificativa='MODELO FICTÍCIO ANTIGO', **BASE)
            # Fingerprint contract used by the pre-structured-sheet application.
            old_hash = assinatura({'modelo':str(model.id), 'dados':{'vendedores':{
                'valor':old.valor, 'revisao_id':str(old.id), 'versao':3, 'situacao':'confirmado',
                'origem':{'tipo':'mensagem', 'mensagem_id':str(message.id), 'trecho':message.texto}}},
                'anexos':[], 'mensagens':[message.id], 'decisoes':[]})
            draft = state.get_model('processos','MinutaAtendimento').objects.create(tenant_id=tenant.id, atendimento_id=case.id,
                autor_id=user.id, modelo_id=model.id, versao=1, corpo='MINUTA LEGADA FICTÍCIA', dados={}, assinatura=old_hash)
            original_date = old.created_at
            executor = MigrationExecutor(connection); executor.migrate(after)
            revised = RevisaoDadoAtendimento.objects.get(pk=old.id)
            self.assertEqual(revised.valor, old.valor)
            self.assertEqual(revised.valor_original, old.valor)
            self.assertEqual(revised.versao, 3)
            self.assertEqual(revised.situacao, 'confirmado')
            self.assertEqual(revised.created_at, original_date)
            self.assertEqual(revised.mensagem_id, message.id)
            self.assertIsNone(revised.objeto_id)
            self.assertEqual(ObjetoFichaAtendimento.objects.filter(atendimento_id=case.id,tipo='legado').count(), 1)
            self.assertFalse(ObjetoFichaAtendimento.objects.filter(atendimento_id=case.id,tipo='pessoa').exists())
            from apps.processos.redacao import snapshot
            from apps.processos.models import MinutaAtendimento
            self.assertEqual(snapshot(Atendimento.objects.get(pk=case.id))[2], old_hash)
            self.assertEqual(MinutaAtendimento.objects.get(pk=draft.id).corpo, 'MINUTA LEGADA FICTÍCIA')
        finally:
            MigrationExecutor(connection).migrate(after)
