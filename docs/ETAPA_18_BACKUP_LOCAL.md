# Etapa 18 — backup local criptografado

Disponível para o piloto SQLite local, sem API externa. Não substitui a rotina de backup de uma implantação PostgreSQL/produção.

## Criar com dois cliques

1. Abra a pasta `scripts` do projeto.
2. Execute **Fazer backup local.cmd**.
3. Digite uma senha de pelo menos 12 caracteres e repita. Ela não aparece na tela e não é passada por argumento, salva no projeto ou enviada por rede.
4. Aguarde a confirmação. O arquivo `.notarius` é salvo em `.local/backups`, com nome único.
5. Guarde a senha separadamente. Sem ela, não há recuperação da cópia.

Nenhum backup real foi criado automaticamente nesta entrega: a criação depende da senha escolhida por você no terminal. Os testes usaram somente bancos temporários fictícios.

## Escopo

A cópia inclui o banco SQLite INTEIRO, com todos os cartórios, usuários, registros de autenticação, conversas, anexos binários, leituras, ficha, modelos, biblioteca, minutas e revisões finais. Não é um backup individual de cartório.

Não inclui `.env`, a chave OpenAI guardada nesse arquivo, código, dependências, arquivos de mídia externos ao banco ou arquivos Word/PDF/TXT já baixados. Para recuperar o sistema completo, também é necessário preservar o código/configuração compatíveis por meios apropriados.

O arquivo é cifrado com AES-256-GCM, com chave derivada da senha via scrypt e sal/nonce aleatórios. Não há arquivo temporário de banco sem criptografia na criação/verificação. A cópia é feita pela API de backup do SQLite, incluindo transações já confirmadas no WAL; não é uma cópia simples do arquivo aberto. Antes da criptografia são conferidas a integridade e as contagens dos registros do piloto.

Limite desta ferramenta: banco de até 512 MiB; usa memória para montar a cópia. Uma espera por banco ocupado tem limite de tempo e pede nova tentativa com o servidor parado. Arquivos existentes nunca são sobrescritos.

## Criar pelo PowerShell

A partir da raiz do projeto, com uma pasta de destino existente:

```powershell
& .venv/Scripts/python.exe apps/notarius-api/manage.py backup_local --saida .local/meu-backup.notarius
```

Escolha um nome novo em cada execução. O atalho de dois cliques gera nomes novos automaticamente.

## Verificar a cópia

```powershell
& .venv/Scripts/python.exe apps/notarius-api/manage.py conferir_backup_local --arquivo .local/meu-backup.notarius
```

Digite a senha. A ferramenta verifica autenticação criptográfica, hash do banco, integridade SQLite e contagens. A saída mostra a data UTC e quantidades, sem listar conteúdo pessoal. Nenhum banco é gravado nesse modo.

## Recuperar um banco separado

```powershell
& .venv/Scripts/python.exe apps/notarius-api/manage.py conferir_backup_local --arquivo .local/meu-backup.notarius --recuperar-em .local/banco-recuperado.sqlite3
```

A recuperação exige um arquivo NOVO e recusa substituir o banco ativo ou qualquer arquivo existente. O banco recuperado contém os dados sem criptografia: proteja-o como o banco original. A troca do banco usado pelo aplicativo não é automática; antes de qualquer troca, pare os servidores, preserve o banco atual e confira a cópia recuperada com a versão compatível do projeto.

Manter o backup somente no mesmo disco não protege contra falha/perda desse disco. Você pode guardar outra cópia do arquivo criptografado em mídia separada, mantendo a senha em local seguro. A ferramenta não envia cópias à nuvem nem agenda backups nesta entrega.

## Verificação da entrega

73 testes anteriores e cinco de backup passaram. Os cinco casos verificam recuperação exata de texto/binário, senha errada/arquivo adulterado, recuperação em arquivo novo sem tocar o ativo, recusa de sobrescrita e cópia de registros confirmados em WAL com banco aberto. A suíte de 77 testes passou; depois foi acrescentado e passou o teste adicional de WAL, junto aos outros quatro de backup.

A normalização do cabeçalho da cópia WAL segue a [documentação SQLite de desserialização](https://www.sqlite.org/c3ref/deserialize.html). Isso é aplicado apenas à cópia concluída, nunca ao banco ativo.
