from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from contextlib import closing
import sqlite3
import subprocess
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command, CommandError
from apps.processos.backup_local import make_backup, read_backup, write_new, BackupInvalido, TABLES, conferir_destino_privado

PASSWORD='Senha inteiramente fictícia 2026!'

class BackupLocalTests(SimpleTestCase):
    def test_outputs_must_be_ignored_and_untracked_inside_git(self):
        with TemporaryDirectory() as root:
            subprocess.run(['git', 'init', '--quiet', root], check=True, capture_output=True)
            folder = Path(root)
            (folder / '.gitignore').write_text('*.notarius\n*.sqlite3\n', encoding='utf-8')
            conferir_destino_privado(folder / 'copia.notarius')
            conferir_destino_privado(folder / 'recuperado.sqlite3')
            with self.assertRaises(BackupInvalido):
                conferir_destino_privado(folder / 'documento.txt')
            tracked = folder / 'rastreado.sqlite3'
            tracked.write_bytes(b'FICTICIO')
            subprocess.run(['git', '-C', root, 'add', '-f', 'rastreado.sqlite3'], check=True, capture_output=True)
            with self.assertRaises(BackupInvalido):
                conferir_destino_privado(tracked)

    def fixture(self,root):
        path=Path(root)/'ficticio.sqlite3'
        with closing(sqlite3.connect(path)) as db:
            db.execute('PRAGMA journal_mode=WAL')
            for table in TABLES.values(): db.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
            db.execute('INSERT INTO processos_atendimento VALUES (1)')
            db.execute('CREATE TABLE evidencia_ficticia (texto TEXT, arquivo BLOB)')
            db.execute('INSERT INTO evidencia_ficticia VALUES (?,?)',('TEXTO FICTÍCIO <teste> & acentos',b'\x00\xffFICTICIO\r\n'))
            db.commit()
        return path

    def test_encrypted_roundtrip_preserves_text_and_binary_and_never_overwrites(self):
        with TemporaryDirectory() as root:
            source=self.fixture(root)
            encrypted,metadata=make_backup(source,PASSWORD)
            self.assertNotIn(b'TEXTO FICT',encrypted)
            self.assertEqual(metadata['contagens']['atendimentos'],1)
            recovered,verified=read_backup(encrypted,PASSWORD)
            self.assertEqual(metadata,verified)
            destination=Path(root)/'recuperado.sqlite3'
            write_new(destination,recovered)
            with closing(sqlite3.connect(destination)) as db:
                row=db.execute('SELECT texto,arquivo FROM evidencia_ficticia').fetchone()
            self.assertEqual(row,('TEXTO FICTÍCIO <teste> & acentos',b'\x00\xffFICTICIO\r\n'))
            with self.assertRaises(FileExistsError): write_new(destination,b'do not overwrite')
            self.assertEqual(destination.read_bytes(),recovered)

    def test_wrong_password_tampering_and_invalid_file_are_rejected(self):
        with TemporaryDirectory() as root:
            encrypted,_=make_backup(self.fixture(root),PASSWORD)
            for data,password in [(encrypted,'Outra senha fictícia 2026!'),(encrypted[:-1]+bytes([encrypted[-1]^1]),PASSWORD),(b'invalid',PASSWORD)]:
                with self.subTest(size=len(data)), self.assertRaises(BackupInvalido): read_backup(data,password)
            with self.assertRaises(BackupInvalido): make_backup(Path(root)/'missing',PASSWORD)
            with self.assertRaises(BackupInvalido): make_backup(Path(root)/'ficticio.sqlite3','short')

    def test_backup_includes_committed_wal_records_while_database_is_open(self):
        with TemporaryDirectory() as root:
            source=self.fixture(root)
            with closing(sqlite3.connect(source)) as writer:
                writer.execute('INSERT INTO processos_atendimento VALUES (2)')
                writer.commit()
                self.assertTrue(Path(str(source)+'-wal').exists())
                encrypted,_=make_backup(source,PASSWORD)
                restored,manifest=read_backup(encrypted,PASSWORD)
                self.assertEqual(manifest['contagens']['atendimentos'],2)
                self.assertEqual(restored[18:20],b'\x01\x01')

    def test_commands_verify_and_recover_separate_copy_without_touching_active_database(self):
        with TemporaryDirectory() as root:
            source=self.fixture(root)
            backup=Path(root)/'copia.notarius'
            destination=Path(root)/'recuperado.sqlite3'
            config={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(source)}}
            with override_settings(DATABASES=config), patch('apps.processos.management.commands.backup_local.getpass',return_value=PASSWORD):
                call_command('backup_local',saida=str(backup),stdout=StringIO())
            before=source.read_bytes()
            with override_settings(DATABASES=config), patch('apps.processos.management.commands.conferir_backup_local.getpass',return_value=PASSWORD):
                call_command('conferir_backup_local',arquivo=str(backup),stdout=StringIO())
                self.assertFalse(destination.exists())
                with self.assertRaises(CommandError):
                    call_command('conferir_backup_local',arquivo=str(backup),recuperar_em=str(source),stdout=StringIO())
                call_command('conferir_backup_local',arquivo=str(backup),recuperar_em=str(destination),stdout=StringIO())
            self.assertTrue(destination.exists())
            self.assertEqual(source.read_bytes(),before)

    def test_confirmation_mismatch_and_existing_destination_do_not_create_or_replace_backup(self):
        with TemporaryDirectory() as root:
            source=self.fixture(root)
            backup=Path(root)/'copia.notarius'
            config={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(source)}}
            with override_settings(DATABASES=config), patch('apps.processos.management.commands.backup_local.getpass',side_effect=[PASSWORD,'Diferente']):
                with self.assertRaises(CommandError): call_command('backup_local',saida=str(backup),stdout=StringIO())
            self.assertFalse(backup.exists())
            backup.write_bytes(b'EXISTENTE')
            with override_settings(DATABASES=config), patch('apps.processos.management.commands.backup_local.getpass') as prompt:
                with self.assertRaises(CommandError): call_command('backup_local',saida=str(backup),stdout=StringIO())
                prompt.assert_not_called()
            self.assertEqual(backup.read_bytes(),b'EXISTENTE')

    def test_optional_feedback_records_are_preserved_and_counted_without_rejecting_older_backups(self):
        with TemporaryDirectory() as root:
            source=self.fixture(root)
            old_backup,_=make_backup(source,PASSWORD)
            self.assertNotIn('feedbacks_teste',read_backup(old_backup,PASSWORD)[1]['contagens'])
            with closing(sqlite3.connect(source)) as db:
                db.execute('CREATE TABLE processos_feedbacktesteatendimento (id INTEGER PRIMARY KEY, descricao TEXT)')
                db.execute('INSERT INTO processos_feedbacktesteatendimento VALUES (1,?)',('RELATO FICTÍCIO',))
                db.commit()
            new_backup,_=make_backup(source,PASSWORD)
            restored,manifest=read_backup(new_backup,PASSWORD)
            self.assertEqual(manifest['contagens']['feedbacks_teste'],1)
            self.assertNotIn('feedbacks_teste',read_backup(old_backup,PASSWORD)[1]['contagens'])
            self.assertIn('RELATO FICTÍCIO'.encode('utf-8'),restored)
