import pytest
from api import app
from tests.pytest.util.config_handler import load_config
from tests.pytest.util.token_handler import create_request_token, decode_token
import time

# Get satellite config
satellite_config = load_config("tests/config/satellite.yml", app)
app.config['satellite'] = satellite_config

# Get client config
client_config = load_config("tests/config/client_fiware.yml", app)

# Standard auth params
auth_params = {
    'grant_type': 'client_credentials',
    'scope': 'iSHARE',
    'client_id': client_config['id'],
    'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
    'client_assertion': None
}

# /token endpoint
TOKEN_ENDPOINT = "/token"

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Successful token
@pytest.mark.ok
@pytest.mark.it('Successfully request access_token')
def test_token_ok(client):
    # Get request token
    token = create_request_token(client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 200

    # Response attributes
    assert response.json['scope'] == 'iSHARE'
    assert response.json['token_type'] == 'Bearer'
    
    # Access token exists
    assert 'access_token' in response.json

    # Decode token
    access_token = decode_token(response.json['access_token'])
    
    # Access token parameters
    assert access_token['client_id'] == client_config['id']
    assert access_token['iss'] == satellite_config['id']
    assert access_token['aud'] == satellite_config['id']
    assert access_token['scope'] == ["iSHARE"]

    # Valid expiration claim
    now = int(str(time.time()).split('.')[0])
    assert access_token['nbf'] <= now
    assert access_token['exp'] > now
    
@pytest.mark.failure
@pytest.mark.it('Failure: Request access token with invalid client')
def test_token_invalid_client(client):
    # Get config
    cnf = load_config("tests/config/client_invalid_fiware.yml", app)
    
    # Get request token
    token = create_request_token(client_id=cnf['id'], satellite_id=satellite_config['id'], key=cnf['key'], crt=cnf['crt'])
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token
    t_auth_params['client_id'] = cnf['id']

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 400

@pytest.mark.failure
@pytest.mark.it('Failure: Request access token with client_id not matching signed request JWT issuer')
def test_token_client_id_unequals_iss(client):
    # Get config
    cnf = load_config("tests/config/client_invalid_fiware.yml", app)
    
    # Get request token
    token = create_request_token(client_id=cnf['id'], satellite_id=satellite_config['id'], key=cnf['key'], crt=cnf['crt'])
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token
    
    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 400

@pytest.mark.failure
@pytest.mark.it('Failure: Request access token with invalid client and certificate from invalid root CA')
def test_token_invalid_root_ca(client):
    # Get config
    cnf = load_config("tests/config/client_invalid_ca_fiware.yml", app)
    
    # Get request token
    token = create_request_token(client_id=cnf['id'], satellite_id=satellite_config['id'], key=cnf['key'], crt=cnf['crt'])
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token
    t_auth_params['client_id'] = cnf['id']

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 400

@pytest.mark.failure
@pytest.mark.it('Failure: Request access token with valid client but cert chain replaced with invalid intermediate+root CA')
def test_token_valid_client_invalid_cert_chain(client):
    # Get configs
    cnf = load_config("tests/config/client_fiware.yml", app)
    cnf_invalid = load_config("tests/config/client_invalid_ca_fiware.yml", app)

    # Build new cert chain
    crt = cnf['client_crt']
    crt = '{}\n{}\n{}'.format(crt, cnf_invalid['intermediate'], cnf_invalid['rootca'])
        
    # Get request token
    token = create_request_token(client_id=cnf['id'], satellite_id=satellite_config['id'], key=cnf['key'], crt=crt)
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token
    t_auth_params['client_id'] = cnf['id']

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 400

@pytest.mark.failure
@pytest.mark.it('Failure: Request access token with valid client but cert chain replaced with invalid intermediate')
def test_token_valid_client_invalid_intermediate(client):
    # Get configs
    cnf = load_config("tests/config/client_fiware.yml", app)
    cnf_invalid = load_config("tests/config/client_invalid_ca_fiware.yml", app)

    # Build new cert chain
    crt = cnf['client_crt']
    crt = '{}\n{}\n{}'.format(crt, cnf_invalid['intermediate'], cnf['rootca'])
        
    # Get request token
    token = create_request_token(client_id=cnf['id'], satellite_id=satellite_config['id'], key=cnf['key'], crt=crt)
    t_auth_params = auth_params
    t_auth_params['client_assertion'] = token
    t_auth_params['client_id'] = cnf['id']

    # Invoke request
    response = client.post(TOKEN_ENDPOINT, data=t_auth_params)
    
    # Status code
    assert response.status_code == 400
