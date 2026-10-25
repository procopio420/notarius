"""Technical record links and explicitly configured dependencies, not legal inference."""
def fonte_atual(revision):
    source = revision.revisao_origem if revision.revisao_origem_id else revision
    if source.mensagem_id:
        from .conversa_orientada import mensagem_atual
        if not mensagem_atual(source.mensagem):
            return False
    from .organizacao_anexos import fonte_valida
    return (not source.pagina_origem_id or source.pagina_origem.leitura_versao == source.pagina_origem.anexo.leitura_versao) and fonte_valida(revision)


def resumo_revisao(revision):
    if not revision:
        return None
    return {'id': str(revision.id), 'versao': revision.versao, 'situacao': revision.situacao,
            'fonte_atual': fonte_atual(revision)}


def capturar(atendimento, objeto, chave, visitados=None):
    visitados = set(visitados or ())
    if chave in visitados:
        return {'configuracao_ciclica': True}
    visitados.add(chave)
    dependencies = {}
    if objeto.tipo == 'complemento':
        from .ficha_estruturada_schema import dependencias_classificacao
        for key in dependencias_classificacao(chave):
            revision = objeto.revisoes.filter(chave=key).select_related('pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo').first()
            dependencies[f'classificacao:{key}'] = resumo_revisao(revision)
    links = [objeto.pessoa_a_id, objeto.pessoa_b_id, objeto.imovel_id]
    for linked_id in [i for i in links if i]:
        latest = {}
        for r in atendimento.revisoes.filter(objeto_id=linked_id).select_related('pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo'):
            latest.setdefault(r.chave, resumo_revisao(r))
        dependencies[f'registro:{linked_id}'] = latest
    model = atendimento.modelos_minuta.first()
    if model:
        keys = sorted({field for rule in model.dependencias_campos_ficha
                       if rule['tipo'] == objeto.tipo and rule['chave'] == chave for field in rule['depende_de']})
        for key in keys:
            r = objeto.revisoes.filter(chave=key).select_related('pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo').first()
            dependencies[f'campo:{key}'] = {'revisao': resumo_revisao(r), 'dependencias': capturar(atendimento, objeto, key, visitados)}
    return dependencies


def confirmacao_atual(atendimento, revision):
    return bool(revision and revision.situacao == 'confirmado' and fonte_atual(revision)
                and revision.dependencias_ficha == capturar(atendimento, revision.objeto, revision.chave))
