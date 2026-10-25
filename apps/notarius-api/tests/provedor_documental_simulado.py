"""Test fixtures only. Not selectable by an HTTP request or production setting."""
from copy import deepcopy
from apps.processos.analise_documental import ambiente_de_teste
from apps.processos.provedor_documental import ProvedorIndisponivel


class ProvedorSimulado:
    identificador = 'simulado_documental_teste_v1'

    def __init__(self, resposta, erro=None):
        if not ambiente_de_teste():
            raise ProvedorIndisponivel('Simulação exclusiva do banco e contexto de teste.')
        self.resposta, self.erro, self.chamadas = resposta, erro, 0

    def analisar(self, entrada):
        if not ambiente_de_teste():
            raise ProvedorIndisponivel('Simulação fora de teste recusada.')
        self.chamadas += 1
        if self.erro:
            raise self.erro
        return deepcopy(self.resposta(entrada) if callable(self.resposta) else self.resposta)


def resposta_ficticia(entrada):
    """Hand-authored fixtures with literal labels, not an AI implementation."""
    unidades = []
    for u in entrada.unidades:
        proposals = []
        if u.texto.startswith('Nome: ') and not u.instrucao_suspeita:
            target = u.destinatarios[0] if len(u.destinatarios) == 1 else None
            proposals = [{'fonte': u.fonte.model_dump(), 'trecho': u.texto, 'inicio': 0, 'fim': len(u.texto),
                'valor': u.texto[6:], 'tipo_registro': 'pessoa', 'campo': 'nome',
                'registro_sugerido_id': target, 'relacionado_id': target, 'associacao': 'sugerida' if target else 'incerta'}]
        unidades.append({'unidade_id': u.unidade_id, 'situacao': 'propostas' if proposals else 'revisao_manual',
                         'propostas': proposals, 'duvidas': [] if proposals else ['RESPOSTA SIMULADA: revisar esta unidade no original; nenhum fato presumido.']})
    return {'contrato': 'documental_v1', 'contexto_assinatura': entrada.contexto_assinatura, 'unidades': unidades}
