from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta

def generate_ssl():
    # Generate a new private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Create a certificate signing request (CSR)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
    ])
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        subject
    ).sign(private_key, hashes.SHA256(), default_backend())

    # Generate a self-signed certificate
    builder = x509.CertificateBuilder(
        subject_name=subject,
        issuer_name=issuer,
        public_key=csr.public_key(),
        serial_number=x509.random_serial_number(),
        not_valid_before=datetime.now(),
        not_valid_after=datetime.now() + timedelta(days=365),
    )
    certificate = builder.sign(private_key, hashes.SHA256(), default_backend())

    # Serialize private key and certificate
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    certificate_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM
    )

    # Write private key and certificate to files
    with open('/app/keys/ssl_private.pem', 'wb') as f:
        f.write(private_key_pem)

    with open('/app/keys/ssl_certificate.pem', 'wb') as f:
        f.write(certificate_pem)
        
