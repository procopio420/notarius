"""Offline oracle over fictional inputs. It never invokes or authenticates a model."""
import hashlib
import json
from .contratos_documentais import EntradaDocumental, SaidaDocumental
from .analise_documental import validar_saida
from .provedor_documental import ProvedorReal, RespostaInvalida, INSTRUCOES
from .politica_documental import LIMITES


def hash_json(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True).encode()).hexdigest()


def versoes(cases):
    return {'avaliador':'documental_ficticio_v1','casos_sha256':hash_json(cases),
            'instrucoes_sha256':hash_json(INSTRUCOES),'entrada_schema_sha256':hash_json(EntradaDocumental.model_json_schema()),
            'saida_schema_sha256':hash_json(SaidaDocumental.model_json_schema())}


def validar_casos(cases):
    seen=set()
    for case in cases:
        if case['id'] in seen or case.get('inteiramente_ficticio') is not True: raise ValueError('Caso repetido ou não fictício.')
        seen.add(case['id']); entrada=EntradaDocumental.model_validate(case['entrada'])
        units={u.unidade_id:u for u in entrada.unidades}
        for expected in case['permitidos']:
            if expected['unidade_id'] not in units or expected['valor'] not in units[expected['unidade_id']].texto:
                raise ValueError('Oráculo não literal ou referência inexistente.')
        if any(e not in case['permitidos'] for e in case['obrigatorios']): raise ValueError('Obrigatório sem resposta admitida.')
        if sum(len(u.texto) for u in entrada.unidades)>LIMITES.caracteres_texto: raise ValueError('Entrada excessiva.')


def avaliar_caso(case,raw):
    try:
        entrada=EntradaDocumental.model_validate(case['entrada'])
        parsed=SaidaDocumental.model_validate(raw).model_dump()
        validar_saida(entrada,parsed)
    except Exception:
        return {'estado':'reprovado','erros':['contrato_fonte_ou_evidencia_invalida']}
    errors=[]; found=[]
    for row in parsed['unidades']:
        unit=next(u for u in entrada.unidades if u.unidade_id==row['unidade_id'])
        if case['duvida_obrigatoria'] and not any(d.strip() for d in row['duvidas']): errors.append('incerteza_nao_encaminhada')
        for p in row['propostas']:
            candidate={k:p[k] for k in ['tipo_registro','campo','valor','registro_sugerido_id','associacao']}
            candidate['unidade_id']=row['unidade_id']
            if candidate not in case['permitidos']: errors.append('valor_campo_pessoa_ou_associacao_incorretos')
            else: found.append(candidate)
            if p['trecho']!=unit.texto or p['inicio']!=0 or p['fim']!=len(unit.texto): errors.append('contexto_literal_incompleto')
    if any(e not in found for e in case['obrigatorios']): errors.append('informacao_obrigatoria_omitida')
    return {'estado':'reprovado' if errors else 'sem_erros_neste_caso_fornecido','erros':sorted(set(errors))}


def plano(cases,modelo=None):
    validar_casos(cases)
    return {'modo':'preparacao_local_sem_envio','provedor_planejado':'OpenAI Responses API','avaliacao_real':'nao_executada',
            'modelo_fornecido':bool(modelo),'versoes':versoes(cases),'quantidade_casos':len(cases),
            'avisos':['Somente casos fictícios embutidos. Nenhum atendimento ou arquivo de cliente foi consultado.',
                      'O oráculo é local e não integra a requisição destinada ao modelo. Zero confirmações automáticas.'],
            'casos':[{'id':c['id'],'entrada':c['entrada'],'oraculo':{'permitidos':c['permitidos'],'obrigatorios':c['obrigatorios'],'duvida_obrigatoria':c['duvida_obrigatoria']},
                      'requisicao_planejada':ProvedorReal.preparar_requisicao(EntradaDocumental.model_validate(c['entrada']),modelo) if modelo else None} for c in cases]}
