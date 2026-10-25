"""Offline policy and non-secret diagnostics. No SDK client or network."""
import os
from dataclasses import dataclass, asdict
from importlib.metadata import version, PackageNotFoundError

@dataclass(frozen=True)
class LimitesDocumentais:
    documentos: int = 5
    unidades: int = 200
    caracteres_unidade: int = 4000
    caracteres_texto: int = 100000
    bytes_requisicao: int = 600000
    bytes_resposta: int = 500000
    tokens_saida: int = 12000
    tentativas_por_acao: int = 1
    repeticoes_sdk: int = 0
    conexao_s: int = 5
    leitura_s: int = 45
    escrita_s: int = 10
    pool_s: int = 5
    prazo_total_planejado_s: int = 60

LIMITES = LimitesDocumentais()
PROVEDOR_PLANEJADO = 'OpenAI Responses API'
BASE_URL = 'https://api.openai.com/v1'
AVISOS = {
 'ia_bloqueada': 'A IA real está bloqueada nesta fase. Nenhum documento foi enviado. Documentos, mensagens e rascunhos foram preservados; continue a revisão manual.',
 'chave_ausente': 'A chave do provedor não está configurada. Nenhuma proposta foi aplicada. Seu trabalho foi preservado; solicite a configuração à pessoa responsável.',
 'creditos_indisponiveis': 'O provedor informou limite de uso ou créditos indisponíveis. A análise foi interrompida sem alterar a ficha. Seu trabalho foi preservado; confira a conta antes de uma nova tentativa.',
 'tempo_esgotado': 'O provedor não respondeu dentro do prazo. Nenhuma proposta foi aplicada. Seu trabalho foi preservado; confira o atendimento antes de tentar novamente. Uma cobrança externa não pode ser descartada só por haver timeout.',
 'limite_temporario': 'O provedor informou um limite temporário de solicitações. Nenhuma proposta foi aplicada. Aguarde e confira o atendimento antes de tentar novamente; não houve repetição automática.',
 'credencial_recusada': 'O provedor recusou a credencial ou o acesso. Nenhuma proposta foi aplicada. Seu trabalho foi preservado; solicite a revisão da configuração.',
 'provedor_indisponivel': 'Falha do provedor. Nenhuma proposta foi aplicada e não houve troca para simulação. Documentos, mensagens e rascunhos foram preservados.',
 'simulacao_fora_teste': 'Resposta simulada recusada nesta ação. Simulação é exclusiva de testes e não substitui IA real. O histórico e seu trabalho foram preservados.',
}


def diagnostico(ambiente=None):
    env=os.environ if ambiente is None else ambiente
    key=env.get('OPENAI_API_KEY','')
    if ambiente is None:
        from django.conf import settings
        key=key or getattr(settings,'OPENAI_API_KEY','')
    model=env.get('NOTARIUS_MODELO_DOCUMENTAL','')
    endpoint=env.get('OPENAI_BASE_URL','').rstrip('/')
    try: sdk=version('openai')
    except PackageNotFoundError: sdk=None
    pending=['autorizacao_envio_ausente','transporte_real_nao_implementado','creditos_nao_consultados','avaliacao_real_pendente','homologacao_profissional_pendente']
    if not isinstance(key,str) or not key.strip(): pending.append('chave_ausente')
    if not isinstance(model,str) or not model.strip(): pending.append('modelo_nao_definido')
    if endpoint and endpoint!=BASE_URL: pending.append('destino_alternativo_nao_permitido')
    if not sdk: pending.append('sdk_ausente')
    return {'modo':'bloqueado_sem_envio','disponivel':False,'provedor_planejado':PROVEDOR_PLANEJADO,
            'destino_planejado':BASE_URL+'/responses','chave_configurada':'chave_ausente' not in pending,
            'modelo_definido':'modelo_nao_definido' not in pending,'sdk_instalado':sdk,
            'creditos':'nao_consultados','pendencias':pending,'limites':asdict(LIMITES),
            'aviso':AVISOS['ia_bloqueada'], 'limites_http':'Planejados para o transporte futuro; não foram testados em rede. Nenhuma variável de ambiente autoriza envio neste código.'}


def codigo_falha(error):
    # Never use str(error), headers or arbitrary provider text as a public notice.
    code=getattr(error,'codigo',None)
    if isinstance(code,str) and code in AVISOS: return code
    body=getattr(error,'body',None)
    provider_code=getattr(error,'code',None)
    if isinstance(body,dict):
        detail=body.get('error',body)
        if isinstance(detail,dict): provider_code=detail.get('code') or detail.get('type') or provider_code
    if provider_code in ['insufficient_quota','billing_hard_limit_reached']: return 'creditos_indisponiveis'
    if isinstance(error,TimeoutError) or type(error).__name__ in ['APITimeoutError','ReadTimeout','ConnectTimeout','WriteTimeout','PoolTimeout']:
        return 'tempo_esgotado'
    status=getattr(error,'status_code',None)
    if status in [401,403]: return 'credencial_recusada'
    if status==429: return 'limite_temporario'
    return 'provedor_indisponivel'
