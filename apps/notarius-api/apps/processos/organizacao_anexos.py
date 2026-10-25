"""Human document classification and explicit, page-scoped owners. No name inference."""
from django.db import transaction, OperationalError, connection
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import OrganizacaoAnexoAtendimento, AnexoAtendimento
from .conferencia import assinatura


def atual(file):
    return file.organizacao_atual


def versao(file):
    return file.organizacao_atual.versao if file.organizacao_atual_id else 0


def destinos(objeto):
    if not objeto:
        return {None}
    if objeto.tipo in ['pessoa', 'imovel']:
        return {str(objeto.id)}
    related = {str(i) for i in [objeto.pessoa_a_id, objeto.pessoa_b_id, objeto.imovel_id] if i}
    return related or {None}


def permite(file, objeto=None, pagina=None):
    org = atual(file)
    if not org or org.finalidade != 'caso' or not org.tipo_documento or org.leitura_versao != file.leitura_versao:
        return False
    owners = {v['objeto_id'] for v in org.vinculos if not v['paginas'] or pagina in v['paginas']}
    return destinos(objeto).issubset(owners)


def validar_fonte(file, objeto, pagina, expected, confirmar=True):
    from .ficha_estruturada import FichaAlterada
    org = atual(file)
    if expected != versao(file):
        raise FichaAlterada('A classificação ou os destinatários do documento mudaram. Reabra a fonte e confira antes de salvar.')
    if org and org.finalidade in ['referencia_redacao', 'nao_utilizar']:
        raise ValidationError('Este arquivo não é fonte comprobatória do caso. Referência de redação ou arquivo desconsiderado não pode fornecer dados à ficha.')
    if confirmar and not permite(file, objeto, pagina):
        raise ValidationError('Classifique o documento como fonte do caso e confirme seus destinatários/páginas antes de confirmar este dado.')
    return org


def fonte_valida(revision):
    source = revision.revisao_origem if revision.revisao_origem_id else revision
    if not source.pagina_origem_id:
        return True
    page = source.pagina_origem
    source_org = revision.organizacao_origem_id or source.organizacao_origem_id
    return bool(source_org and source_org == page.anexo.organizacao_atual_id
                and permite(page.anexo, revision.objeto if revision.objeto_id else None, page.numero))


def resumo(file):
    org = atual(file)
    return {'id': str(org.id) if org else None, 'versao': org.versao if org else 0,
            'finalidade': org.finalidade if org else 'pendente', 'tipo_documento': org.tipo_documento if org else '',
            'vinculos': org.vinculos if org else [], 'leitura_versao': org.leitura_versao if org else None,
            'autor': org.autor.get_full_name() or org.autor.username if org else None,
            'data': org.created_at.isoformat() if org else None, 'motivo': org.motivo if org else '',
            'leitura_atual': bool(org and org.leitura_versao == file.leitura_versao)}


def pendencias(atendimento):
    result = []
    for file in atendimento.anexos.select_related('organizacao_atual').defer('conteudo'):
        org = atual(file)
        if org and org.finalidade in ['referencia_redacao', 'nao_utilizar']:
            continue
        if not org or org.finalidade != 'caso' or not org.tipo_documento or not org.vinculos or org.leitura_versao != file.leitura_versao:
            result.append({'chave': f'organizacao:{file.id}', 'tipo': 'organizacao_documento', 'rotulo': file.nome,
                'pergunta': 'Confira a finalidade, o tipo e a quem pertence este documento, inclusive as páginas e a versão de leitura. Nomes parecidos não comprovam vínculo.',
                'assinatura': assinatura([str(file.id), str(file.organizacao_atual_id), file.leitura_versao]),
                'versao': org.versao if org else 0, 'candidatos': [], 'atual': None})
    return result


class VinculoSerializer(serializers.Serializer):
    objeto_id = serializers.UUIDField(allow_null=True)
    paginas = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=100, allow_empty=True)


class PedidoSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    versao_esperada = serializers.IntegerField(min_value=0)
    leitura_versao = serializers.IntegerField(min_value=1)
    finalidade = serializers.ChoiceField(choices=['pendente', 'caso', 'referencia_redacao', 'nao_utilizar'])
    tipo_documento = serializers.CharField(max_length=120, allow_blank=True)
    vinculos = VinculoSerializer(many=True, max_length=100)
    motivo = serializers.CharField(max_length=2000)
    conferi = serializers.BooleanField()


def salvar(atendimento, file, user, payload):
    from .ficha_estruturada import reservar_atendimento, FichaAlterada
    s = PedidoSerializer(data=payload); s.is_valid(raise_exception=True); data = s.validated_data
    digest = assinatura(data)
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            previous = atendimento.organizacoes_anexos.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != user.id or previous.anexo_id != file.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador de decisão já usado com outro arquivo, conteúdo ou autora.')
                return {'id': str(previous.id), 'versao': previous.versao}, False
            file = get_object_or_404(atendimento.anexos.select_related('organizacao_atual'), id=file.id)
            if data['versao_esperada'] != versao(file) or data['leitura_versao'] != file.leitura_versao:
                raise FichaAlterada('O documento, sua classificação ou leitura mudou. Atualize antes de decidir.')
            if not data['conferi']:
                raise ValidationError('Confira explicitamente a classificação e os destinatários; isso não confirma os dados nem autentica o documento.')
            if data['finalidade'] == 'caso' and (not data['tipo_documento'] or not data['vinculos']):
                raise ValidationError('Informe o tipo e os destinatários explícitos, inclusive atendimento geral quando aplicável.')
            if data['finalidade'] != 'caso' and data['vinculos']:
                raise ValidationError('Somente documento do caso pode ter vínculos comprobatórios. Mantenha dúvidas como pendentes.')
            total = file.metadados_leitura.get('total_paginas')
            if total is None:
                total = file.paginas.filter(leitura_versao=file.leitura_versao).order_by('-numero').values_list('numero', flat=True).first()
            links = []; seen = set()
            for link in data['vinculos']:
                oid = link['objeto_id']
                if oid:
                    get_object_or_404(atendimento.objetos_ficha, id=oid, tenant_id=atendimento.tenant_id, tipo__in=['pessoa', 'imovel'])
                pages = sorted(set(link['paginas']))
                if pages and (total is None or max(pages) > total):
                    raise ValidationError('Página não identificada nesta leitura. Confira o original; não invente paginação.')
                key = (str(oid) if oid else None, tuple(pages))
                if key in seen:
                    raise ValidationError('Não repita o mesmo vínculo e suas páginas.')
                seen.add(key); links.append({'objeto_id': str(oid) if oid else None, 'paginas': pages})
            org = OrganizacaoAnexoAtendimento.objects.create(atendimento=atendimento, anexo=file, tenant=atendimento.tenant,
                autor=user, versao=versao(file) + 1, client_id=data['client_id'], requisicao_hash=digest,
                finalidade=data['finalidade'], tipo_documento=data['tipo_documento'], vinculos=links,
                leitura_versao=file.leitura_versao, motivo=data['motivo'])
            AnexoAtendimento.objects.filter(pk=file.id).update(organizacao_atual=org)
            type(atendimento).objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, user, data['motivo'])
            return {'id': str(org.id), 'versao': org.versao}, True
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada() from None
        raise
