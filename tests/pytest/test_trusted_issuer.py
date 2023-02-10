import pytest
from api import app
from tests.pytest.util.config_handler import load_config

TEST_DID = "did:key:z6Mkv4Lh9zBTPLoFhLHHMFJA7YAeVw5HFYZV8rkdfY9fNtm3"

# Get satellite config
satellite_config = load_config("tests/config/satellite.yml", app)
app.config['satellite'] = satellite_config

# Get client config
client_config = load_config("tests/config/client_fiware.yml", app)

# /trusted_issuer endpoint
TRUSTED_ISSUER_ENDPOINT = "/trusted_issuer/v3/issuers"

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Successful trusted_issuer
@pytest.mark.ok
@pytest.mark.it('Successfully request /trusted_issuer')
def test_trusted_issuer_list_ok(client):
    
    # Invoke request
    response = client.get(TRUSTED_ISSUER_ENDPOINT)
    
    # Status code
    assert response.status_code == 200, "The trusted_issuers endpoint should return a successful response."

    # Trusted result list
    assert 'items' in response.json, "The list of items should be included in the response."
    # Pagination
    assert 'pageSize' in response.json, "The pagination information should be returned."
    assert 'total' in response.json, "The total should be included in the response."

    assert 100 == response.json['pageSize'], "Without a pageSize requested, the default should be returened." 

    assert len(response.json['items']) == 1, "Only one party is configured with a did, thus only one should be returned."
    assert response.json['total'] == 1, "Only one party is configured with a did, thus the total has to be one."
    
    firstItem = response.json['items'][0]

    assert 'did' in firstItem, "The item must have a did."
    assert firstItem['did'] == TEST_DID, "The did must be the one configured in the satellite yaml."

# Successfully retrieve trusted_issuer
@pytest.mark.ok
@pytest.mark.it('Get a single /trusted_issuer')
def test_trusted_issuer(client):
    
    # Invoke request
    response = client.get(TRUSTED_ISSUER_ENDPOINT + "/" + TEST_DID)

    # Status code
    assert response.status_code == 200, "The issuer endpoint should be returned in a successful response."

    assert 'attributes' in response.json, "The attributes of the issuer should be returned."
    assert 'did' in response.json, "The did of the issuer should be returned."
    
    assert response.json['did'] == TEST_DID, "The requested issuer should have been returned"
    assert len(response.json['attributes']) == 7, "All configured attributes should be returned"