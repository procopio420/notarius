"""Deterministic task routing and append-only conversation corrections. No provider."""
from uuid import uuid4
from django.db import transaction, OperationalError, connection
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import MensagemAtendimento, Atendimento
from .conferencia import conferir, assinatura
from .ficha_estruturada import reservar_atendimento, FichaAlterada


def mensagem_atual(message):
    return not MensagemAtendimento.objects.filter(correcao_de_id=message.id).exists()


class CorrecaoSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    texto = serializers.CharField(max_length=10000, trim_whitespace=False)
    justificativa = serializers.CharField(max_length=2000)

    def validate_texto(self, value):
        if not value.strip():
            raise ValidationError('Informe o texto corrigido.')
        return value


def corrigir(atendimento, user, message_id, payload):
    s = CorrecaoSerializer(data=payload); s.is_valid(raise_exception=True); data = s.validated_data
    digest = assinatura(['correcao_mensagem_v1', str(message_id), data])
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            old = get_object_or_404(atendimento.mensagens, id=message_id, tenant_id=atendimento.tenant_id)
            previous = atendimento.mensagens.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador de envio já utilizado com outro conteúdo ou autora.')
                return previous, False
            if not mensagem_atual(old):
                raise FichaAlterada('Esta resposta já foi corrigida. Abra a última mensagem da cadeia antes de corrigir novamente.')
            message = MensagemAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                autor=user, client_id=data['client_id'], texto=data['texto'], correcao_de=old,
                motivo_correcao=data['justificativa'], requisicao_hash=digest)
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, user, 'Correção expressa da conversa: ' + data['justificativa'])
            Atendimento.objects.filter(id=atendimento.id).update(updated_at=timezone.now())
            return message, True
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada() from None
        raise


def roteiro(atendimento):
    report = conferir(atendimento)
    from .rotulos_ficha import rotulos
    labels = rotulos(atendimento)
    objects = {str(o.id): o.tipo for o in atendimento.objetos_ficha.exclude(tipo='legado')}
    for q in report['pendencias']:
        target = q.get('destino', {})
        if target.get('objeto_id') in labels:
            target['registro_rotulo'] = labels[target['objeto_id']]
            q['rotulo'] += ' · ' + labels[target['objeto_id']]
        if target.get('subtipo') == 'registro_vazio' and objects.get(target.get('objeto_id')) == 'pessoa':
            target['campo'] = 'nome'
    priorities = {'organizacao_documento': 0, 'anexar': 1, 'documento': 2, 'pendencia_ficha': 3,
                  'mensagem': 4, 'leitura': 2, 'divergencia': 3, 'confirmacao': 5,
                  'estrutura': 6, 'vinculacao_minuta': 8}
    kinds = {'arquivo_sem_leitura': 0, 'pagina': 1, 'proposta': 2, 'registro_vazio': 3,
             'leitura': 4, 'vinculo_inativo': 4, 'ausencia': 5, 'confirmacao': 5,
             'comparacao_fontes': 6, 'trecho': 7, 'analise_documental': 7}
    pending = sorted(report['pendencias'], key=lambda q: (priorities.get(q['tipo'], 7),
        kinds.get(q.get('destino', {}).get('subtipo'), 5), q['chave']))
    files = list(atendimento.anexos.defer('conteudo').select_related('organizacao_atual'))
    proposals = atendimento.propostas_dados.count()
    return {'modo': 'orientacao_local_sem_ia', 'recebido': {
        'mensagens': atendimento.mensagens.count(), 'documentos': len(files), 'propostas': proposals,
        'pessoas': atendimento.objetos_ficha.filter(tipo='pessoa').count(),
        'imoveis': atendimento.objetos_ficha.filter(tipo='imovel').count(),
        'arquivos': [{'id': str(f.id), 'nome': f.nome, 'leitura_versao': f.leitura_versao,
                     'situacao_leitura': f.situacao,
                     'finalidade': f.organizacao_atual.finalidade if f.organizacao_atual_id else 'pendente'} for f in files]},
        'pendencias': pending, 'total_pendencias': len(pending), 'proxima': pending[0] if pending else None,
        'bloqueado': report['bloqueado'], 'pode_redigir': report['pode_redigir'],
        'mensagem': report['mensagem'], 'limite': report['limite'],
        'aviso': 'Roteiro local com todas as pendências atuais, sem IA real. Receber mensagem, documento ou proposta não confirma dados. Somente a escrevente decide.',
        'orientacao': report['orientacao']}
