"""Display labels from explicit saved links, never identity or relationship inference."""
def rotulos(atendimento, revisoes=None):
    objects=list(atendimento.objetos_ficha.exclude(tipo='legado'))
    revisions=revisoes if revisoes is not None else atendimento.revisoes.filter(objeto__isnull=False).order_by('-versao','-created_at')
    values={}
    for r in revisions:
        if r.objeto_id: values.setdefault((str(r.objeto_id),r.chave),r.valor)
    def value(oid,key,fallback):
        return (values.get((str(oid),key)) or fallback)[:100]
    result={}
    for obj in objects:
        oid=str(obj.id)
        if obj.tipo=='pessoa': label='Pessoa — '+value(oid,'nome','nome não informado')
        elif obj.tipo=='papel': label=value(oid,'tipo_papel','Papel a revisar')+' — '+value(obj.pessoa_a_id,'nome','pessoa sem nome informado')
        elif obj.tipo=='relacao':
            kind={'conjuge_de':'Cônjuge informado','representante_de':'Representação informada'}.get(value(oid,'tipo_relacao',''),'Relação informada')
            label=kind+' — '+value(obj.pessoa_a_id,'nome','primeira pessoa sem nome')+' → '+value(obj.pessoa_b_id,'nome','segunda pessoa sem nome')
        elif obj.tipo=='imovel': label='Imóvel — '+value(oid,'descricao','descrição não informada')
        elif obj.tipo=='negociacao': label='Negociação — '+value(obj.imovel_id,'descricao','imóvel sem descrição informada')
        elif obj.tipo=='complemento': label='Complemento — '+value(oid,'assunto','assunto não informado')
        else: label='Dados do ato — '+value(oid,'referencia','referência não informada')
        result[oid]=label+' · '+oid[:8]
    return result
