"""Two fictional review fixtures; never professional approval or case evidence."""
from uuid import uuid4, uuid5, NAMESPACE_URL
from django.db import transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from .models import Atendimento, EventoFichaAtendimento
from .conferencia import normalizar, assinatura
from .ficha_estruturada import alterar

VERSAO = 'comparacao-compra-venda-ficticia-v1'
AVISO = 'CENÁRIO FICTÍCIO PARA REVISÃO. Não é documento autêntico, modelo homologado ou resposta de IA real.'


def especificacao(variante):
    if variante not in ['direta', 'procuracao']:
        raise ValidationError('Escolha direta ou procuracao.')
    pessoa = lambda nome, ref: {'nome': nome, 'cpf': f'CPF-FICTICIO-{ref}-INVALIDO',
        'documento_numero': f'ID-FICTICIO-{ref}', 'orgao_emissor': 'EMISSOR FICTÍCIO SEM VALIDADE',
        'nacionalidade': 'NACIONALIDADE FICTÍCIA', 'profissao': 'PROFISSÃO FICTÍCIA',
        'estado_civil': 'solteiro — DADO EXCLUSIVAMENTE FICTÍCIO', 'endereco': f'ENDEREÇO INEXISTENTE {ref}'}
    nodes = [
        {'alias': 'vendedor', 'tipo': 'pessoa', 'campos': pessoa('PESSOA VENDEDORA FICTÍCIA ALFA', 'ALFA')},
        {'alias': 'comprador', 'tipo': 'pessoa', 'campos': pessoa('PESSOA COMPRADORA FICTÍCIA BETA', 'BETA')},
        {'alias': 'bem', 'tipo': 'imovel', 'campos': {'descricao': 'IMÓVEL INEXISTENTE — UNIDADE DE TESTE',
            'matricula': 'MATRICULA-FICTICIA-SEM-VALIDADE', 'registro': 'REGISTRO FICTÍCIO',
            'titularidade': 'TITULARIDADE FICTÍCIA ALFA — APENAS CENÁRIO', 'aquisicao': 'TÍTULO FICTÍCIO SEM VALIDADE',
            'onus': 'TEXTO FICTÍCIO PARA TESTAR CONFERÊNCIA DE ÔNUS; NÃO É CERTIDÃO'}},
        {'alias': 'papel_vendedor', 'tipo': 'papel', 'vinculos': {'pessoa_a': 'vendedor'}, 'campos': {'tipo_papel': 'vendedor'}},
        {'alias': 'papel_comprador', 'tipo': 'papel', 'vinculos': {'pessoa_a': 'comprador'}, 'campos': {'tipo_papel': 'comprador'}},
        {'alias': 'negocio', 'tipo': 'negociacao', 'vinculos': {'imovel': 'bem'}, 'campos': {'preco': 'R$ 200.000,00 — VALOR FICTÍCIO'}},
    ]
    if variante == 'procuracao':
        nodes.insert(2, {'alias': 'procurador', 'tipo': 'pessoa', 'campos': pessoa('PESSOA PROCURADORA FICTÍCIA GAMA', 'GAMA')})
        nodes.append({'alias': 'representacao', 'tipo': 'relacao', 'vinculos': {'pessoa_a': 'procurador', 'pessoa_b': 'vendedor'},
            'campos': {'tipo_relacao': 'representante_de', 'instrumento': 'INSTRUMENTO-FICTICIO-PROC-001 — SEM VALIDADE',
                       'descricao': 'DESCRIÇÃO FICTÍCIA DE REPRESENTAÇÃO; NÃO ATESTA PODERES, SUFICIÊNCIA OU VALIDADE'}})
    def qualify(alias):
        return ', '.join('{{' + alias + '.' + k + '}}' for k in ['nome', 'cpf', 'documento_numero', 'orgao_emissor', 'nacionalidade', 'profissao', 'estado_civil', 'endereco'])
    text = 'RASCUNHO FICTÍCIO DE COMPRA E VENDA — PARA HOMOLOGAÇÃO\nSEM VALIDADE PROFISSIONAL\n\nQUALIFICAÇÃO INFORMADA DO VENDEDOR\n' + qualify('vendedor')
    text += '\nPapel informado: {{papel_vendedor.tipo_papel}}\n\nQUALIFICAÇÃO INFORMADA DO COMPRADOR\n' + qualify('comprador')
    text += '\nPapel informado: {{papel_comprador.tipo_papel}}'
    if variante == 'procuracao':
        text += '\n\nREPRESENTAÇÃO INFORMADA\nPessoa indicada como representante: ' + qualify('procurador')
        text += '\nRelação informada: {{representacao.tipo_relacao}}\nInstrumento indicado: {{representacao.instrumento}}\nLimites informados: {{representacao.descricao}}'
    text += '''

1.- DO IMÓVEL E SUA TITULAÇÃO
{{bem.descricao}}
Referência: {{bem.matricula}} · {{bem.registro}}
Titularidade informada: {{bem.titularidade}}
Aquisição informada: {{bem.aquisicao}}
Ônus informados: {{bem.onus}}

2.- CONDIÇÕES INFORMADAS DO NEGÓCIO
Preço: {{negocio.preco}}
Condições: {{negocio.condicoes}}
Situação informada: {{negocio.situacao_pagamento}}'''
    model = {'corpo': text, 'representacao': '', 'observacoes': '', 'aprovado': False,
        'justificativa': 'Preparação automática de material FICTÍCIO, pendente de revisão profissional.',
        'registros_minuta': [{'chave': n['alias'], 'rotulo': n['alias'].replace('_', ' ').capitalize(),
                             'tipo': n['tipo'], 'vinculos': n.get('vinculos', {})} for n in nodes]}
    return {'versao': VERSAO, 'variante': variante, 'aviso': AVISO, 'registros': nodes, 'modelo': model,
            'mensagem': 'Condições de pagamento: PREVISÃO FICTÍCIA DE PAGAMENTO FUTURO\nSituação do pagamento: previsto',
            'campos_mensagem': {'condicoes': 'PREVISÃO FICTÍCIA DE PAGAMENTO FUTURO', 'situacao_pagamento': 'previsto'}}


