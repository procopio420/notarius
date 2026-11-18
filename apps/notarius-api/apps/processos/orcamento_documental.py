"""Persistent, conservative pilot budget. Does not enable or perform API calls.

The future transport must reserve BEFORE each attempt, with SDK retries disabled.
Reservations are never refunded, including timeouts and failures. Prices must be
reviewed before activation; this is not an account-wide billing guarantee.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


class OrcamentoBloqueado(Exception):
    pass


MODELO = 'gpt-6-luna'
TETO_CENTAVOS = 50  # US$ .50 cumulative; no automatic monthly reset.
RESERVA_CENTAVOS = 5  # At most ten small attempts, including failures.
MAX_BYTES_TESTE = 32000
MAX_TOKENS_SAIDA_TESTE = 4000


def validar_requisicao(requisicao):
    # Allow only the plain text extraction request, without paid tools, images,
    # conversations, priority tiers or other unbounded additional inputs.
    required = {'model', 'store', 'max_output_tokens', 'input', 'text'}
    if not isinstance(requisicao, dict) or set(requisicao) != required:
        raise OrcamentoBloqueado('Formato de requisição não autorizado para o orçamento piloto.')
    if requisicao['model'] != MODELO or requisicao['store'] is not False:
        raise OrcamentoBloqueado('Somente GPT-6 Luna sem armazenamento é permitido.')
    tokens = requisicao['max_output_tokens']
    if type(tokens) is not int or not 1 <= tokens <= MAX_TOKENS_SAIDA_TESTE:
        raise OrcamentoBloqueado('Limite de saída inválido.')
    messages = requisicao['input']
    if not isinstance(messages, list) or len(messages) != 2:
        raise OrcamentoBloqueado('Somente extração de texto é permitida.')
    for message, role in zip(messages, ('system', 'user')):
        if (not isinstance(message, dict) or set(message) != {'role', 'content'}
                or message['role'] != role or not isinstance(message['content'], str)):
            raise OrcamentoBloqueado('Somente extração de texto é permitida.')
    try:
        size = len(json.dumps(requisicao, ensure_ascii=False, allow_nan=False).encode('utf-8'))
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise OrcamentoBloqueado('Requisição inválida.') from None
    # Stay below Luna's 272K long-context threshold even with conservative
    # one-token-per-byte counting and overhead. At current standard rates,
    # 32K input + 4K output costs US$ .0052, below the US$ .05 reservation.
    if size > MAX_BYTES_TESTE:
        raise OrcamentoBloqueado('Texto grande demais para o teste econômico; divida os documentos.')


def reservar(requisicao, arquivo=None):
    """Commit US$ .05 before an attempt. Missing/corrupt ledger fails closed.

    Initialize the ledger explicitly using criar_registro(). Never create it
    automatically: deleting/moving a ledger must not silently reset spending.
    No document text, key or provider response is stored here.
    """
    validar_requisicao(requisicao)
    path = _caminho(arquivo)
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=20)) as connection, connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT reservado FROM orcamento WHERE id=1').fetchone()
            if row is None or type(row[0]) is not int or row[0] < 0:
                raise OrcamentoBloqueado('Registro de orçamento inválido; nenhum envio permitido.')
            if row[0] + RESERVA_CENTAVOS > TETO_CENTAVOS:
                raise OrcamentoBloqueado('Teto de US$ 0,50 dos testes atingido; nenhum novo envio permitido.')
            connection.execute('UPDATE orcamento SET reservado=? WHERE id=1',
                               (row[0] + RESERVA_CENTAVOS,))
            return row[0] + RESERVA_CENTAVOS
    except sqlite3.Error:
        raise OrcamentoBloqueado('Registro de orçamento indisponível; nenhum envio permitido.') from None


def _caminho(arquivo):
    if arquivo is None:
        from django.conf import settings
        arquivo = Path(settings.BASE_DIR).parent.parent / '.local' / 'orcamento-ia.sqlite3'
    return Path(arquivo).resolve()


def criar_registro(arquivo=None):
    """Explicit first-time initialization; refuses to replace an existing file."""
    path = _caminho(arquivo)
    with path.open('xb'):
        pass
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute('CREATE TABLE orcamento (id INTEGER PRIMARY KEY CHECK(id=1), reservado INTEGER NOT NULL)')
        connection.execute('INSERT INTO orcamento VALUES (1, 0)')
