# Etapa 9 — OCR local e revisão da leitura

Implementado em 24/10/2026. PNG, JPG e páginas digitalizadas de PDF passam por OCR do Windows em português, dentro do processo local. Não usa serviço externo nem chave de IA. O arquivo original continua no armazenamento privado do atendimento.

## Como testar

1. Anexe uma imagem ou PDF fictício em um atendimento.
2. Abra **Conferir leitura**, depois **Ver página para conferir**.
3. Selecione uma linha reconhecida para localizar sua posição na imagem. **Usar linha** abre a revisão da ficha; confira o original antes de confirmar qualquer dado.
4. Use **Ler novamente** para criar outra versão da leitura. As páginas anteriores e as fontes das revisões permanecem no histórico. A nova leitura exige nova conferência e torna a minuta anterior desatualizada.

## Limites e comportamento seguro

- OCR pode errar ou omitir nomes, números e trechos. Não fornece pontuação de confiança e não confirma dados automaticamente.
- Texto nativo e OCR ficam separados; diferenças nos campos reconhecidos aparecem na conferência. Isto não é uma comparação semântica completa de todos os documentos.
- Até 40 páginas de PDF, com OCR em até 10 páginas por leitura. Páginas excedentes recebem aviso explícito.
- Imagens limitadas a 25 milhões de pixels e reduzidas para até 3200 pixels por dimensão. Há limites de tempo; falhas deixam pendência para revisão.
- Requer Windows e o idioma OCR pt-BR instalado. Outros ambientes interrompem a leitura OCR com aviso; a extração de texto nativo continua disponível.
- Páginas privadas exigem autenticação e vínculo ao cartório. Respostas de imagem usam no-store.
- O uso continua sendo piloto acompanhado: ainda falta homologar o modelo da escritura e implementar/validar interpretação mais ampla da conversa.

## Verificação

38 testes Django passaram, incluindo OCR real de PNG/JPG, PDF misto, coordenadas, isolamento de acesso, divergências, indisponibilidade, timeout, limite de páginas e preservação do histórico na releitura. ESLint passou nos componentes de atendimento e cliente da API.
