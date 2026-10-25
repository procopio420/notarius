import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.processos.casos_avaliacao_documental import casos
from apps.processos.avaliacao_documental import plano, avaliar_caso, versoes
from apps.processos.provedor_documental import ProvedorReal, objeto_sem_repeticoes

class Command(BaseCommand):
    help='Prepara avaliação documental fictícia ou confere respostas fornecidas, sempre offline. Não ativa IA.'
    def add_arguments(self,parser):
        parser.add_argument('--saida',required=True)
        parser.add_argument('--modelo')
        parser.add_argument('--respostas',help='JSON local com envelopes Responses por caso; procedência não é atestada.')
        parser.add_argument('--executar-real',action='store_true',help='Recusado nesta fase; nenhum transporte está habilitado.')
    def handle(self,*args,**options):
        if options['executar_real']: raise CommandError('Envio real bloqueado: exige autorização, créditos, revisão do transporte e aceite. Nenhum dado enviado.')
        destination=Path(options['saida']).resolve()
        if destination.exists() or not destination.parent.is_dir(): raise CommandError('Escolha um arquivo novo em pasta existente.')
        cases=casos()
        if not options['respostas']: report=plano(cases,options['modelo'])
        else:
            try:
                source=Path(options['respostas'])
                if source.stat().st_size>6000000: raise ValueError()
                raw=json.loads(source.read_text(encoding='utf-8'),object_pairs_hook=objeto_sem_repeticoes)
                if not isinstance(raw,dict) or set(raw)!={'versoes','respostas'} or raw['versoes']!=versoes(cases): raise ValueError()
                rows=raw['respostas']
                if not isinstance(rows,list) or len(rows)!=len(cases) or any(not isinstance(r,dict) or set(r)!={'caso','resposta_api'} for r in rows): raise ValueError()
                ids=[r['caso'] for r in rows]
                if len(set(ids))!=len(ids) or set(ids)!={c['id'] for c in cases}: raise ValueError()
            except Exception: raise CommandError('Arquivo fora do contrato, versão antiga, omisso ou excessivo. Nenhum conteúdo aplicado ou enviado.') from None
            results=[]
            for case in cases:
                row=next(r for r in rows if r['caso']==case['id'])
                try: result=avaliar_caso(case,ProvedorReal.interpretar_resposta(row['resposta_api']).model_dump())
                except Exception: result={'estado':'reprovado','erros':['envelope_recusado_incompleto_ou_invalido']}
                results.append({'caso':case['id'],**result})
            report={'modo':'verificacao_offline_de_respostas_fornecidas','avaliacao_real':'nao_executada_por_este_comando',
                    'origem_das_respostas':'nao_atestada','versoes':versoes(cases),'resultados':results,
                    'resultado':'reprovado' if any(r['erros'] for r in results) else 'sem_erros_nos_casos_fornecidos',
                    'aviso':'Não é homologação profissional ou aprovação de modelo real. Dados do caso não foram alterados.'}
        with destination.open('x',encoding='utf-8') as output: json.dump(report,output,ensure_ascii=False,indent=2)
        self.stdout.write('Relatório offline salvo. Nenhuma chamada externa; IA real não avaliada por este comando.')
        if report.get('resultado')=='reprovado': raise CommandError('Há falhas nas respostas fornecidas; consulte os códigos do relatório.')
