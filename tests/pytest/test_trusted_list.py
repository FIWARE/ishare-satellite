import pytest
from api import app
from tests.pytest.util.config_handler import load_config
from tests.pytest.util.token_handler import decode_header, verify_token, get_access_token
import time

# Get satellite config
satellite_config = load_config("tests/config/satellite.yml", app)
app.config['satellite'] = satellite_config

# Get client config
client_config = load_config("tests/config/client_fiware.yml", app)

# /trusted_list endpoint
TRUSTED_LIST_ENDPOINT = "/trusted_list"

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Successful trusted_list
@pytest.mark.ok
@pytest.mark.it('Successfully request /trusted_list')
def test_trusted_list_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Invoke request
    response = client.get(TRUSTED_LIST_ENDPOINT, headers=headers)
    
    # Status code
    assert response.status_code == 200, "Response should have status code 200"

    # Trusted list token exists
    assert 'trusted_list_token' in response.json, "Response should contain trusted_list_token"

    # Get header
    token_header = decode_header(response.json['trusted_list_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in token_header, "x5c parameter should be in the response token header"
    trusted_list_token = {}
    try:
        trusted_list_token = verify_token(response.json['trusted_list_token'], token_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned trusted_list token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # versions token parameters
    assert trusted_list_token['aud'] == client_config['id'], "Returned token aud parameter should be equal to client ID"
    assert trusted_list_token['iss'] == satellite_config['id'], "Returned token iss parameter should be equal to satellite ID"
    assert trusted_list_token['sub'] == satellite_config['id'], "Returned token sub parameter should be equal to satellite ID"

    # Valid expiration claim
    now = int(str(time.time()).split('.')[0])
    assert trusted_list_token['iat'] <= now, "Returned token iad parameter should be smaller or equal than current timestamp"
    assert trusted_list_token['exp'] > now, "Returned token exp parameter should be larger than current timestamp"

    # Verify trusted list
    assert len(trusted_list_token['trusted_list']) == 2, "Trusted list should contain 2 entries"
    assert trusted_list_token['trusted_list'][0]['certificate_fingerprint'] == "A78FDF7BA13BBD95C6236972DD003FAE07F4E447B791B6EF6737AD22F0B61862", "1st fingerprint should be correctly calculated"
    assert trusted_list_token['trusted_list'][1]['certificate_fingerprint'] == "8ECB9BD8E0FE12D7368ACDE12905E823812C34A71F97439D9E42383477C94E2B", "2nd fingerprint should be correctly calculated"

