"""Evaluation oracle deliberately stricter than literal-substring validation."""
import hashlib
import json
from .interpretacao_ia import Interpretacao, PROMPT

def avaliar_resultado(caso, resposta):
    errors = []
    try:
        parsed = Interpretacao.model_validate(resposta)
    except Exception:
        return ['Estrutura inválida.']
    found = set()
    for proposal in parsed.propostas:
        if proposal.trecho not in caso['texto'] or proposal.valor not in proposal.trecho:
            errors.append('Evidência não literal.')
        if proposal.valor not in caso['permitidos'].get(proposal.campo, []):
            errors.append('Campo ou valor fora das respostas esperadas para este caso fictício.')
        else:
            found.add(proposal.campo)
    if set(caso['obrigatorios']) - found:
        errors.append('Informação explícita obrigatória omitida.')
    if any(not quote.strip() or quote not in caso['texto'] for quote in parsed.duvidas):
        errors.append('Dúvida sem trecho literal válido.')
    if caso['duvida'] and not parsed.duvidas:
        errors.append('Incerteza não encaminhada à escrevente.')
    return list(dict.fromkeys(errors))

def validar_casos(casos):
    ids = set()
    for caso in casos:
        if caso['id'] in ids or not caso['texto'].strip() or len(caso['texto']) > 10000:
            raise ValueError('Caso inválido ou duplicado.')
        ids.add(caso['id'])
        for campo, valores in caso['permitidos'].items():
            for valor in valores:
                if not valor or valor not in caso['texto']:
                    raise ValueError('Resposta esperada não literal.')
        if set(caso['obrigatorios']) - set(caso['permitidos']):
            raise ValueError('Campo obrigatório sem resposta esperada.')

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

def versoes(casos):
    return {'casos_sha256':fingerprint(casos), 'prompt_sha256':fingerprint(PROMPT),
            'schema_sha256':fingerprint(Interpretacao.model_json_schema())}
