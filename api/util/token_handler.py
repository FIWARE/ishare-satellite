import jwt
from OpenSSL import crypto
from OpenSSL.crypto import X509StoreContextError
import cryptography.x509.oid as oid
from cryptography.x509 import load_pem_x509_certificate, NameAttribute
import time, os

# Encoding of certificate subject names
SUBJECT_ENCODING = os.environ.get('SATELLITE_SUBJECT_ENCODING', 'UTF-8')

# Encoding of x5c certificates in JWTs
X5C_ENCODING = os.environ.get('SATELLITE_X5C_ENCODING', 'UTF-8')

# Header name where to expect access_token
AUTHORIZATION_HEADER = os.environ.get('SATELLITE_AUTHORIZATION_HEADER', 'Authorization')

# Name attributes as defined by rfc 4514, we set the value to PH(place holder, two capital letters comply with all names), since its required but unused
SUPPORTED_NAME_ATTRIBUTES = [
    NameAttribute(oid = oid.NameOID.COMMON_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.LOCALITY_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.STATE_OR_PROVINCE_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.ORGANIZATION_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.ORGANIZATIONAL_UNIT_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.COUNTRY_NAME, value= "PH"),
    NameAttribute(oid = oid.NameOID.STREET_ADDRESS, value= "PH"),
    NameAttribute(oid = oid.NameOID.DOMAIN_COMPONENT, value= "PH"),
    NameAttribute(oid = oid.NameOID.USER_ID, value= "PH"),
    NameAttribute(oid = oid.NameOID.EMAIL_ADDRESS, value= "PH")
]

# Get the short name for the given attribute if there is one
def get_short_name_if_available(name: str) -> str:
    nameAttribute: NameAttribute
    for nameAttribute in SUPPORTED_NAME_ATTRIBUTES: 
        if nameAttribute.oid._name == name: 
            return nameAttribute.rfc4514_attribute_name
    return name

# Verifies client_id EORI against parties list for known party
def validate_client_id(client_id, config):
    for p in config['parties']:
        if p['id'] == client_id and p['status'] == "Active":
            # Active participant
            return True

    # Not found
    return False

# Verify fingerprint of certificate against trusted_list
def verify_fingerprint(certificate, config):
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, certificate)
    fingerprint = cert.digest('sha256').decode(SUBJECT_ENCODING).replace(':','')
    for t in config['trusted_list']:
        t_cert = crypto.load_certificate(crypto.FILETYPE_PEM, t['crt'])
        t_fingerprint = t_cert.digest('sha256').decode(SUBJECT_ENCODING).replace(':','')
        if fingerprint == t_fingerprint:
            return True

    # Fingerprint not found
    return False

# Get Authorization header
def get_authorization_header(request):
    try:
        request_token = request.headers.get(AUTHORIZATION_HEADER)
        if len(request_token) < 1:
            return None
        return request_token.replace('Bearer ','')
    except Exception as ex:
        return None

# Load certificate
def load_certificate(cert):
    return crypto.load_certificate(crypto.FILETYPE_PEM, cert)

# Retrieves x5c cert chain array from config string
def get_x5c_chain(cert):
    sp = cert.split('-----BEGIN CERTIFICATE-----\n')
    sp = sp[1:]
    
    ca_chain = []
    for ca in sp:
        ca_sp = ca.split('\n-----END CERTIFICATE-----')
        ca_chain.append(ca_sp[0].replace('\n',''))
        
    return ca_chain

# Get subject components with there short names and original names
def get_subject_components_full(cert) -> dict: 
    cr = load_certificate(cert)
    subject = cr.get_subject()
    b_subject_components = subject.get_components()

    # Convert from bytes to string
    subject_components = {}
    for c in b_subject_components:
        originalName : str= c[0].decode(SUBJECT_ENCODING)
        shortName: str = get_short_name_if_available(originalName)   
        subject_components[originalName] = c[1].decode(SUBJECT_ENCODING)
        subject_components[shortName] = c[1].decode(SUBJECT_ENCODING)

    return subject_components

# Get subject components
def get_subject_components(cert):
    cr = load_certificate(cert)
    subject = cr.get_subject()
    b_subject_components = subject.get_components()

    # Convert from bytes to string
    subject_components = []
    for c in b_subject_components:
        subject_components.append((c[0].decode(SUBJECT_ENCODING), c[1].decode(SUBJECT_ENCODING)))

    return subject_components

