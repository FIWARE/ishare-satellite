import jwt
import os
import time
import uuid
from cryptography.x509 import load_pem_x509_certificate

# /token endpoint
TOKEN_ENDPOINT = "/token"

# Create iSHARE JWT token
def create_request_token(client_id, satellite_id, key, crt):

    def getCAChain(cert):

        sp = cert.split('-----BEGIN CERTIFICATE-----\n')
        sp = sp[1:]

        ca_chain = []
        for ca in sp:
            ca_sp = ca.split('\n-----END CERTIFICATE-----')
            ca_chain.append(ca_sp[0])
            
        return ca_chain

    iat = int(str(time.time()).split('.')[0])
    exp = iat + 30
    
    token = {
        "jti": str(uuid.uuid4()),
        "iss": client_id,
        "sub": client_id,
        "aud": [
            satellite_id
        ],
        "iat": iat,
        "nbf": iat,
        "exp": exp
    }

    return jwt.encode(token, key, algorithm="RS256", headers={
        'x5c': getCAChain(crt)
    })

# Decode iSHARE JWT
def decode_token(token):
    return jwt.decode(token, options={"verify_signature": False})

# Decode header of iSHARE JWT without verification
def decode_header(token):
    return jwt.get_unverified_header(token)

# Verify signature of iSHARE JWT and return decoded payload
def verify_token(token, x5c, alg="RS256", aud=None):
    cert_pem = "-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----\n".format(x5c)
    cert_obj = load_pem_x509_certificate(cert_pem.encode('UTF-8'))
    public_key = cert_obj.public_key()
    return jwt.decode(token, public_key, algorithms=alg, audience=aud)

# Encode token
def encode_token(token, key, x5c=None):
    headers = {}
    if x5c is not None:
        headers['x5c'] = x5c

    return jwt.encode(token, key, algorithm="RS256", headers=headers)

# Get access token
def get_access_token(client, client_id, satellite_id, key, crt):
    # Auth params
    auth_params = {
        'grant_type': 'client_credentials',
        'scope': 'iSHARE',
        'client_id': client_id,
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': None
    }
    
    # Get request token
    token = create_request_token(client_id=client_id, satellite_id=satellite_id, key=key, crt=crt)
    auth_params['client_assertion'] = token

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=auth_params)

    return response.json['access_token']
