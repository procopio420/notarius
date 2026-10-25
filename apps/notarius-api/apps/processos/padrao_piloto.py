"""Candidate from the existing professional package; never case data or approval."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from .blocos_minuta import plano, referencias, expansoes, MARCADORES
from .ficha_estruturada_schema import SCHEMA
from .redacao import validar_modelo, validar_fatos_fixos
from .serializers import SalvarModeloSerializer

ARQUIVO = Path(__file__).resolve().parents[4] / 'docs/piloto-profissional/padrao-acompanhado-v2.json'


def candidato():
    raw = ARQUIVO.read_bytes()
    package = json.loads(raw)
    # Always reconstruct and validate; no shared mutable template or fallback.
    serializer = SalvarModeloSerializer(data=package['modelo'])
    serializer.is_valid(raise_exception=True)
    model = dict(serializer.validated_data)
    if package['aprovado'] is not False or model['aprovado'] is not False:
        raise ValueError('O pacote oferecido deve permanecer rascunho sem aprovação.')
    validar_modelo(model)
    validar_fatos_fixos(SimpleNamespace(**model))
    positions = {r['chave']: r for r in model['registros_minuta']}
    fields = {kind: {f['chave']: f['rotulo'] for f in schema} for kind, schema in SCHEMA.items()}
    def rotulo(match):
        alias, field = match[1], match[2]
        return '⟦' + positions[alias]['rotulo'] + ': ' + fields[positions[alias]['tipo']][field] + '⟧'
    preview = []
    for section, nodes in plano(model).items():
        if not model[section].strip():
            continue
        preview.append(''.join(MARCADORES.sub(rotulo, text) for node in nodes for text, _ in expansoes(node)))
    package.update(modelo=model, texto_candidato='\n\n'.join(preview), sha256=hashlib.sha256(raw).hexdigest(),
                   mapa_campos=[{'marcador': f'{alias}.{field}', 'tipo': positions[alias]['tipo'],
                                 'rotulo': fields[positions[alias]['tipo']][field]}
                                for alias, field in sorted(set(referencias(model)))])
    return package
