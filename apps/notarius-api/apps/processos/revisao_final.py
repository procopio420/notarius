"""Human final-review records are bound to the exact immutable saved text."""
import hashlib

def hash_texto(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def registro_final(minuta):
    record = getattr(minuta, 'revisao_final', None)
    if not record:
        return None
    return {'id':str(record.id), 'autor_nome':record.autor.get_full_name() or record.autor.username,
            'created_at':record.created_at, 'motivo':record.motivo,
            'texto_corresponde':record.texto_sha256 == hash_texto(minuta.corpo)}
