"""Literal saved-version comparison. No semantic or legal interpretation."""
from difflib import SequenceMatcher
from .ficha import CAMPOS

MAX_LINES = 1500

def comparar_textos(before, after):
    old = before.splitlines(keepends=True)
    new = after.splitlines(keepends=True)
    # Bound the matching work for pathological or very fragmented documents.
    if len(old) > MAX_LINES or len(new) > MAX_LINES:
        if before == after:
            return [{'tipo':'igual', 'texto':before}], True
        return [{'tipo':'removido','texto':before}, {'tipo':'adicionado','texto':after}], True
    parts = []
    for tag, a, b, c, d in SequenceMatcher(None, old, new, autojunk=True).get_opcodes():
        if tag == 'equal':
            parts.append({'tipo':'igual', 'texto':''.join(old[a:b])})
        else:
            if a != b:
                parts.append({'tipo':'removido', 'texto':''.join(old[a:b])})
            if c != d:
                parts.append({'tipo':'adicionado', 'texto':''.join(new[c:d])})
    return parts, False

def comparar_minutas(base, target):
    parts, simplified = comparar_textos(base.corpo, target.corpo)
    fields = []
    labels = {key: label for key, (label, _) in CAMPOS.items()}
    labels.update({key: key for key in set(base.dados) | set(target.dados) if key not in labels})
    for key, label in labels.items():
        old, new = base.dados.get(key), target.dados.get(key)
        if old != new:
            fields.append({'chave':key, 'rotulo':label, 'antes':old, 'depois':new,
                           'valor_alterado':(old or {}).get('valor') != (new or {}).get('valor')})
    return {'base':{'id':str(base.id), 'versao':base.versao, 'modelo_versao':base.modelo.versao},
            'destino':{'id':str(target.id), 'versao':target.versao, 'modelo_versao':target.modelo.versao},
            'texto_alterado':base.corpo != target.corpo, 'trechos':parts,
            'dados_alterados':fields, 'comparacao_simplificada':simplified,
            'aviso':'Comparação literal entre versões salvas. Alterações manuais no texto não atualizam a ficha. Isto não verifica correção jurídica ou veracidade.'}
