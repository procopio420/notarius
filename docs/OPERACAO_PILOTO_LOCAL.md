# Operação local do piloto

Etapa 2 operacional solicitada em 25/10/2026. Não corresponde à etapa histórica de parametrização do padrão. Escopo: preparar o equipamento atual, sem homologar modelo/cenário ou realizar atendimento no lugar da escrevente.

## Iniciar e acessar

Abra um PowerShell na pasta deste projeto e execute:

```powershell
.\scripts\iniciar-piloto-local.ps1
```

Acesse **http://localhost:3002/atendimentos**. Use a conta existente, com sua senha, e confira o cartório selecionado antes de abrir ou criar um atendimento. Nenhuma senha de usuário foi alterada. Não use contas compartilhadas entre pessoas. Se a senha tiver sido esquecida, o responsável local pode executar o comando administrativo abaixo no próprio equipamento, substituindo o nome da conta; a senha é pedida no terminal, sem aparecer na tela:

```powershell
.\.venv\Scripts\python.exe apps/notarius-api/manage.py changepassword NOME_DA_CONTA --settings=config.settings_piloto
```

O iniciador confere dependências instaladas, exclusão do banco do Git, integridade/estrutura SQLite, configuração e migrações aplicadas; espera a API e a página de login responderem. Não instala dependências nem aplica migrações automaticamente. Se as portas estiverem ocupadas, encerre pelo procedimento abaixo e tente novamente. Processo de outro projeto é recusado, sem encerramento automático.

O endereço da API é `http://localhost:8002`, reservado ao uso local. Ambos os serviços escutam somente em `127.0.0.1`. Não configure redirecionamento de portas, túnel, proxy público ou compartilhamento remoto.

O atalho anterior `iniciar-teste-local.ps1` passou a chamar esse mesmo iniciador. Use sempre o perfil `config.settings_piloto` para os comandos administrativos desta operação.

## Salvar, sair e voltar

1. Aguarde a confirmação de salvamento de cada mensagem, dado ou anexo. Texto ainda no formulário não equivale a dado salvo.
2. Confira o atendimento e o cartório. Documentos recebidos, texto OCR e propostas não são confirmações profissionais.
3. Ao terminar, saia da conta pelo menu do usuário. Para encerrar os serviços, execute:

```powershell
.\scripts\encerrar-piloto-local.ps1
```

4. Feche a aba. Para retomar, inicie novamente e abra o atendimento salvo na lista. O encerramento preserva banco/anexos; requisição interrompida antes de completar pode não ter sido salva. Confira seu estado antes de repetir uma operação.

O navegador guarda token de acesso e rascunhos locais/de sessão. Use perfil de navegador e conta Windows exclusivos da pessoa autorizada; bloquear a tela é necessário. Encerrar o servidor não apaga esses dados do navegador. Rascunhos não substituem backup.

## Onde ficam os dados

- Sem seleção explícita anterior, continua em uso `apps/notarius-api/db.sqlite3`, preservado nesta etapa.
- A seleção explícita fica no arquivo privado `.local/piloto-banco.txt`. O iniciador usa esse caminho nas próximas execuções. A variável `NOTARIUS_PILOTO_DB` é usada somente em comandos/ensaios deliberadamente configurados; o iniciador fixa o banco selecionado e não herda uma substituição acidental.
- **Anexos originais, páginas extraídas, OCR e dados do atendimento ficam no banco**, não em uma pasta de uploads. O backup SQLite inclui esses registros e todos os cartórios/usuários desse banco.
- Segredo de sessão local: `.local/piloto-secret.key`, criado uma única vez. Credenciais existentes permanecem nos arquivos `.env` ignorados; não copie seus valores para documentação ou mensagens.
- Logs de inicialização: `.local/logs/piloto/`. O perfil da API descarta logs de requisição/exceções, sem imprimir corpos, cabeçalhos ou parâmetros de busca. Login e tratamento global de falhas da interface não imprimem objetos de erro no modo piloto. Isso reduz o diagnóstico em casos reais: reproduza problemas com dados fictícios antes de habilitar qualquer instrumentação.
- Exportações devem ser salvas em pasta privada, por exemplo `.local/exportacoes/`, criada pelo operador. Documentos recebidos também devem permanecer em `.local` ou fora do repositório. Não coloque documentos reais em `docs/`.

Git ignora `.local`, bancos SQLite e seus arquivos auxiliares, `.env` (exceto exemplos), logs, chaves e backups `.notarius`. Os comandos de backup/restauração recusam destinos rastreados ou não ignorados dentro de um repositório Git. Ignorar um arquivo não protege seu acesso pelo Windows nem remove uma inclusão histórica; não use `git add -f` para esses arquivos.

