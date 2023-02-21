import pytest
from api import app
from tests.pytest.util.config_handler import load_config
from tests.pytest.util.token_handler import decode_token, decode_header, verify_token, get_access_token, encode_token
import time

# Get satellite config
satellite_config = load_config("tests/config/satellite.yml", app)
app.config['satellite'] = satellite_config

# Get client config
client_config = load_config("tests/config/client_fiware.yml", app)

# /versions endpoint
VERSIONS_ENDPOINT = "/versions"

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Successful versions
@pytest.mark.ok
@pytest.mark.it('Successfully request /versions')
def test_versions_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Invoke request
    response = client.get(VERSIONS_ENDPOINT, headers=headers)
    
    # Status code
    assert response.status_code == 200, "Response should have status code 200"

    # Versions token exists
    assert 'versions_token' in response.json, "Response should contain versions_token"

    # Get header
    token_header = decode_header(response.json['versions_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in token_header, "x5c parameter should be in the response token header"
    versions_token = {}
    try:
        versions_token = verify_token(response.json['versions_token'], token_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned versions token --> Exception {}: {}'.format(type(ex).__name__, ex))

    # versions token parameters
    assert versions_token['aud'] == client_config['id'], "Returned token aud parameter should be equal to client ID"
    assert versions_token['iss'] == satellite_config['id'], "Returned token iss parameter should be equal to satellite ID"
    assert versions_token['sub'] == satellite_config['id'], "Returned token sub parameter should be equal to satellite ID"

    # Valid expiration claim
    now = int(str(time.time()).split('.')[0])
    assert versions_token['iat'] <= now, "Returned token iad parameter should be smaller or equal than current timestamp"
    assert versions_token['exp'] > now, "Returned token exp parameter should be larger than current timestamp"
    
    # Should contain 3 versions
    assert len(versions_token['versions_info']) == 3, "Response verions info should contain 3 entries"

@pytest.mark.failure
@pytest.mark.it('Failure: Request /versions, but access_token is expired')
def test_versions_expired_access_token(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Decode access_token
    decoded_token = decode_token(access_token)
    
    # Change exp parameter
    decoded_token['exp'] = decoded_token['nbf'] - 1
    
    # Encode access token again with satellite private key
    access_token = encode_token(decoded_token, satellite_config['key'])
    
    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Invoke request
    response = client.get(VERSIONS_ENDPOINT, headers=headers)
    
    # Status code
    assert response.status_code == 401, "Response should have status code 401"
    
@pytest.mark.failure
@pytest.mark.it('Failure: Request /versions, but replaced client_id in access_token to invalid client')
def test_versions_replaced_client_id_access_token(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Decode access_token
    decoded_token = decode_token(access_token)
    
    # Load config of invalid client and replace client_id
    cnf = load_config("tests/config/client_invalid_fiware.yml", app)
    decoded_token['client_id'] = cnf['id']
    
    # Encode access token again
    access_token = encode_token(decoded_token, cnf['key'])
    
    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Invoke request
    response = client.get(VERSIONS_ENDPOINT, headers=headers)
    
    # Status code
    assert response.status_code == 401, "Response should have status code 401"

@pytest.mark.failure
@pytest.mark.it('Failure: Request /versions, but using self-issued access_token')
def test_versions_self_issued_access_token(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Decode access_token
    decoded_token = decode_token(access_token)
    
    # Replace iss/aud parameters
    decoded_token['iss'] = client_config['id']
    decoded_token['aud'] = client_config['id']
    
    # Encode access token again
    access_token = encode_token(decoded_token, client_config['key'])
    
    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Invoke request
    response = client.get(VERSIONS_ENDPOINT, headers=headers)
    
    # Status code
    assert response.status_code == 401, "Response should have status code 401"
