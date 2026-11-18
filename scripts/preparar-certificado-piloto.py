from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
import plistlib
import secrets
import sys
import uuid

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


address = IPv4Address(sys.argv[1])
if not any(address in IPv4Network(block) for block in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
    raise SystemExit('Informe o endereço IPv4 privado do computador.')

folder = Path(__file__).resolve().parents[1] / '.local' / 'piloto-rede' / str(address)
folder.mkdir(parents=True, exist_ok=True)
profile_path = folder / 'notarius.mobileconfig'
server_cert = folder / 'servidor.pem'
server_key = folder / 'servidor.key'
root_cert = folder / 'autoridade.pem'
now = datetime.now(timezone.utc)

if all(path.is_file() for path in (profile_path, server_cert, server_key, root_cert)):
    existing = x509.load_pem_x509_certificate(server_cert.read_bytes())
    if existing.not_valid_after_utc > now + timedelta(days=1):
        raise SystemExit(0)

authority_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = f'Notarius local {secrets.token_hex(3).upper()}'
authority_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, str(address))])


def certificate(subject_name, issuer_name, public_key):
    return (x509.CertificateBuilder().subject_name(subject_name).issuer_name(issuer_name)
            .public_key(public_key).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=10)))


authority = (certificate(authority_name, authority_name, authority_key.public_key())
             .not_valid_after(now + timedelta(days=91))
             .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
             .add_extension(x509.SubjectKeyIdentifier.from_public_key(authority_key.public_key()), critical=False)
             .sign(authority_key, hashes.SHA256()))
leaf = (certificate(subject, authority_name, key.public_key())
        .not_valid_after(now + timedelta(days=90))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(address)]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(authority_key.public_key()), critical=False)
        .sign(authority_key, hashes.SHA256()))

root_cert.write_bytes(authority.public_bytes(serialization.Encoding.PEM))
server_cert.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
server_key.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption()))
profile_path.write_bytes(plistlib.dumps({
    'PayloadType': 'Configuration', 'PayloadVersion': 1,
    'PayloadIdentifier': f'local.notarius.{address}', 'PayloadUUID': str(uuid.uuid4()),
    'PayloadDisplayName': name,
    'PayloadContent': [{
        'PayloadType': 'com.apple.security.root', 'PayloadVersion': 1,
        'PayloadIdentifier': f'local.notarius.{address}.ca', 'PayloadUUID': str(uuid.uuid4()),
        'PayloadDisplayName': name, 'PayloadCertificateFileName': 'Notarius.cer',
        'PayloadContent': authority.public_bytes(serialization.Encoding.DER),
    }],
}))
