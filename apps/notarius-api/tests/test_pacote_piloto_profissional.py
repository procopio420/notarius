"""Exercise the delivered draft package; all case information is fictional."""
import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.processos.ficha import CAMPOS, TOKEN
from apps.processos.models import ModeloAtendimento, MinutaAtendimento
from apps.processos.redacao import validar_modelo, validar_fatos_fixos
from apps.processos.serializers import SalvarModeloSerializer
from tests import test_atendimentos as helpers


def pacote():
    path = Path(__file__).resolve().parents[3] / 'docs/piloto-profissional/modelo-v1.json'
    return json.loads(path.read_text(encoding='utf-8'))


class ContratoPacotePilotoTests(SimpleTestCase):
    def test_delivered_package_passes_real_validators_without_professional_defaults(self):
        package = pacote()
        serializer = SalvarModeloSerializer(data=package['modelo'])
        serializer.is_valid(raise_exception=True)
        model = serializer.validated_data
        validar_modelo(model)
        validar_fatos_fixos(SimpleNamespace(**model))
        self.assertFalse(package['aprovado'])
        self.assertFalse(model['aprovado'])
        for key in ('registros_minuta', 'campos_obrigatorios_ficha', 'dependencias_campos_ficha'):
            self.assertEqual(model[key], [])
        text = '\n'.join(model[key] for key in ('corpo', 'representacao', 'observacoes'))
        self.assertEqual(set(TOKEN.findall(text)), set(CAMPOS))

    def test_fixed_quittance_cannot_be_smuggled_into_delivered_model(self):
        model = pacote()['modelo']
        model['corpo'] += '\nO preço foi pago e os vendedores dão quitação.'
        with self.assertRaises(ValidationError):
            validar_fatos_fixos(SimpleNamespace(**model))


class PercursoPacotePilotoTests(APITestCase):
    setUp = helpers.AtendimentoTests.setUp
    create_case = helpers.AtendimentoTests.create_case
    ready_for_draft = helpers.AtendimentoTests.ready_for_draft
    report = helpers.AtendimentoTests.report
    answer = helpers.AtendimentoTests.answer
    generate_draft = helpers.AtendimentoTests.generate_draft

    def save_package(self, case):
        response = self.client.post(
            f'/api/v1/atendimentos/{case}/modelo-minuta/', pacote()['modelo'], format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_save_and_reopen_delivered_package_preserves_draft_without_case_facts(self):
        case = self.create_case()
        saved = self.save_package(case)
        reopened = self.client.get(f'/api/v1/atendimentos/{case}/modelo-minuta/')
        self.assertEqual(reopened.status_code, 200)
        current = reopened.data['versoes'][0]
        self.assertEqual(current['id'], saved.data['id'])
        self.assertEqual(current['corpo'], pacote()['modelo']['corpo'])
        self.assertFalse(current['aprovado'])
        self.assertFalse(ModeloAtendimento.objects.get(pk=current['id']).aprovado)
        self.assertFalse(MinutaAtendimento.objects.exists())

    def test_even_fictionally_completed_fields_do_not_approve_delivered_package(self):
        case = self.ready_for_draft()
        self.save_package(case)
        for block in ('corpo', 'representacao', 'observacoes'):
            for key in TOKEN.findall(pacote()['modelo'][block]):
                if any(q['chave'] == key for q in self.report(case)['pendencias']):
                    response, _ = self.answer(case, key, f'TEXTO INTEIRAMENTE FICTÍCIO PARA {key}')
                    self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(self.report(case)['bloqueado'])
        self.assertEqual(self.generate_draft(case).status_code, 400)
        self.assertFalse(MinutaAtendimento.objects.exists())
        self.assertFalse(ModeloAtendimento.objects.filter(aprovado=True).exists())
