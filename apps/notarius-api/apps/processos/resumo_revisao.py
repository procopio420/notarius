"""Read-only review overview over current, source-linked records."""
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .ficha import campos_ativos
from .conferencia import conferir, assinatura
from .redacao import snapshot, preparar
from .serializers import AtendimentoSerializer, RevisaoDadoSerializer
from .revisao_final import registro_final

class ResumoAlterado(Exception):
    pass

def gerar_resumo(atendimento):
    model, _, fingerprint = snapshot(atendimento)
    latest_draft = atendimento.minutas_preparadas.first()
    draft_id = latest_draft.id if latest_draft else None
    report = conferir(atendimento)
    latest = {}
    for revision in atendimento.revisoes.filter(objeto__isnull=True).select_related('autor', 'mensagem', 'pagina_origem__anexo').order_by('chave', '-versao'):
        latest.setdefault(revision.chave, revision)
    fields = [{'chave':key, 'rotulo':label, 'obrigatorio':required,
               'atual':RevisaoDadoSerializer(latest[key]).data if key in latest else None}
              for key,(label,required) in campos_ativos(atendimento).items()]
    documents = []
    decisions = list(atendimento.decisoes.select_related('autor').order_by('-created_at','-id'))
    for attachment in atendimento.anexos.defer('conteudo').prefetch_related('paginas').all():
        sign = assinatura([f'anexo:{attachment.id}',attachment.sha256,attachment.leitura_versao])
        decision = next((d for d in decisions if d.chave == f'anexo:{attachment.id}' and d.assinatura == sign),None)
        pages = [p for p in attachment.paginas.all() if p.leitura_versao == attachment.leitura_versao]
        documents.append({'id':str(attachment.id), 'nome':attachment.nome, 'situacao_leitura':attachment.situacao,
            'aviso':attachment.aviso, 'leitura_versao':attachment.leitura_versao, 'paginas':len(pages),
            'paginas_ocr':sum(bool(p.texto_ocr) for p in pages),
            'revisao_manual':{'autor_nome':decision.autor.get_full_name() or decision.autor.username,
                'created_at':decision.created_at, 'justificativa':decision.justificativa} if decision else None})
    ready = False
    reason = 'Resolva as pendências do atendimento.' if report['bloqueado'] else 'Revise e aprove o modelo atual.'
    if not report['bloqueado'] and model and model.aprovado:
        try:
            preparar(atendimento)
            ready = True
            reason = ''
        except ValidationError as error:
            reason = ' '.join(map(str,error.detail)) if isinstance(error.detail,list) else str(error.detail)
    _, _, current_fingerprint = snapshot(atendimento)
    current_draft = atendimento.minutas_preparadas.first()
    if current_fingerprint != fingerprint or (current_draft.id if current_draft else None) != draft_id:
        raise ResumoAlterado()
    return {'gerado_em':timezone.now(), 'assinatura':fingerprint,
        'atendimento':AtendimentoSerializer(atendimento).data, 'campos':fields, 'documentos':documents,
        'pendencias':report['pendencias'], 'pronto_para_preparar':ready, 'motivo_bloqueio':reason,
        'modelo':{'id':str(model.id), 'versao':model.versao, 'aprovado':model.aprovado} if model else None,
        'minuta':{'id':str(latest_draft.id), 'versao':latest_draft.versao, 'tipo':latest_draft.tipo,
                  'desatualizada':latest_draft.assinatura != fingerprint,
                  'revisao_final':registro_final(latest_draft)} if latest_draft else None,
        'aviso':'Resumo dos registros atuais, não uma aprovação do ato. Confirmação humana e trecho literal não comprovam autenticidade ou veracidade. Confira o conteúdo integral dos documentos e da minuta.'}
