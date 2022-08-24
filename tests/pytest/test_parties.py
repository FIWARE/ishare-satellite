import pytest
from api import app
from tests.pytest.util.config_handler import load_config
from tests.pytest.util.token_handler import decode_token, decode_header, verify_token, get_access_token
import time

# Get satellite config
satellite_config = load_config("tests/config/satellite.yml", app)
app.config['satellite'] = satellite_config

# Get client config
client_config = load_config("tests/config/client_fiware.yml", app)

# /parties endpoint
PARTIES_ENDPOINT = "/parties"

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.mark.ok
@pytest.mark.it('Request all parties by EORI')
def test_all_parties_eori_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "*"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # versions token parameters
    assert parties_token['aud'] == client_config['id']
    assert parties_token['iss'] == satellite_config['id']
    assert parties_token['sub'] == satellite_config['id']

    # Valid expiration claim
    now = int(str(time.time()).split('.')[0])
    assert parties_token['iat'] <= now
    assert parties_token['exp'] > now

    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10
    assert parties_token['parties_info']['count'] == 14

@pytest.mark.ok
@pytest.mark.it('Request all parties by name')
def test_all_parties_name_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'name': "*"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10
    assert parties_token['parties_info']['count'] == 14

@pytest.mark.ok
@pytest.mark.it('Request party by eori')
def test_party_by_eori_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "EU.EORI.NLPACKETDEL"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1
    assert parties_token['parties_info']['count'] == 1
    assert parties_token['parties_info']['data'][0]['party_id'] == "EU.EORI.NLPACKETDEL"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active"

@pytest.mark.ok
@pytest.mark.it('Request party by name')
def test_party_by_name_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'name': "NoCheaper"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1
    assert parties_token['parties_info']['count'] == 1
    assert parties_token['parties_info']['data'][0]['party_id'] == "EU.EORI.NLNOCHEAPER"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active"

@pytest.mark.ok
@pytest.mark.it('Request active parties only')
def test_all_parties_active_only_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'active_only': "true"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert p['adherence']['status'] == "Active"

@pytest.mark.ok
@pytest.mark.it('Request non-active parties only')
def test_all_parties_nonactive_only_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'active_only': "false"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert p['adherence']['status'] != "Active"

@pytest.mark.ok
@pytest.mark.it('Request certified parties only')
def test_all_parties_certified_only_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'certified_only': "true"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert 'certifications' in p

@pytest.mark.ok
@pytest.mark.it('Request non-certified parties only')
def test_all_parties_noncertified_only_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'certified_only': "false"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert 'certifications' not in p

@pytest.mark.ok
@pytest.mark.it('Request party by eori and subject')
def test_party_by_subject_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "EU.EORI.NLPACKETDEL",
        'certificate_subject_name': "CN=PacketDeliveryCo,O=Packet Delivery Co,serialNumber=EU.EORI.NLPACKETDEL,C=NL"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1
    assert parties_token['parties_info']['count'] == 1
    assert parties_token['parties_info']['data'][0]['party_id'] == "EU.EORI.NLPACKETDEL"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active"

@pytest.mark.failure
@pytest.mark.it('Failure: Request party by eori and subject, but invalid subject name')
def test_party_by_subject_invalid(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "EU.EORI.NLPACKETDEL",
        'certificate_subject_name': "CN=PacketDeliveryCo,O=Packet Delivery Co,serialNumber=EU.EORI.NLPACKETDEL,C=DE"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0
    assert parties_token['parties_info']['count'] == 0

@pytest.mark.failure
@pytest.mark.it('Failure: Request party by eori and subject, but invalid serialNumber in subject name')
def test_party_by_subject_invalid_serial_number(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "EU.EORI.NLPACKETDEL",
        'certificate_subject_name': "CN=PacketDeliveryCo,O=Packet Delivery Co,serialNumber=EU.EORI.FIWARECLIENT,C=NL"
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0
    assert parties_token['parties_info']['count'] == 0

@pytest.mark.ok
@pytest.mark.it('Request all parties by EORI, page 1 with 10 parties')
def test_all_parties_eori_page1_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "*",
        'page': 1
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10
    assert parties_token['parties_info']['count'] == 14

@pytest.mark.ok
@pytest.mark.it('Request all parties by EORI, page 2 only 4 parties')
def test_all_parties_eori_page2_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "*",
        'page': 2
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 4
    assert parties_token['parties_info']['count'] == 14

@pytest.mark.ok
@pytest.mark.it('Request all parties by EORI, page 3 empty')
def test_all_parties_eori_page3_empty_ok(client):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': "*",
        'page': 3
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200

    # Parties token exists
    assert 'parties_token' in response.json

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0
    assert parties_token['parties_info']['count'] == 14