## Backup

Ao final de cada sessão e antes de migrações ou troca de banco, execute:

```powershell
.\.venv\Scripts\python.exe scripts/backup-local.py
```

Também é possível abrir `scripts/Fazer backup local.cmd`. Informe e confirme uma senha de pelo menos 12 caracteres no terminal. Não envie essa senha pelo chat. O arquivo novo `.notarius` fica em `.local/backups/`, criptografado com AES-GCM e chave derivada com scrypt. Guarde a senha separadamente: não existe recuperação de senha. Nenhum arquivo de backup anterior é sobrescrito.

O mecanismo usa a API de backup SQLite e verifica integridade. Pode funcionar com o banco aberto; para a rotina simples, termine de salvar e encerre os serviços primeiro. O limite atual é 512 MiB por banco, e a operação usa memória para construir/criptografar a cópia. Acima desse limite, não há backup disponível por esse mecanismo.

Copie periodicamente o backup criptografado para uma unidade local separada autorizada e confira sua leitura. Uma cópia no mesmo disco não protege contra perda do equipamento. Não foi configurada sincronização ou cópia em nuvem.

O backup **não inclui** `.env`, segredo local, código/dependências, arquivos exportados ou mídia dos módulos legados. Preserve esses itens separadamente em armazenamento privado se necessários à recuperação do equipamento. Não use este procedimento como backup de S3/MinIO ou PostgreSQL.

## Restaurar sem sobrescrever

Escolha um nome de banco novo em uma pasta privada existente. Exemplo com nomes genéricos; substitua o nome do backup pelo arquivo efetivo:

```powershell
.\scripts\restaurar-piloto-local.ps1 -Arquivo .local\backups\NOME_DO_BACKUP.notarius -Destino .local\recuperado.sqlite3
```

Informe a senha localmente. Senha incorreta, alteração do arquivo, estrutura inválida, destino existente ou banco ativo como destino são recusados. A restauração cria uma cópia **sem criptografia** e não muda a seleção do banco em uso.

Para conferir e passar a utilizar a cópia recuperada:

```powershell
.\scripts\encerrar-piloto-local.ps1
.\scripts\iniciar-piloto-local.ps1 -Banco .local\recuperado.sqlite3
```

Entre com a conta que existia no momento do backup; confira atendimento, mensagens e download dos originais. A seleção fica persistida. O banco anterior permanece intacto. Para voltar a ele, encerre e use `-Banco` com seu caminho anterior. Não copie banco por cima de outro, nem remova arquivos WAL/journal manualmente. A restauração não mescla alterações posteriores ao backup.

## Evidência e limites

O ensaio `scripts/verificar-piloto-local.py` cria bancos **exclusivamente fictícios** dentro de `.local/verificacao-piloto/`, executa migrações nesse destino separado, inicia uma API em porta loopback livre, autentica via HTTP, salva atendimento/mensagem/anexo, encerra/reinicia o processo, reabre, cria backup criptografado e restaura em outro arquivo. Depois abre essa cópia em outro processo e compara os dados e bytes do original. A entrada de senha é simulada somente nesse ensaio automatizado; os comandos reais de backup/restauração e a criptografia são exercitados. O ensaio não altera a seleção operacional.

Resultado desta execução e verificações estão em [Continuidade](CONTINUIDADE_PILOTO_REAL.md). A conferência HTTP da página de login não substitui avaliação visual do navegador pela escrevente. Nenhum atendimento real foi confirmado, revisado ou exportado nesta etapa.

O ambiente permanece com Next em desenvolvimento e Django runserver; não é uma instalação de produção. Rotas da API fora de atendimento e acesso à conta ficam indisponíveis neste perfil. A política de conteúdo do navegador limita conexões a endereços locais; não é um bloqueio de rede do Windows. IA documental continua bloqueada, sem autorização ou transporte externo novo.

A inspeção limitada de ACLs não encontrou permissões explícitas para os grupos amplos examinados nos quatro caminhos conferidos; a herança permanece habilitada. Não houve auditoria integral de usuários/grupos, criptografia de disco, malware, extensões de navegador, sincronização do diretório Documentos ou permissões de todos os arquivos. O responsável precisa manter o equipamento e os destinos privados, verificar eventual sincronização automática e controlar o acesso à conta Windows antes de inserir material real. O banco operacional não foi migrado ou substituído.
