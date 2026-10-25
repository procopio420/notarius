# Etapa 7 — teste acompanhado

Avaliação realizada em 24/10/2026. O fluxo de atendimento foi liberado apenas para teste funcional acompanhado com dados fictícios, neste computador.

## Evidências

- Suíte Django de atendimentos: 32 testes aprovados.
- Teste integrado HTTP com conta nova: 12 verificações aprovadas, desde autenticação até revisão, edição, Word/PDF e nova preparação após divergência.
- Lint dos arquivos novos aprovado após corrigir a resolução de plugins do ESLint no pnpm.
- A verificação global de TypeScript continua com erros anteriores em áreas fora do fluxo. Os arquivos do fluxo não apresentaram erros no filtro usado.
- A conta da tester foi criada sem administração, em um cartório fictício separado. Nenhuma senha ou token foi incluído neste documento ou nos arquivos versionados.
- Login pela interface conferido com a conta da escrevente: dois atendimentos fictícios visíveis e seletor mostrando somente o cartório autorizado.
- Script de inicialização validado sintaticamente e executado com os serviços existentes, sem encerrá-los ou criar serviços duplicados.

O teste integrado comprovou persistência, reenvio sem duplicação, download idêntico ao anexo, confirmação humana, bloqueio por modelo em rascunho, edição com histórico, texto exportado, divergência nova, bloqueio das exportações antigas e recusa de acesso a outro cartório. Resultado detalhado local em `.local/resultado-etapa7.json`.

## Material da tester

A pasta `docs/teste-escrevente/` contém o roteiro, três arquivos fictícios e um formulário de feedback. Há dois atendimentos preparados: um vazio para executar o roteiro e um exemplo com o percurso concluído e histórico das verificações.

Uma cópia compactada desse material foi preparada em `.local/pacote-teste-escrevente.zip`, sem credenciais.

O login passa a abrir Atendimentos diretamente. A troca de usuário limpa a seleção anterior de cartório e os tokens locais; o seletor carrega os cartórios vinculados ao usuário em vez de listar todos os cartórios.

Se os servidores forem encerrados, `scripts/iniciar-teste-local.ps1` inicia o ambiente já instalado. Não instala dependências, não abre firewall, não encerra processos de outros projetos nem publica o sistema. O acesso em outro computador ainda precisa ser preparado separadamente.

## O que ainda impede uso com clientes

- Sem interpretação semântica geral dos documentos: a conferência automática reconhece apenas campos explícitos e encaminha o restante à revisão humana.
- Sem OCR: imagens e páginas escaneadas exigem leitura manual.
- Modelo profissional completo precisa ser fornecido e revisado pela escrevente.
- Word teve validação de conteúdo, mas não visual de paginação; o conversor não está instalado neste ambiente. PDF foi inspecionado visualmente.
- Servidores de desenvolvimento, armazenamento local, sem rotina operacional de backup e sem implantação para outro computador.
- Outras páginas e geradores anteriores ao novo fluxo não foram liberados por este teste.

Este piloto permite avaliar a organização do trabalho e os controles. Ainda não comprova redução de tempo em uma escritura real nem a confiabilidade de uma IA notarial completa.
