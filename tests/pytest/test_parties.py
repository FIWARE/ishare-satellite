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
    #app.logger.setLevel("DEBUG")
    #app.logger.info("Setting test logger...")

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # versions token parameters
    assert parties_token['aud'] == client_config['id'], "Returned token aud parameter should be equal to client ID"
    assert parties_token['iss'] == satellite_config['id'], "Returned token iss parameter should be equal to satellite ID"
    assert parties_token['sub'] == satellite_config['id'], "Returned token sub parameter should be equal to satellite ID"

    # Valid expiration claim
    now = int(str(time.time()).split('.')[0])
    assert parties_token['iat'] <= now, "Returned token iad parameter should be smaller or equal than current timestamp"
    assert parties_token['exp'] > now, "Returned token exp parameter should be larger than current timestamp"

    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10, "Parties list should contain only 10 entries due to pagination"
    assert parties_token['parties_info']['count'] == 14, "Parties info should report 14 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10, "Parties list should contain only 10 entries due to pagination"
    assert parties_token['parties_info']['count'] == 14, "Parties info should report 14 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1, "Parties list should contain 1 entry"
    assert parties_token['parties_info']['count'] == 1, "Parties info should report 1 entry"
    assert parties_token['parties_info']['data'][0]['party_id'] == "EU.EORI.NLPACKETDEL", "ID of first entry should be equal to EU.EORI.NLPACKETDEL"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active", "Status of first entry should be equal to Active"
    p = parties_token['parties_info']['data'][0]
    assert p['registrar_id'] == satellite_config['id'], "registrar_id should be equal to satellite ID"
    assert 'additional_info' in p, "should contain additional_info"
    assert p['additional_info']['website'] == "https://www.packetdelivery.com", "additional_info should contain website"
    assert 'agreements' in p, "should contain agreements"
    assert len(p['agreements']) == 2, "agreements should contain 2 entries"
    assert p['agreements'][0]['type'] == "TermsOfUse", "First agreement should have correct type"
    assert p['agreements'][1]['framework'] == "iSHARE", "Second agreement should have correct framework"
    assert 'certificates' in p, "should contain certificates"
    assert len(p['certificates']) == 1, "certificates list should contain only 1 entry"
    assert p['certificates'][0]['x5t#S256'] == "AB082F48B3CDA0D3502553E978311CAF5122DC8EB3924D85223A5D145771188F", "certificate should have correct fingerprint"
    assert p['certificates'][0]['enabled_from'] == "2021-02-18T11:24:03.000Z", "certificate should have correct issue date"
    assert 'roles' in p, "should contain roles"
    assert len(p['roles']) == 1, "should contain 1 role"
    assert p['roles'][0]['role'] == "ServiceProvider", "should have ServiceProvider role"
    assert 'authregistery' in p, "should contain authregistery"
    assert len(p['authregistery']) == 1, "authregistery should have 1 entry"
    assert p['authregistery'][0]['authorizationRegistryID'] == "EU.EORI.NLPACKETDEL", "authregistery should have correct authorizationRegistryID"
    
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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1, "Parties list should contain 1 entry"
    assert parties_token['parties_info']['count'] == 1, "Parties info should report 1 entry"
    assert parties_token['parties_info']['data'][0]['party_id'] == "EU.EORI.NLNOCHEAPER", "ID of first entry should be equal to EU.EORI.NLNOCHEAPER"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active", "Status of first entry should be equal to Active"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert p['adherence']['status'] == "Active", "Status of parties entry {} should be equal to Active".format(p['party_id'])

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert p['adherence']['status'] != "Active", "Status of parties entry {} should be unequal to Active".format(p['party_id'])

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert 'certifications' in p, "Parties entry {} should contain parameter certifications".format(p['party_id'])

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    for p in parties_token['parties_info']['data']:
        assert 'certifications' not in p, "Parties entry {} should not contain parameter certifications".format(p['party_id'])

test_request_data= [
    ("EU.EORI.NLPACKETDEL", "CN=PacketDeliveryCo,O=Packet Delivery Co,serialNumber=EU.EORI.NLPACKETDEL,C=NL"),
    ("EU.EORI.NLPACKETDEL", "CN=PacketDeliveryCo,O=Packet Delivery Co,E=client@fiware.org,serialNumber=EU.EORI.NLPACKETDEL,C=NL"),
    ("EU.EORI.FIWARECLIENT", "E=client@fiware.org,serialNumber=EU.EORI.FIWARECLIENT,C=DE"),
    ("EU.EORI.FIWARECLIENT", "emailAddress=client@fiware.org,serialNumber=EU.EORI.FIWARECLIENT,C=DE"),
    ("EU.EORI.FIWARECLIENT", "CN=FIWARE-Client,O=FIWARE Client,emailAddress=client@fiware.org,serialNumber=EU.EORI.FIWARECLIENT,C=DE"),
    ("EU.EORI.FIWARECLIENT", "CN=FIWARE-Client,O=FIWARE Client,E=client@fiware.org,serialNumber=EU.EORI.FIWARECLIENT,C=DE")
]


@pytest.mark.ok
@pytest.mark.it('Request party by eori and subject')
@pytest.mark.parametrize("eori,subject", test_request_data)
def test_party_by_subject_ok(client, eori, subject):
    # Get access token
    access_token = get_access_token(client=client, client_id=client_config['id'], satellite_id=satellite_config['id'], key=client_config['key'], crt=client_config['crt'])

    # Set header
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Set params
    params = {
        'eori': eori,
        'certificate_subject_name': subject
    }
    
    # Invoke request
    response = client.get(PARTIES_ENDPOINT, headers=headers, query_string=params)
    
    # Status code
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Get header
    parties_header = decode_header(response.json['parties_token'])

    # Verify token with provided x5c header and get decoded payload
    assert 'x5c' in parties_header, "x5c parameter should be in the response token header"
    parties_token = {}
    try:
        parties_token = verify_token(response.json['parties_token'], parties_header['x5c'][0], alg="RS256", aud=client_config['id'])
    except Exception as ex:
        pytest.fail('Error when verifying and decoding returned parties token --> Exception {}: {}'.format(type(ex).__name__, ex))
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 1, "Parties list should contain 1 entry"
    assert parties_token['parties_info']['count'] == 1, "Parties info should report 1 entry"
    assert parties_token['parties_info']['data'][0]['party_id'] == eori, "Party ID of first entry should equal requested EORI of query"
    assert parties_token['parties_info']['data'][0]['adherence']['status'] == "Active", "Status of first entry should be equal to Active"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0, "Parties list should be empty"
    assert parties_token['parties_info']['count'] == 0, "Parties info should report 0 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0, "Parties list should be empty"
    assert parties_token['parties_info']['count'] == 0, "Parties info should report 0 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 10, "Parties list should contain 10 entries"
    assert parties_token['parties_info']['count'] == 14, "Parties info should report 14 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 4, "Parties list should contain 4 entries"
    assert parties_token['parties_info']['count'] == 14, "Parties info should report 14 entries"

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
    assert response.status_code == 200, "Response should have status code 200"

    # Parties token exists
    assert 'parties_token' in response.json, "Response should contain parties_token"

    # Decode token
    parties_token = decode_token(response.json['parties_token'])
    
    # Verify parties
    assert len(parties_token['parties_info']['data']) == 0, "Parties list should be empty"
    assert parties_token['parties_info']['count'] == 14, "Parties info should report 14 entries"
