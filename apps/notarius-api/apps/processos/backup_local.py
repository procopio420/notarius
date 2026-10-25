"""Encrypted, consistent SQLite backups for the local pilot only."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import time
from contextlib import closing
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b'NOTARIUS-BKP1\x00'
MAX_DB = 512 * 1024 * 1024
TABLES = {
    'atendimentos':'processos_atendimento', 'mensagens':'processos_mensagematendimento',
    'anexos':'processos_anexoatendimento', 'paginas':'processos_paginaanexoatendimento',
    'ficha':'processos_revisaodadoatendimento', 'modelos':'processos_modeloatendimento',
    'minutas':'processos_minutaatendimento', 'revisoes_finais':'processos_revisaofinalminuta',
    'biblioteca':'processos_modeloreutilizavel', 'organizacao':'processos_historicoorganizacaoatendimento',
}
OPTIONAL_TABLES = {'analises_documentais':'processos_analisedocumentalatendimento', 'organizacoes_anexos':'processos_organizacaoanexoatendimento', 'vinculacoes_minuta':'processos_vinculacaominutaatendimento', 'pendencias_ficha':'processos_pendenciafichaatendimento', 'historico_pendencias_ficha':'processos_historicopendenciaficha', 'feedbacks_teste':'processos_feedbacktesteatendimento',
                   'objetos_ficha':'processos_objetofichaatendimento', 'eventos_ficha':'processos_eventofichaatendimento',
                   'propostas_dados':'processos_propostadadoatendimento', 'decisoes_propostas':'processos_decisaopropostaatendimento'}

class BackupInvalido(Exception):
    pass

def key(password, salt):
    if not isinstance(password,str) or not 12 <= len(password) <= 1024:
        raise BackupInvalido('A senha precisa ter entre 12 e 1024 caracteres.')
    return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode('utf-8'))

def inspect_database(connection):
    connection.execute('PRAGMA trusted_schema=OFF')
    connection.execute('PRAGMA query_only=ON')
    if connection.execute('PRAGMA integrity_check').fetchmany(2) != [('ok',)]:
        raise BackupInvalido('A cópia do banco não passou na verificação de integridade.')
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not set(TABLES.values()).issubset(tables):
        raise BackupInvalido('O banco não contém a estrutura esperada deste piloto.')
    counted = {**TABLES, **{name:table for name,table in OPTIONAL_TABLES.items() if table in tables}}
    return {name:connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for name,table in counted.items()}

def make_backup(source, password):
    source = Path(source).resolve()
    if not source.is_file() or source.stat().st_size > MAX_DB:
        raise BackupInvalido('Banco ausente ou acima do limite de 512 MiB do backup local.')
    deadline = time.monotonic()+30
    page_size = 4096
    def progress(status, remaining, total):
        if total*page_size > MAX_DB:
            raise BackupInvalido('Cópia acima do limite de 512 MiB.')
        if time.monotonic() > deadline:
            raise BackupInvalido('O banco permaneceu ocupado. Tente novamente com o servidor parado.')
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=5)) as origin:
        page_size = origin.execute('PRAGMA page_size').fetchone()[0]
        if page_size*origin.execute('PRAGMA page_count').fetchone()[0] > MAX_DB:
            raise BackupInvalido('Cópia acima do limite de 512 MiB.')
        with closing(sqlite3.connect(':memory:')) as copy:
            origin.backup(copy,pages=256,progress=progress,sleep=0.05)
            counts = inspect_database(copy)
            data = copy.serialize()
    # SQLite's documented deserialize workaround for a serialized WAL snapshot.
    # Only the completed backup copy is normalized; the active database is untouched.
    if data[18:20] == b'\x02\x02':
        data = data[:18]+b'\x01\x01'+data[20:]
    if len(data) > MAX_DB:
        raise BackupInvalido('Cópia acima do limite de 512 MiB.')
    manifest = {'formato':1,'criado_em':datetime.now(timezone.utc).isoformat(),
                'banco_sha256':hashlib.sha256(data).hexdigest(), 'contagens':counts,
                'escopo':'Banco SQLite inteiro: todos os cartórios, usuários e anexos armazenados no banco. Não inclui .env, código, mídia externa ou arquivos exportados.'}
    metadata = json.dumps(manifest,ensure_ascii=False).encode('utf-8')
    payload = struct.pack('>I',len(metadata))+metadata+data
    salt, nonce = os.urandom(16),os.urandom(12)
    encrypted = AESGCM(key(password,salt)).encrypt(nonce,payload,MAGIC)
    return MAGIC+salt+nonce+encrypted, manifest

def read_backup(data,password):
    if len(data) > MAX_DB+65536 or not data.startswith(MAGIC) or len(data) < len(MAGIC)+44:
        raise BackupInvalido('Formato ou tamanho de backup inválido.')
    offset = len(MAGIC)
    try:
        payload = AESGCM(key(password,data[offset:offset+16])).decrypt(data[offset+16:offset+28],data[offset+28:],MAGIC)
        length = struct.unpack('>I',payload[:4])[0]
        if not 1 <= length <= 32768:
            raise ValueError()
        metadata = json.loads(payload[4:4+length])
        database = payload[4+length:]
        if metadata['formato'] != 1 or metadata['banco_sha256'] != hashlib.sha256(database).hexdigest():
            raise ValueError()
        if not database.startswith(b'SQLite format 3\x00') or len(database) > MAX_DB:
            raise ValueError()
        with closing(sqlite3.connect(':memory:')) as copy:
            copy.deserialize(database)
            counts = inspect_database(copy)
        if counts != metadata['contagens']:
            raise ValueError()
        return database, metadata
    except Exception:
        raise BackupInvalido('Senha incorreta, arquivo alterado ou backup inválido. Nenhum banco foi substituído.') from None

def write_new(path,data):
    path = Path(path).resolve()
    # Exclusive creation guarantees no existing backup/database is overwritten.
    with path.open('xb') as output:
        try:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        except Exception:
            output.close()
            path.unlink(missing_ok=True)
            raise