# Validate iSHARE JWT
def validate_jwt(token, config, app, required_issuer=None):
    app.logger.debug('Validating iSHARE JWT...')

    try:
    
        # Empty token?
        if (not token) or len(token) < 1:
            app.logger.debug('Empty token')
            return False

        # Decode JWT w/o verification to extract headers first
        decoded_payload = jwt.decode(token, options={"verify_signature": False})
        decoded_header = jwt.get_unverified_header(token)
        app.logger.debug('--> Decoded JWT payload: {}'.format(decoded_payload))
        app.logger.debug('--> Decoded JWT header: {}'.format(decoded_header))
        
        # Validate timestamp
        now = int(str(time.time()).split('.')[0])
        exp = decoded_payload['exp']
        nbf = 0
        if 'nbf' in decoded_payload:
            nbf = decoded_payload['nbf']
        elif 'iat' in decoded_payload:
            nbf = decoded_payload['iat']
        else:
            app.logger.debug('JWT is missing iat and nbf claim')
            return False
        if exp < now or nbf > now:
            app.logger.debug('JWT has expired or was issued in the future')
            return False
        
        # Validate alg
        if decoded_header['alg'].upper() != "RS256":
            app.logger.debug('Wrong header alg={}'.format(decoded_header['alg']))
            return False

        # Check required issuer
        if required_issuer is not None:
            if decoded_payload['iss'] != required_issuer:
                app.logger.debug("Invalid iss parameter")
                return False

        # Check for x5c header
        if 'x5c' not in decoded_header:
            app.logger.debug('Missing x5c header')
            return False

        # Check for at least client and root CA certificates
        if len(decoded_header['x5c']) < 2:
            app.logger.debug('x5c certificate chain requires at least two certificates')
            return False

        # Get first certificate from x5c header and retrieve subject
        issuer_cert = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format("".join(decoded_header['x5c'][0].splitlines()))
        subject_components = get_subject_components(issuer_cert)
        
        # Compare JWT iss against certificate subject serialNumber
        serialNumber = ""
        for c in subject_components:
            if 'serialNumber' == c[0]:
                serialNumber = c[1]
                break
        if len(serialNumber) < 1:
            app.logger.debug('Missing serialNumber in certificate subject')
            return False
        if decoded_payload['iss'] != serialNumber:
            app.logger.debug('serialNumber={} in certificate subject does not equal JWT issuer={}'.format(serialNumber, decoded_payload['iss']))
            return False
        
        # Verify provided x5c root CA fingerprint against trusted_list
        root_ca = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format("".join(decoded_header['x5c'][len(decoded_header['x5c'])-1].splitlines()))
        if not verify_fingerprint(root_ca, config):
            app.logger.debug('Provided x5c root CA not in trusted_list')
            return False

        # Add root CA to store
        store = crypto.X509Store()
        root_crt = crypto.load_certificate(crypto.FILETYPE_PEM, root_ca)
        store.add_cert(root_crt)

        # Verify first intermediate
        if len(decoded_header['x5c']) >= 3:
            int_crt_pem = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format("".join(decoded_header['x5c'][len(decoded_header['x5c'])-2].splitlines()))
            int_crt = crypto.load_certificate(crypto.FILETYPE_PEM, int_crt_pem)
            store_ctx = crypto.X509StoreContext(store, int_crt)
            try:
                store_ctx.verify_certificate()
                store.add_cert(int_crt)
            except X509StoreContextError as xerr:
                app.logger.debug('Failed validation of first intermediate certificate: {}'.format(xerr.certificate))
                return False
        
        # Verify further intermediates
        if len(decoded_header['x5c']) >= 3:
            for c_pem in list(reversed(decoded_header['x5c']))[2:len(decoded_header['x5c'])]:
                int_crt_pem = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format("".join(c_pem.splitlines()))
                int_crt = crypto.load_certificate(crypto.FILETYPE_PEM, int_crt_pem)
                store_ctx = crypto.X509StoreContext(store, int_crt)
                try:
                    store_ctx.verify_certificate()
                    store.add_cert(int_crt)
                except X509StoreContextError as xerr:
                    app.logger.debug('Failed validation of intermediate certificate: {}'.format(xerr.certificate))
                    return False

        # Verify client certificate
        if len(decoded_header['x5c']) >= 2:
            client_crt_pem = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format("".join(decoded_header['x5c'][0].splitlines()))
            client_crt = crypto.load_certificate(crypto.FILETYPE_PEM, client_crt_pem)
            store_ctx = crypto.X509StoreContext(store, client_crt)
            try:
                store_ctx.verify_certificate()
            except X509StoreContextError as xerr:
                app.logger.debug('Failed validation of client certificate: {}'.format(xerr.certificate))
                return False
        
        # Verify JWT against client certificate
        cert_pem = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----".format("".join(decoded_header['x5c'][0].splitlines()))
        cert_obj = load_pem_x509_certificate(cert_pem.encode(X5C_ENCODING))
        public_key = cert_obj.public_key()
        try:
            jwt.decode(token, key=public_key, algorithms=['RS256'], audience=config['id'])
        except Exception as dex:
            app.logger.debug('{}: JWT failed validation against provided certificate --> {}'.format(type(dex), dex))
            return False

    except Exception as ex:
        app.logger.debug('Could not validate JWT: {}'.format(ex))
        return False
    
    return True
