import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.processos.casos_avaliacao_ia import CASOS
from apps.processos.avaliacao_ia import avaliar_resultado, validar_casos, versoes
from apps.processos.interpretacao_ia import analisar_mensagem, AnaliseIndisponivel

class Command(BaseCommand):
    help = 'Avaliação legada de mensagens por rótulos, sem IA real; não avalia documental_v1. Para documentos, use avaliar_ia_documental.'

    def add_arguments(self, parser):
        parser.add_argument('--executar', action='store_true', help='Executa somente a simulação local dos casos fictícios.')
        parser.add_argument('--repeticoes', type=int, default=1)
        parser.add_argument('--saida', required=True, help='Novo arquivo JSON de relatório; não sobrescreve arquivo existente.')

    def handle(self, *args, **options):
        if not 1 <= options['repeticoes'] <= 3:
            raise CommandError('Use entre 1 e 3 repetições.')
        destination = Path(options['saida']).resolve()
        if destination.exists() or not destination.parent.is_dir():
            raise CommandError('Escolha um arquivo novo em uma pasta existente.')
        validar_casos(CASOS)
        report = {'criado_em':timezone.now().isoformat(), 'modelo':'simulador_por_rotulos',
                  'versoes':versoes(CASOS), 'modo':'simulacao_local' if options['executar'] else 'validacao_local',
                  'quantidade_casos':len(CASOS), 'resultados':[], 'avaliacao_modelo':'nao_executada',
                  'limite':'Casos fictícios finitos; aprovação não equivale a homologação jurídica ou ausência de erros.'}
        if options['executar']:
            for iteration in range(options['repeticoes']):
                for case in CASOS:
                    item = {'caso':case['id'], 'repeticao':iteration+1}
                    try:
                        response = analisar_mensagem(case['texto'])
                        errors = avaliar_resultado(case, response)
                        item.update({'estado':'reprovado' if errors else 'aprovado', 'erros':errors, 'resposta':response})
                    except AnaliseIndisponivel:
                        item.update({'estado':'inconclusivo', 'erros':['Provedor indisponível ou resposta rejeitada.']})
                    report['resultados'].append(item)
                    self.stdout.write(case['id']+': '+item['estado'])
                    # Stop on provider failure rather than repeatedly billing/failing requests.
                    if item['estado'] == 'inconclusivo':
                        break
                if report['resultados'][-1]['estado'] == 'inconclusivo':
                    break
            states = [r['estado'] for r in report['resultados']]
            report['avaliacao_modelo'] = ('inconclusiva' if 'inconclusivo' in states else
                'reprovada' if 'reprovado' in states else 'aprovada_nestes_casos')
        with destination.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
        self.stdout.write('Relatório salvo: '+str(destination))
        if report['avaliacao_modelo'] in ['inconclusiva','reprovada']:
            raise CommandError('A avaliação não aprovou o modelo. Consulte o relatório.')
        if not options['executar']:
            self.stdout.write('Casos validados. Modelo NÃO avaliado. Nenhuma chamada externa.')
