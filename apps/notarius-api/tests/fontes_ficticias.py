"""Explicit simulated classification decisions, used only in regression fixtures."""
from uuid import uuid4
from apps.processos.models import PaginaAnexoAtendimento, ObjetoFichaAtendimento
from apps.processos.organizacao_anexos import destinos


def organizar(test, case, pagina_id, objeto_id=None):
    page = PaginaAnexoAtendimento.objects.select_related('anexo__organizacao_atual').get(pk=pagina_id)
    file = page.anexo
    if str(file.atendimento_id) != str(case):
        return 0
    if not file.organizacao_atual_id:
        obj = ObjetoFichaAtendimento.objects.get(pk=objeto_id) if objeto_id else None
        response = test.client.post(f'/api/v1/atendimentos/{case}/anexos/{file.id}/organizacao/', {
            'client_id': str(uuid4()), 'versao_esperada': 0, 'leitura_versao': file.leitura_versao,
            'finalidade': 'caso', 'tipo_documento': 'Fonte FICTÍCIA de teste',
            'vinculos': [{'objeto_id': oid, 'paginas': []} for oid in sorted(destinos(obj), key=str)],
            'motivo': 'CLASSIFICAÇÃO HUMANA SIMULADA NO BANCO DE TESTE', 'conferi': True,
        }, format='json')
        test.assertEqual(response.status_code, 201, response.data)
        file.refresh_from_db()
    return file.organizacao_atual.versao


def preparar_campos(test, case, payload):
    for field in payload.get('campos', []):
        if field.get('pagina_id') and 'organizacao_versao' not in field:
            field['organizacao_versao'] = organizar(test, case, field['pagina_id'], payload.get('objeto_id'))
