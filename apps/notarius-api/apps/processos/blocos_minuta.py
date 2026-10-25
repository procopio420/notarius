"""Bounded template directives, never Python/Jinja/eval or inferred clauses."""
import json
import re
from rest_framework.exceptions import ValidationError

DIRETIVA = re.compile(r'{%([\s\S]*?)%}')
ID = r'[a-z][a-z0-9_]{0,39}'
REF = re.compile(rf'({ID})\.({ID})')
MARCADORES = re.compile(rf'\{{\{{\s*({ID})\.({ID})\s*\}}\}}')


def plano(model):
    get = (lambda k: model.get(k, '')) if isinstance(model, dict) else (lambda k: getattr(model, k))
    result = {}; keys = set(); total = 0
    for section in ['corpo', 'representacao', 'observacoes']:
        text = get(section); nodes = []; cursor = 0; active = None
        for match in DIRETIVA.finditer(text):
            header = match[1].strip()
            if header == 'fim':
                if not active:
                    raise ValidationError('Fim de bloco sem abertura configurada.')
                body = text[cursor:match.start()]
                if '{%' in body or '%}' in body:
                    raise ValidationError('Diretiva incompleta no bloco.')
                nodes.append({**active, 'texto': body}); active = None
            else:
                if active:
                    raise ValidationError('Blocos aninhados não são suportados. Separe as decisões explicitamente.')
                nodes.append({'tipo': 'texto', 'texto': text[cursor:match.start()]})
                condition = re.fullmatch(rf'se\s+({ID})\s+(\{{[\s\S]*\}})', header)
                repeat = re.fullmatch(rf'repetir\s+({ID})\s+({ID}(?:\s*,\s*{ID})*)', header)
                if condition:
                    try:
                        def unique(pairs):
                            data = {}
                            for k, v in pairs:
                                if k in data: raise ValueError('duplicado')
                                data[k] = v
                            return data
                        rule = json.loads(condition[2], object_pairs_hook=unique)
                    except (ValueError, TypeError, RecursionError):
                        raise ValidationError('Condição inválida: use campo, permitidos e incluir sem chaves duplicadas.') from None
                    if not isinstance(rule, dict) or set(rule) != {'campo', 'permitidos', 'incluir'} or not isinstance(rule['campo'], str) or not REF.fullmatch(rule['campo']):
                        raise ValidationError('Condição exige campo posição.campo, alternativas permitidas e alternativas que incluem o bloco.')
                    for key in ['permitidos', 'incluir']:
                        vals = rule[key]
                        if not isinstance(vals, list) or not 1 <= len(vals) <= 20 or any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in vals) or len(set(vals)) != len(vals):
                            raise ValidationError('Configure de 1 a 20 alternativas literais distintas por condição.')
                    if not set(rule['incluir']).issubset(rule['permitidos']) or any(v in ['a_esclarecer', 'pendente'] for v in rule['permitidos']):
                        raise ValidationError('As alternativas de inclusão devem pertencer ao cenário permitido; incerteza não é cenário aprovado.')
                    active = {'tipo': 'se', 'chave': condition[1], 'regra': rule}
                elif repeat:
                    positions = [v.strip() for v in repeat[2].split(',')]
                    if len(positions) > 60 or len(positions) != len(set(positions)):
                        raise ValidationError('Repetição exige até 60 posições explícitas e distintas, na ordem desejada.')
                    active = {'tipo': 'repetir', 'chave': repeat[1], 'posicoes': positions}
                else:
                    raise ValidationError('Diretiva não reconhecida. Use somente se, repetir e fim; sem expressões livres.')
                if active['chave'] in keys:
                    raise ValidationError('Cada bloco deve ter identificador próprio no modelo inteiro.')
                keys.add(active['chave']); total += 1
                if total > 60:
                    raise ValidationError('O modelo admite até 60 blocos explícitos.')
            cursor = match.end()
        if active or '{%' in text[cursor:] or '%}' in text[cursor:]:
            raise ValidationError('Bloco sem fechamento ou diretiva incompleta.')
        nodes.append({'tipo': 'texto', 'texto': text[cursor:]})
        if any('{%' in n['texto'] or '%}' in n['texto'] for n in nodes):
            raise ValidationError('Diretiva incompleta; o texto não será tratado como bloco aprovado.')
        result[section] = nodes
    return result


def expansoes(node):
    if node['tipo'] != 'repetir':
        return [(node['texto'], None)]
    if not any(alias == 'item' for alias, _ in MARCADORES.findall(node['texto'])):
        raise ValidationError('O texto de repetição precisa usar ao menos um marcador item.campo.')
    return [(MARCADORES.sub(lambda m: '{{'+alias+'.'+m[2]+'}}' if m[1] == 'item' else m[0], node['texto']),
             {'bloco': node['chave'], 'posicao': alias, 'indice': i + 1}) for i, alias in enumerate(node['posicoes'])]


def referencias(model):
    found = []
    for nodes in plano(model).values():
        for node in nodes:
            if node['tipo'] == 'se': found.append(tuple(node['regra']['campo'].split('.')))
            for text, _ in expansoes(node): found.extend(MARCADORES.findall(text))
    if len(found) > 3000:
        raise ValidationError('O modelo expandido excede 3.000 referências. Nada será truncado.')
    return found