def arquivos(spec):
    return {f"FICTICIO-{node['alias']}.txt": AVISO + '\n' + '\n'.join(f"{key.replace('_', ' ')}: {value}" for key, value in node['campos'].items()) for node in spec['registros']}


def preparar(tenant, user, variante):
    """Idempotent, atomic fixture creation; never save field/model confirmations."""
    if 'fict' not in normalizar(tenant.nome) or not getattr(user, 'profile', None) or not user.profile.can_access_tenant(tenant):
        raise ValidationError('Use somente cartório identificado como fictício e usuária com acesso a ele.')
    spec = especificacao(variante)
    case_id = uuid5(NAMESPACE_URL, f'notarius:{VERSAO}:{tenant.id}:{variante}')
    event_id = uuid5(case_id, 'preparacao')
    with transaction.atomic():
        existing = Atendimento.objects.filter(id=case_id).first()
        if existing:
            event = existing.eventos_ficha.filter(client_id=event_id, tenant=tenant, requisicao_hash=assinatura(spec)).first()
            if not event or existing.tenant_id != tenant.id:
                raise ValidationError('Identificador ocupado por outro registro. Nada foi substituído.')
            return event.resultado, False
        case = Atendimento.objects.create(id=case_id, tenant=tenant, criado_por=user,
            titulo=f'TESTE FICTÍCIO — homologação comparativa: {"participação direta" if variante == "direta" else "com procuração"}')
        client = APIClient(HTTP_HOST='localhost'); client.force_authenticate(user)
        client.credentials(HTTP_X_TENANT_ID=str(tenant.id))
        def post(path, data, fmt='json'):
            response = client.post(f'/api/v1/atendimentos/{case.id}/{path}/', data, format=fmt)
            if response.status_code not in [200, 201]:
                raise ValidationError({'preparacao_ficticia': response.data})
            return response.data
        model = post('modelo-minuta', {**spec['modelo'], 'versao_esperada': 0})
        ids = {}
        for n in spec['registros']:
            ids[n['alias']] = alterar(case, user, {'client_id': str(uuid4()), 'modelo_id': model['id'],
                'operacao': 'criar', 'tipo': n['tipo'], 'justificativa': 'Registro FICTÍCIO proposto para revisão, sem confirmação de dados.',
                **{f'{link}_id': ids[alias] for link, alias in n.get('vinculos', {}).items()}})[0]['objeto_id']
        expected = []
        for n in spec['registros']:
            name = f"FICTICIO-{n['alias']}.txt"
            upload = post('anexos', {'arquivo': SimpleUploadedFile(name, arquivos(spec)[name].encode('utf-8'))}, 'multipart')
            post('propostas-dados', {'operacao': 'extrair', 'anexo_id': upload['id'], 'leitura_versao': 1, 'client_id': str(uuid4())})
            for p in case.propostas_dados.filter(pagina__anexo_id=upload['id']):
                key = next(key for key in n['campos'] if key.replace('_', ' ') == p.rotulo)
                expected.append({'proposta_id': str(p.id), 'alias': n['alias'], 'objeto_id': ids[n['alias']], 'chave': key,
                                 'valor_revisado_ficticio': n['campos'][key]})
        message = post('mensagens', {'texto': spec['mensagem'], 'client_id': str(uuid4())})
        post('propostas-dados', {'operacao': 'extrair', 'mensagem_id': message['id'], 'client_id': str(uuid4())})
        for p in case.propostas_dados.filter(mensagem_id=message['id']):
            key = 'situacao_pagamento' if normalizar(p.rotulo) == 'situacao do pagamento' else 'condicoes'
            expected.append({'proposta_id': str(p.id), 'alias': 'negocio', 'objeto_id': ids['negocio'], 'chave': key,
                             'valor_revisado_ficticio': spec['campos_mensagem'][key]})
        result = {'versao': VERSAO, 'variante': variante, 'atendimento_id': str(case.id), 'modelo_id': model['id'],
                  'aviso': AVISO, 'modelo_aprovado': False, 'registros': ids, 'resultado_esperado_proposto': expected}
        EventoFichaAtendimento.objects.create(atendimento=case, tenant=tenant, autor=user, client_id=event_id,
            requisicao_hash=assinatura(spec), resultado=result)
        return result, True
