import uuid
from django_filters import rest_framework as df_filters
from rest_framework import filters
from rest_framework import mixins, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.base.views import BaseTenantViewSet

from .models import Processo, ProcessoParte, Protocolo, Atendimento, MensagemAtendimento
from .serializers import AtendimentoSerializer, MensagemAtendimentoSerializer
from .serializers import ProcessoParteSerializer, ProcessoSerializer, ProtocoloSerializer
from .models import RevisaoDadoAtendimento
from .serializers import RevisaoDadoSerializer, AtualizarDadoSerializer
from .ficha import CAMPOS, campos_ativos
from .models import AnexoAtendimento, PaginaAnexoAtendimento
from .serializers import AnexoAtendimentoSerializer
from .leitura_anexos import extrair_pdf, MAX_BYTES
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from django.utils.http import content_disposition_header
import hashlib
from pathlib import Path
from .conferencia import conferir, assinatura, sem_dado
from .models import DecisaoConferencia
from .serializers import RespostaConferenciaSerializer
from .models import ModeloAtendimento, MinutaAtendimento
from .serializers import SalvarModeloSerializer, ModeloMinutaSerializer
from .redacao import BASE, validar_modelo, snapshot, preparar
from .serializers import EditarMinutaSerializer


class AtendimentoViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AtendimentoSerializer
    pagination_class = None

    @action(detail=True, methods=['get'], url_path='roteiro-conversa')
    def roteiro_conversa(self, request, pk=None):
        from .conversa_orientada import roteiro
        response = Response(roteiro(self.get_object()))
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['post'], url_path=r'mensagens/(?P<mensagem_id>[0-9a-f-]+)/corrigir')
    def corrigir_mensagem(self, request, pk=None, mensagem_id=None):
        from .conversa_orientada import corrigir
        result, created = corrigir(self.get_object(), request.user, mensagem_id, request.data)
        return Response(MensagemAtendimentoSerializer(result).data, status=201 if created else 200)

    @action(detail=True, methods=['get'], url_path='comparacao-fontes')
    def comparacao_fontes(self, request, pk=None):
        from .comparacao_fontes import comparar
        response = Response(comparar(self.get_object()))
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='analise-documental')
    def analise_documental(self, request, pk=None):
        from .analise_documental import executar
        from .provedor_documental import ProvedorIndisponivel, RespostaInvalida
        case = self.get_object()
        if request.method == 'GET':
            from .politica_documental import diagnostico
            response = Response({'preparacao': diagnostico(), 'contrato': 'documental_v1', 'disponivel': False, 'provedor': 'real_bloqueado',
                'aviso': 'Análise documental por IA bloqueada nesta fase. Simulação exclusiva de testes; sem fallback automático.',
                'analises': [{'id': str(a.id), 'provedor': a.provedor, 'data': a.created_at,
                             'contexto_assinatura': a.contexto_assinatura, 'entrada': a.entrada, 'saida': a.saida}
                            for a in case.analises_documentais.all()]})
        else:
            try:
                result, created = executar(case, request.user, request.data)
                response = Response(result, status=201 if created else 200)
            except ProvedorIndisponivel as error:
                response = Response({'codigo': error.codigo, 'detail': str(error), 'aplicado': False}, status=503)
            except RespostaInvalida as error:
                response = Response({'codigo': 'resposta_documental_invalida', 'detail': str(error), 'aplicado': False}, status=422)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path=r'anexos/(?P<anexo_id>[0-9a-f-]+)/organizacao')
    def organizacao_anexo(self, request, pk=None, anexo_id=None):
        from django.shortcuts import get_object_or_404
        from .organizacao_anexos import salvar, resumo
        atendimento = self.get_object()
        file = get_object_or_404(atendimento.anexos.select_related('organizacao_atual'), id=anexo_id)
        if request.method == 'POST':
            result, created = salvar(atendimento, file, request.user, request.data)
            response = Response(result, status=201 if created else 200)
        else:
            response = Response({'atual': resumo(file), 'historico': [{'id': str(o.id), 'versao': o.versao,
                'finalidade': o.finalidade, 'tipo_documento': o.tipo_documento, 'vinculos': o.vinculos,
                'leitura_versao': o.leitura_versao, 'motivo': o.motivo, 'data': o.created_at.isoformat(),
                'autor': o.autor.get_full_name() or o.autor.username} for o in file.organizacoes.select_related('autor')]})
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='vinculacao-minuta')
    def vinculacao_minuta(self, request, pk=None):
        from .redacao_estruturada import consultar, salvar
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response(consultar(atendimento))
        else:
            result, created = salvar(atendimento, request.user, request.data)
            response = Response(result, status=201 if created else 200)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='propostas-dados')
    def propostas_dados(self, request, pk=None):
        from .propostas_dados import consultar_propostas, registrar
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response({'propostas': consultar_propostas(atendimento)})
        else:
            result, created = registrar(atendimento, request.user, request.data)
            response = Response(result, status=201 if created else 200)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get'], url_path=r'propostas-dados/(?P<proposta_id>[0-9a-f-]+)/fonte')
    def fonte_proposta(self, request, pk=None, proposta_id=None):
        from django.shortcuts import get_object_or_404
        from .propostas_dados import serializar
        atendimento = self.get_object()
        proposal = get_object_or_404(atendimento.propostas_dados.select_related('pagina__anexo', 'mensagem'),
                                     pk=proposta_id, tenant_id=atendimento.tenant_id)
        info = serializar(proposal)
        text = ((proposal.pagina.texto_ocr if proposal.canal == 'ocr' else proposal.pagina.texto)
                if proposal.pagina_id else proposal.mensagem.texto)
        response = Response({'texto': text, 'trecho': proposal.trecho, 'origem': info['origem'], 'fonte_atual': info['fonte_atual']})
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='pendencias-ficha')
    def pendencias_ficha(self, request, pk=None):
        from .pendencias_ficha import consultar, executar
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response({'pendencias': consultar(atendimento)})
        else:
            result, created = executar(atendimento, request.user, request.data)
            response = Response(result, status=201 if created else 200)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='ficha-detalhada')
    def ficha_detalhada(self, request, pk=None):
        from .ficha_estruturada import consultar, alterar
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response(consultar(atendimento))
        else:
            result, created = alterar(atendimento, request.user, request.data)
            response = Response(result, status=201 if created else 200)
        response['Cache-Control'] = 'no-store'
        return response

    def tenant(self):
        from apps.base.views import get_tenant_for_request
        tenant = get_tenant_for_request(self.request)
        profile = getattr(self.request.user, 'profile', None)
        if not tenant or not profile or not profile.can_access_tenant(tenant):
            raise PermissionDenied('Você não tem acesso a este cartório.')
        return tenant

    def get_queryset(self):
        queryset = Atendimento.objects.filter(tenant=self.tenant())
        if self.action == 'list':
            search = self.request.query_params.get('busca', '').strip()
            state = self.request.query_params.get('situacao', '')
            if len(search) > 160 or state and state not in ['em_andamento', 'aguardando', 'pausado']:
                raise ValidationError('Filtro de atendimento inválido.')
            if search:
                queryset = queryset.filter(titulo__icontains=search)
            if state:
                queryset = queryset.filter(situacao=state)
        return queryset

    @action(detail=True, methods=['get', 'post'])
    def organizacao(self, request, pk=None):
        from rest_framework import serializers
        from .models import HistoricoOrganizacaoAtendimento
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response({'historico':[
                {'versao':event.versao, 'titulo_anterior':event.titulo_anterior, 'titulo_novo':event.titulo_novo,
                 'situacao_anterior':event.situacao_anterior, 'situacao_nova':event.situacao_nova,
                 'motivo':event.motivo, 'autor_nome':event.autor.get_full_name() or event.autor.username,
                 'created_at':event.created_at}
                for event in atendimento.historico_organizacao.select_related('autor').all()]})
            response['Cache-Control'] = 'no-store'
            return response
        title = serializers.CharField(max_length=160).run_validation(request.data.get('titulo'))
        state = serializers.ChoiceField(choices=['em_andamento', 'aguardando', 'pausado']).run_validation(request.data.get('situacao'))
        reason = serializers.CharField(max_length=2000).run_validation(request.data.get('motivo'))
        expected = serializers.IntegerField(min_value=1).run_validation(request.data.get('versao_esperada'))
        with transaction.atomic():
            atendimento = Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            if atendimento.versao_cadastro != expected:
                return Response({'detail':'A organização do atendimento mudou. Atualize antes de salvar.'}, status=409)
            if atendimento.titulo != title or atendimento.situacao != state:
                HistoricoOrganizacaoAtendimento.objects.create(tenant=atendimento.tenant, atendimento=atendimento,
                    autor=request.user, titulo_anterior=atendimento.titulo, titulo_novo=title,
                    situacao_anterior=atendimento.situacao, situacao_nova=state, motivo=reason,
                    versao=expected+1)
                atendimento.titulo = title
                atendimento.situacao = state
                atendimento.versao_cadastro += 1
                atendimento.save(update_fields=['titulo', 'situacao', 'versao_cadastro', 'updated_at'])
        return Response(AtendimentoSerializer(atendimento).data)

    def perform_create(self, serializer):
        serializer.save(tenant=self.tenant(), criado_por=self.request.user)

    @action(detail=True, methods=['get'])
    def conferencia(self, request, pk=None):
        return Response(conferir(self.get_object()))

    @action(detail=True, methods=['get', 'post'], url_path='feedbacks-teste')
    def feedbacks_teste(self, request, pk=None):
        from .models import FeedbackTesteAtendimento
        from .serializers import FeedbackTesteSerializer, CriarFeedbackTesteSerializer
        atendimento = self.get_object()
        if request.method == 'GET':
            response = Response(FeedbackTesteSerializer(atendimento.feedbacks_teste.select_related('autor').all(), many=True).data)
            response['Cache-Control'] = 'no-store'
            return response
        serializer = CriarFeedbackTesteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        digest = assinatura(data)
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            previous = atendimento.feedbacks_teste.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != request.user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador de feedback já utilizado.')
                return Response(FeedbackTesteSerializer(previous).data)
            model, _, fingerprint = snapshot(atendimento)
            latest = atendimento.minutas_preparadas.first()
            item = FeedbackTesteAtendimento.objects.create(tenant=atendimento.tenant, atendimento=atendimento,
                autor=request.user, requisicao_hash=digest, **data,
                contexto={'assinatura_dados':fingerprint, 'modelo_versao':model.versao if model else None,
                          'minuta_versao':latest.versao if latest else None,
                          'pendencias':len(conferir(atendimento)['pendencias'])})
        return Response(FeedbackTesteSerializer(item).data, status=201)

    @action(detail=True, methods=['get'], url_path='resumo-revisao')
    def resumo_revisao(self, request, pk=None):
        from .resumo_revisao import gerar_resumo, ResumoAlterado
        atendimento = self.get_object()
        try:
            with transaction.atomic():
                atendimento = Atendimento.objects.select_for_update().get(pk=atendimento.pk)
                data = gerar_resumo(atendimento)
        except ResumoAlterado:
            return Response({'detail':'Os registros mudaram durante a consulta. Atualize o resumo.'}, status=409)
        response = Response(data)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=False, methods=['get'], url_path='biblioteca-modelos')
    def biblioteca_modelos(self, request):
        from .models import ModeloReutilizavel
        search = request.query_params.get('busca', '')[:120].strip()
        items = ModeloReutilizavel.objects.filter(tenant=self.tenant())
        if search:
            items = items.filter(nome__icontains=search)
        rows = list(items.select_related('origem', 'autor')[:51])
        response = Response({'mais_resultados':len(rows) > 50, 'modelos':[
            {'id':str(item.id), 'nome':item.nome, 'corpo':item.corpo,
             'representacao':item.representacao, 'observacoes':item.observacoes, 'registros_minuta':item.registros_minuta, 'campos_qualificacao':item.campos_qualificacao, 'campos_obrigatorios_ficha':item.campos_obrigatorios_ficha, 'dependencias_campos_ficha':item.dependencias_campos_ficha,
             'origem_versao':item.origem.versao, 'created_at':item.created_at,
             'autor_nome':item.autor.get_full_name() or item.autor.username} for item in rows[:50]]})
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['post'], url_path='publicar-modelo')
    def publicar_modelo(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers
        from .models import ModeloReutilizavel
        atendimento = self.get_object()
        model_id = serializers.UUIDField().run_validation(request.data.get('modelo_id'))
        name = serializers.CharField(max_length=120).run_validation(request.data.get('nome'))
        if request.data.get('confirmar_sem_dados') is not True:
            raise ValidationError('Confira que o modelo contém apenas o padrão e marcadores, sem dados de pessoas ou negócios.')
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            model = get_object_or_404(atendimento.modelos_minuta, pk=model_id)
            if not model.aprovado or atendimento.modelos_minuta.first().id != model.id:
                return Response({'detail':'Publique somente a versão atual e aprovada do modelo.'}, status=409)
            validar_modelo({'corpo':model.corpo, 'representacao':model.representacao, 'observacoes':model.observacoes,
                            'registros_minuta':model.registros_minuta, 'campos_qualificacao':model.campos_qualificacao})
            item, created = ModeloReutilizavel.objects.get_or_create(tenant=atendimento.tenant, origem=model, nome=name,
                defaults={'autor':request.user, 'corpo':model.corpo, 'representacao':model.representacao,
                          'observacoes':model.observacoes, 'registros_minuta':model.registros_minuta, 'campos_qualificacao':model.campos_qualificacao, 'campos_obrigatorios_ficha':model.campos_obrigatorios_ficha, 'dependencias_campos_ficha':model.dependencias_campos_ficha})
        return Response({'id':str(item.id), 'nome':item.nome}, status=201 if created else 200)

    @action(detail=True, methods=['get', 'post'], url_path='modelo-minuta')
    def modelo_minuta(self, request, pk=None):
        atendimento = self.get_object()
        if request.method == 'GET':
            from .modelo_referencia import BASE_REFERENCIA, REFERENCIA
            from .modelo_complementar import referencia_complementar
            from .modelo_ficticio_estruturado import MODELO_FICTICIO_ETAPA7
            return Response({'base': BASE, 'referencia': {**REFERENCIA, 'modelo': BASE_REFERENCIA},
                'modelo_ficticio_estruturado': MODELO_FICTICIO_ETAPA7,
                'referencias_complementares': [referencia_complementar(v) for v in ['direta', 'procuracao']],
                'marcadores': [{'chave': key, 'rotulo': label} for key, (label, _) in CAMPOS.items()],
                'versoes': ModeloMinutaSerializer(atendimento.modelos_minuta.all(), many=True).data})
        serializer = SalvarModeloSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        validar_modelo(data)
        expected = data.pop('versao_esperada')
        reference_id = data.pop('referencia_id', None)
        reference = None
        if reference_id:
            from django.shortcuts import get_object_or_404
            from .models import ModeloReutilizavel
            reference = get_object_or_404(ModeloReutilizavel, pk=reference_id, tenant=atendimento.tenant)
        with transaction.atomic():
            from .ficha_estruturada import reservar_atendimento
            reservar_atendimento(atendimento)
            current = atendimento.modelos_minuta.first()
            version = current.versao if current else 0
            if expected != version:
                return Response({'detail': 'O modelo mudou. Atualize antes de salvar outra versão.'}, status=409)
            model = ModeloAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                autor=request.user, versao=version + 1, referencia=reference, **data)
            Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, request.user)
        return Response(ModeloMinutaSerializer(model).data, status=201)

    @action(detail=True, methods=['get', 'post'], url_path='minuta-preparada')
    def minuta_preparada(self, request, pk=None):
        atendimento = self.get_object()
        if request.method == 'POST':
            with transaction.atomic():
                from .ficha_estruturada import reservar_atendimento
                reservar_atendimento(atendimento)
                model, values, fingerprint = snapshot(atendimento)
                if request.data.get('assinatura_esperada') != fingerprint:
                    return Response({'detail': 'Os dados ou o modelo mudaram. Atualize antes de preparar a minuta.'}, status=409)
                model, values, fingerprint, text = preparar(atendimento)
                existing = atendimento.minutas_preparadas.filter(assinatura=fingerprint).first()
                if not existing:
                    previous = atendimento.minutas_preparadas.first()
                    MinutaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                        autor=request.user, modelo=model, versao=(previous.versao if previous else 0) + 1,
                        corpo=text, dados=values, assinatura=fingerprint)
        model, values, fingerprint = snapshot(atendimento)
        report = conferir(atendimento)
        ready = False
        blocked_reason = 'Resolva as pendências do atendimento.' if report['bloqueado'] else 'Revise e aprove a versão atual do modelo.'
        if not report['bloqueado'] and model and model.aprovado:
            try:
                preparar(atendimento)
                ready = True
                blocked_reason = ''
            except ValidationError as error:
                blocked_reason = ' '.join(str(item) for item in error.detail) if isinstance(error.detail, list) else str(error.detail)
        from .revisao_final import registro_final
        versions = [{'id': str(m.id), 'versao': m.versao, 'corpo': m.corpo, 'tipo': m.tipo,
                     'revisao_final': registro_final(m),
                     'motivo': m.motivo, 'autor_nome': m.autor.get_full_name(), 'base_id': str(m.base_id) if m.base_id else None,
                     'modelo_versao': m.modelo.versao, 'dados': m.dados, 'ocorrencias_correspondem_texto': m.tipo != 'editada',
                     'created_at': m.created_at, 'desatualizada': m.assinatura != fingerprint}
                    for m in atendimento.minutas_preparadas.select_related('modelo', 'autor', 'revisao_final__autor').all()]
        return Response({'assinatura': fingerprint, 'pronto': ready, 'motivo_bloqueio': blocked_reason,
                         'pendencias': len(report['pendencias']), 'modelo_aprovado': bool(model and model.aprovado), 'versoes': versions})

    @action(detail=True, methods=['post'], url_path='editar-minuta')
    def editar_minuta(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        atendimento = self.get_object()
        serializer = EditarMinutaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            from .ficha_estruturada import reservar_atendimento
            reservar_atendimento(atendimento)
            previous = atendimento.minutas_preparadas.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != request.user.id or str(previous.base_id) != str(data['minuta_id']) or previous.corpo != data['corpo'] or previous.motivo != data['motivo']:
                    raise ValidationError('Identificador de edição já utilizado.')
                return Response({'id': str(previous.id), 'versao': previous.versao})
            base = get_object_or_404(atendimento.minutas_preparadas, pk=data['minuta_id'])
            latest = atendimento.minutas_preparadas.first()
            _, _, fingerprint = snapshot(atendimento)
            if base.id != latest.id or base.versao != data['versao_esperada'] or base.assinatura != fingerprint:
                return Response({'detail': 'A minuta ou os dados mudaram. Reabra a versão atual antes de editar.'}, status=409)
            preparar(atendimento)
            revision = MinutaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                autor=request.user, modelo=base.modelo, base=base, tipo='editada', motivo=data['motivo'],
                client_id=data['client_id'], versao=latest.versao+1, corpo=data['corpo'], dados=base.dados,
                assinatura=base.assinatura)
        return Response({'id': str(revision.id), 'versao': revision.versao}, status=201)

    @action(detail=True, methods=['get'], url_path='comparar-minutas')
    def comparar_minutas(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers
        from .comparacao_minutas import comparar_minutas
        atendimento = self.get_object()
        base_id = serializers.UUIDField().run_validation(request.query_params.get('base'))
        target_id = serializers.UUIDField().run_validation(request.query_params.get('destino'))
        versions = atendimento.minutas_preparadas.select_related('modelo')
        base = get_object_or_404(versions, pk=base_id)
        target = get_object_or_404(versions, pk=target_id)
        response = Response(comparar_minutas(base, target))
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['post'], url_path=r'minutas/(?P<minuta_id>[0-9a-f-]+)/revisar')
    def revisar_minuta(self, request, pk=None, minuta_id=None):
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers
        from .models import RevisaoFinalMinuta
        from .revisao_final import hash_texto, registro_final
        atendimento = self.get_object()
        reason = serializers.CharField(max_length=2000).run_validation(request.data.get('motivo'))
        version = serializers.IntegerField(min_value=1).run_validation(request.data.get('versao_esperada'))
        if any(request.data.get(key) is not True for key in ['conferi_texto', 'conferi_dados', 'conferi_fontes']):
            raise ValidationError('Confira integralmente o texto, os dados e as fontes antes de registrar a revisão final.')
        with transaction.atomic():
            from .ficha_estruturada import reservar_atendimento
            reservar_atendimento(atendimento)
            minuta = get_object_or_404(atendimento.minutas_preparadas, pk=minuta_id)
            latest = atendimento.minutas_preparadas.first()
            _, _, fingerprint = snapshot(atendimento)
            if minuta.id != latest.id or minuta.versao != version or minuta.assinatura != fingerprint:
                return Response({'detail':'Esta minuta não é a versão atual. Revise os dados e abra a versão mais recente.'}, status=409)
            preparar(atendimento)
            if '{{' in minuta.corpo or '}}' in minuta.corpo or any(ord(c) < 32 and c not in '\n\r\t' for c in minuta.corpo):
                raise ValidationError('Corrija os marcadores ou caracteres inválidos antes da revisão final.')
            record, created = RevisaoFinalMinuta.objects.get_or_create(minuta=minuta,
                defaults={'tenant':atendimento.tenant, 'autor':request.user, 'motivo':reason, 'texto_sha256':hash_texto(minuta.corpo)})
            if not created and (record.autor_id != request.user.id or record.motivo != reason or record.texto_sha256 != hash_texto(minuta.corpo)):
                return Response({'detail':'Esta versão já possui revisão final registrada. O registro anterior foi preservado.'}, status=409)
            return Response(registro_final(minuta), status=201 if created else 200)

    @action(detail=True, methods=['get'], url_path=r'minutas/(?P<minuta_id>[0-9a-f-]+)/exportar')
    def exportar_minuta(self, request, pk=None, minuta_id=None):
        from django.shortcuts import get_object_or_404
        from . import exportacao
        atendimento = self.get_object()
        format = request.query_params.get('formato')
        if format not in ['docx', 'pdf']:
            raise ValidationError('Escolha docx ou pdf.')
        with transaction.atomic():
            from .ficha_estruturada import reservar_atendimento
            reservar_atendimento(atendimento)
            minuta = get_object_or_404(atendimento.minutas_preparadas.select_related('modelo'), pk=minuta_id)
            latest = atendimento.minutas_preparadas.first()
            _, _, fingerprint = snapshot(atendimento)
            if minuta.id != latest.id or minuta.assinatura != fingerprint:
                return Response({'detail': 'Esta versão está desatualizada. Reabra a versão atual; dados novos exigem revisão e nova preparação.'}, status=409)
            preparar(atendimento)
            from .revisao_final import registro_final
            review = registro_final(minuta)
            if not review or not review['texto_corresponde']:
                return Response({'detail':'Registre a revisão final desta versão antes de baixar Word ou PDF.'}, status=409)
            if '{{' in minuta.corpo or '}}' in minuta.corpo or any(ord(c) < 32 and c not in '\n\r\t' for c in minuta.corpo):
                raise ValidationError('O texto contém marcadores ou caracteres inválidos. Revise antes de exportar.')
            try:
                content = exportacao.word(minuta) if format == 'docx' else exportacao.pdf(minuta)
            except ValidationError:
                raise
            except Exception:
                return Response({'detail': 'Não foi possível produzir o arquivo. O texto salvo foi preservado.'}, status=503)
        mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if format == 'docx' else 'application/pdf'
        response = HttpResponse(content, content_type=mime)
        response['Content-Disposition'] = content_disposition_header(True, f'minuta-v{minuta.versao}.{format}')
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['post'], url_path='responder')
    def responder(self, request, pk=None):
        atendimento = self.get_object()
        serializer = RespostaConferenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        digest = assinatura(data)
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            previous = atendimento.mensagens.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != request.user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador de resposta já utilizado.')
                return Response({'mensagem': MensagemAtendimentoSerializer(previous).data, 'conferencia': conferir(atendimento)})
            report = conferir(atendimento)
            question = next((q for q in report['pendencias'] if q['chave'] == data['chave']), None)
            if not question or question['assinatura'] != data['assinatura'] or question['versao'] != data['versao_esperada']:
                return Response({'detail': 'As informações mudaram. Atualize a pergunta antes de responder.'}, status=409)
            if question['tipo'] in ['estrutura', 'pendencia_ficha', 'vinculacao_minuta', 'organizacao_documento']:
                raise ValidationError('Confira a ficha detalhada. Os registros por pessoa não podem ser resolvidos por uma resposta de bloco antigo.')
            document = question['tipo'] in ['documento', 'mensagem']
            if question['tipo'] == 'anexar':
                raise ValidationError('Anexe os documentos; uma resposta de texto não substitui os arquivos.')
            if document and not data['confirmar']:
                raise ValidationError('A revisão manual precisa ser confirmada explicitamente.')
            if not document and not data['valor'].strip():
                raise ValidationError('Informe uma resposta ou mantenha a pendência aberta.')
            if not document and data['confirmar'] and sem_dado(data['valor']):
                raise ValidationError('Uma informação ausente ou desconhecida não pode ser confirmada. Mantenha a pendência aberta.')
            message = MensagemAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                autor=request.user, client_id=data['client_id'], campo='' if document else data['chave'],
                pergunta=question['pergunta'], requisicao_hash=digest,
                texto=f"Revisão manual de {data['chave']}: {data['justificativa']}" if document else data['valor'])
            revision = None
            if not document:
                revision = RevisaoDadoAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                    autor=request.user, chave=data['chave'], valor=data['valor'], mensagem=message,
                    situacao='confirmado' if data['confirmar'] else 'informado',
                    justificativa=data['justificativa'], versao=question['versao'] + 1)
            if data['confirmar']:
                # Include this answer in the evidence snapshot. A later source reopens the question.
                new_question = next(q for q in conferir(atendimento)['pendencias'] if q['chave'] == data['chave'])
                DecisaoConferencia.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                    chave=data['chave'], assinatura=new_question['assinatura'], autor=request.user,
                    justificativa=data['justificativa'], revisao=revision)
            Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, request.user)
        return Response({'mensagem': MensagemAtendimentoSerializer(message).data, 'conferencia': conferir(atendimento)}, status=201)

    @action(detail=True, methods=['post'], url_path='verificar-redacao')
    def verificar_redacao(self, request, pk=None):
        report = conferir(self.get_object())
        return Response(report, status=409 if report['bloqueado'] else 200)

    @action(detail=True, methods=['get', 'post'], parser_classes=[MultiPartParser, FormParser])
    def anexos(self, request, pk=None):
        atendimento = self.get_object()
        if request.method == 'GET':
            return Response(AnexoAtendimentoSerializer(atendimento.anexos.defer('conteudo').select_related('organizacao_atual__autor').prefetch_related('paginas'), many=True).data)
        file = request.FILES.get('arquivo')
        if not file or file.size == 0 or file.size > MAX_BYTES:
            raise ValidationError('Envie um arquivo não vazio de até 10 MB.')
        name = Path(file.name.replace('\\', '/')).name[:200]
        ext = Path(name).suffix.lower()
        data = file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValidationError('O limite é de 10 MB.')
        types = {'.pdf': 'application/pdf', '.txt': 'text/plain', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
        if ext not in types:
            raise ValidationError('Formatos aceitos: PDF, TXT UTF-8, PNG e JPG.')
        if (ext == '.pdf' and not data.startswith(b'%PDF-')) or (ext == '.png' and not data.startswith(b'\x89PNG\r\n\x1a\n')) or (ext in ['.jpg', '.jpeg'] and not data.startswith(b'\xff\xd8\xff')):
            raise ValidationError('O conteúdo do arquivo não corresponde ao formato indicado.')
        digest = hashlib.sha256(data).hexdigest()
        existing = atendimento.anexos.filter(sha256=digest).first()
        if existing:
            return Response(AnexoAtendimentoSerializer(existing).data)
        result = None
        if ext == '.pdf':
            result = extrair_pdf(data)
        elif ext in ['.png', '.jpg', '.jpeg']:
            result = extrair_pdf(data, image=True)
        elif ext == '.txt':
            try:
                text = data.decode('utf-8-sig').strip()
            except UnicodeDecodeError:
                raise ValidationError('O TXT precisa estar em UTF-8. Nenhum conteúdo foi interpretado.')
            if not text or '\x00' in text or len(text) > 50000:
                raise ValidationError('TXT vazio, binário ou acima de 50.000 caracteres. Divida o arquivo.')
            result = {'situacao': 'extraido', 'aviso': 'Texto recebido literalmente; ainda não conferido.',
                      'metadados_leitura': {'total_paginas': 1, 'unidade': 'texto_txt', 'limites': []},
                      'paginas': [{'numero': 1, 'texto': text, 'situacao': 'extraido', 'aviso': 'TXT é apresentado como uma unidade de texto, não como página física.'}]}
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            attachment, created = AnexoAtendimento.objects.get_or_create(
                atendimento=atendimento, sha256=digest,
                defaults={'tenant': atendimento.tenant, 'autor': request.user, 'nome': name,
                          'mime': types[ext], 'tamanho': len(data), 'conteudo': data,
                          'situacao': result['situacao'], 'aviso': result['aviso'], 'metadados_leitura': result.get('metadados_leitura', {})})
            if created:
                PaginaAnexoAtendimento.objects.bulk_create([
                    PaginaAnexoAtendimento(tenant=atendimento.tenant, anexo=attachment, **page) for page in result['paginas']])
                Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
                from .pendencias_ficha import sincronizar
                sincronizar(atendimento, request.user)
        return Response(AnexoAtendimentoSerializer(attachment).data, status=201 if created else 200)

    @action(detail=True, methods=['get'], url_path=r'anexos/(?P<anexo_id>[0-9a-f-]+)/download')
    def download_anexo(self, request, pk=None, anexo_id=None):
        from django.shortcuts import get_object_or_404
        attachment = get_object_or_404(self.get_object().anexos, pk=anexo_id)
        response = HttpResponse(bytes(attachment.conteudo), content_type=attachment.mime)
        response['Content-Disposition'] = content_disposition_header(True, attachment.nome)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get'], url_path=r'anexos/(?P<anexo_id>[0-9a-f-]+)/paginas/(?P<pagina_id>[0-9a-f-]+)/imagem')
    def imagem_pagina(self, request, pk=None, anexo_id=None, pagina_id=None):
        from django.shortcuts import get_object_or_404
        from .leitura_anexos import renderizar_imagem
        atendimento = self.get_object()
        anexo = get_object_or_404(atendimento.anexos, pk=anexo_id)
        page = get_object_or_404(anexo.paginas, pk=pagina_id)
        if anexo.mime == 'text/plain':
            raise ValidationError('Este anexo é texto, não uma imagem.')
        content = renderizar_imagem(bytes(anexo.conteudo), page.numero, anexo.mime.startswith('image/'))
        if not content:
            return Response({'detail': 'Não consegui exibir a página. Baixe o original para conferir.'}, status=503)
        response = HttpResponse(content, content_type='image/png')
        response['Cache-Control'] = 'no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    @action(detail=True, methods=['post'], url_path=r'anexos/(?P<anexo_id>[0-9a-f-]+)/reler')
    def reler_anexo(self, request, pk=None, anexo_id=None):
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers
        atendimento = self.get_object()
        anexo = get_object_or_404(atendimento.anexos, pk=anexo_id)
        expected = serializers.IntegerField(min_value=1).run_validation(request.data.get('leitura_versao'))
        if anexo.mime not in ['application/pdf', 'image/png', 'image/jpeg']:
            raise ValidationError('OCR é aplicável a PDFs e imagens.')
        if expected != anexo.leitura_versao:
            return Response({'detail': 'A leitura já mudou. Atualize o anexo.'}, status=409)
        result = extrair_pdf(bytes(anexo.conteudo), image=anexo.mime.startswith('image/'))
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            anexo.refresh_from_db()
            if expected != anexo.leitura_versao:
                return Response({'detail': 'Outra leitura foi salva. Atualize o anexo.'}, status=409)
            version = expected+1
            PaginaAnexoAtendimento.objects.bulk_create([PaginaAnexoAtendimento(tenant=atendimento.tenant,
                anexo=anexo, leitura_versao=version, **page) for page in result['paginas']])
            anexo.leitura_versao = version
            anexo.situacao = result['situacao']; anexo.aviso = result['aviso']
            anexo.metadados_leitura = result.get('metadados_leitura', {})
            anexo.save(update_fields=['leitura_versao', 'situacao', 'aviso', 'metadados_leitura', 'updated_at'])
            Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, request.user)
        return Response(AnexoAtendimentoSerializer(anexo).data)

    @action(detail=True, methods=['get', 'post'])
    def ficha(self, request, pk=None):
        atendimento = self.get_object()
        if request.method == 'POST':
            serializer = AtualizarDadoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            with transaction.atomic():
                Atendimento.objects.select_for_update().get(pk=atendimento.pk)
                current = atendimento.revisoes.filter(objeto__isnull=True, chave=data['chave']).order_by('-versao').first()
                version = current.versao if current else 0
                if version != data['versao_esperada']:
                    return Response({'detail': 'Este campo foi alterado. Atualize a ficha antes de salvar.'}, status=409)
                message = None
                page = None
                organization = None
                if data.get('mensagem_id'):
                    message = atendimento.mensagens.filter(pk=data['mensagem_id']).first()
                    if not message:
                        raise ValidationError('A mensagem de origem não pertence a este atendimento.')
                    from .conversa_orientada import mensagem_atual
                    if not mensagem_atual(message):
                        return Response({'detail': 'Esta mensagem foi corrigida. Confira a mensagem atual.'}, status=409)
                if data.get('pagina_id'):
                    page = PaginaAnexoAtendimento.objects.filter(pk=data['pagina_id'], anexo__atendimento=atendimento).first()
                    source_text = (page.texto_ocr if data['canal_origem'] == 'ocr' else page.texto) if page else ''
                    if not page or page.leitura_versao != page.anexo.leitura_versao or data['trecho_origem'] not in source_text:
                        raise ValidationError('O trecho deve existir literalmente em uma página deste atendimento.')
                    from .organizacao_anexos import validar_fonte
                    organization = validar_fonte(page.anexo, None, page.numero, data.get('organizacao_versao'), data['situacao'] == 'confirmado')
                if not message and not page and data['valor'].strip():
                    # A manual entry is an authored statement, not extracted evidence.
                    message = MensagemAtendimento.objects.create(
                        atendimento=atendimento, tenant=atendimento.tenant, autor=request.user,
                        client_id=uuid.uuid4(), campo=data['chave'], texto=data['valor'],
                        pergunta='Informação registrada manualmente na ficha pela escrevente.')
                revision = RevisaoDadoAtendimento.objects.create(
                    atendimento=atendimento, tenant=atendimento.tenant, autor=request.user,
                    chave=data['chave'], valor=data['valor'], situacao=data['situacao'],
                    justificativa=data['justificativa'], mensagem=message, versao=version + 1,
                    pagina_origem=page, organizacao_origem=organization, trecho_origem=data.get('trecho_origem', ''), canal_origem=data['canal_origem'])
                Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
                from .pendencias_ficha import sincronizar
                sincronizar(atendimento, request.user)
            return Response(RevisaoDadoSerializer(revision).data, status=201)
        revisions = list(atendimento.revisoes.filter(objeto__isnull=True).select_related('autor', 'mensagem', 'pagina_origem__anexo').all())
        fields = []
        for key, (label, required) in campos_ativos(atendimento).items():
            history = [r for r in revisions if r.chave == key]
            fields.append({'chave': key, 'rotulo': label, 'obrigatorio': required,
                           'atual': RevisaoDadoSerializer(history[0]).data if history else None,
                           'historico': RevisaoDadoSerializer(history, many=True).data})
        return Response({'campos': fields})

    @action(detail=True, methods=['post'], url_path='interpretar-mensagem')
    def interpretar_mensagem(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers
        from .interpretacao_ia import analisar_mensagem, AnaliseIndisponivel
        atendimento = self.get_object()
        message_id = serializers.UUIDField().run_validation(request.data.get('mensagem_id'))
        message = get_object_or_404(atendimento.mensagens, pk=message_id)
        try:
            result = analisar_mensagem(message.texto)
        except AnaliseIndisponivel as error:
            return Response({'detail': str(error)}, status=503)
        proposals = [{**proposal, 'situacao': 'informado', 'confirmado': False,
                      'origem': {'tipo': 'mensagem', 'mensagem_id': str(message.id),
                                 'leitura': 'rotulos_locais_v1', 'trecho': proposal['trecho']}}
                     for proposal in result['propostas']]
        return Response({'mensagem_id': str(message.id), 'propostas': proposals,
                         'duvidas': result['duvidas'], 'confirmado': False, 'modo': 'simulacao_local',
                         'aviso': 'SIMULAÇÃO LOCAL por rótulos explícitos; não é interpretação por IA. Nenhum dado foi enviado a provedores externos. Confira contexto, pessoas e papéis: trecho literal não garante interpretação correta. Nenhum dado da ficha foi alterado.'})

    @action(detail=True, methods=['get', 'post'])
    def mensagens(self, request, pk=None):
        atendimento = self.get_object()
        if request.method == 'GET':
            return Response(MensagemAtendimentoSerializer(
                atendimento.mensagens.select_related('autor').all(), many=True).data)
        serializer = MensagemAtendimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            Atendimento.objects.select_for_update().get(pk=atendimento.pk)
            message, created = MensagemAtendimento.objects.get_or_create(
                atendimento=atendimento, client_id=serializer.validated_data['client_id'],
                defaults={'tenant': atendimento.tenant, 'autor': request.user,
                          'texto': serializer.validated_data['texto']})
            if message.autor_id != request.user.id or message.texto != serializer.validated_data['texto']:
                raise ValidationError('Identificador de mensagem já utilizado.')
            if created:
                Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
                from .pendencias_ficha import sincronizar
                sincronizar(atendimento, request.user)
        return Response(MensagemAtendimentoSerializer(message).data, status=201 if created else 200)


class ProcessoFilter(df_filters.FilterSet):
    tipo_ato = df_filters.CharFilter(field_name="tipo_ato", lookup_expr="icontains")
    status = df_filters.CharFilter(field_name="status", lookup_expr="iexact")

    class Meta:
        model = Processo
        fields = ["tipo_ato", "status", "responsavel"]


class ProcessoViewSet(BaseTenantViewSet):
    queryset = Processo.objects.all().order_by("-created_at")
    serializer_class = ProcessoSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProcessoFilter
    search_fields = ["tipo_ato", "id"]
    ordering_fields = ["created_at", "updated_at", "sla_at"]


class ProcessoParteViewSet(BaseTenantViewSet):
    queryset = ProcessoParte.objects.all().order_by("-created_at")
    serializer_class = ProcessoParteSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["processo", "papel", "parte"]
    search_fields = ["processo__id", "parte__nome"]
    ordering_fields = ["created_at", "updated_at"]


class ProtocoloViewSet(BaseTenantViewSet):
    queryset = Protocolo.objects.all().order_by("-ano", "-numero")
    serializer_class = ProtocoloSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["ano", "tipo", "processo"]
    search_fields = ["numero", "processo__id"]
    ordering_fields = ["ano", "numero", "created_at"]
