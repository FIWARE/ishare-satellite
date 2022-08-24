from flask import Blueprint, Response, current_app, abort, request
from api.util.token_handler import validate_jwt, get_authorization_header, get_x5c_chain
from api.util.config_handler import get_private_key, get_certificates
import uuid
import time, os
import jwt

# Duration of the created response token
RESPONSE_TOKEN_DURATION = int(os.environ.get('SATELLITE_RESPONSE_TOKEN_DURATION', 30))

# Blueprint
versions = Blueprint("versions", __name__, url_prefix="/versions")

# GET /versions
@versions.route("")
def index():

    # Load config
    satellite = current_app.config['satellite']

    # Get Authorization header
    request_token = get_authorization_header(request)
    if not request_token:
        current_app.logger.debug('Could not retrieve Authorization header: {}'.format(ex))
        abort(401, description='Could not retrieve Authorization header')

    # Validate and verify JWT
    if not validate_jwt(request_token, satellite, current_app, required_issuer=satellite['id']):
        current_app.logger.debug('iSHARE JWT access_token could not be validated')
        abort(401, description='iSHARE JWT access_token could not be validated')
    
    # Versions info
    result = {
        "versions_info": [
            {
                "valid_from": "2030-07-04T08:00:00Z",
                "valid_to": "2050-01-04T08:00:00Z",
                "version_name": "3.0.0",
                "version_status": "planned"
            },
            {
                "valid_from": "2018-07-04T08:00:00Z",
                "valid_to": "2030-07-04T08:00:00Z",
                "version_name": "2.0.0",
                "version_status": "active"
            },
            {
                "valid_from": "2019-01-04T08:00:00Z",
                "valid_to": "2030-07-04T08:00:00Z",
                "version_name": "1.9.0",
                "version_status": "active"
            }
        ]
    }

    # Add iss/sub (= local EORI)
    try:
        result['iss'] = satellite['id']
        result['sub'] = satellite['id']
    except KeyError as ke:
        current_app.logger.error('Could not load satellite EORI, config key not found: {}'.format(ke))
        abort(500)

    # Add aud (= requester EORI)
    decoded_payload = ""
    try:
        decoded_payload = jwt.decode(request_token, options={"verify_signature": False})
    except Exception as ex:
        current_app.logger.debug('Could not decode JWT: {}'.format(ex))
        abort(401, description="Could not decode iSHARE JWT Access_token")
    result['aud'] = decoded_payload['client_id']
    
    # Add exp/iat
    iat = int(str(time.time()).split('.')[0])
    exp = iat + RESPONSE_TOKEN_DURATION
    result['iat'] = iat
    result['exp'] = exp

    # Add jti
    result['jti'] = str(uuid.uuid4())

    # Build header
    header = {
        'x5c': get_x5c_chain(get_certificates(satellite))
    }

    # Encode JWT
    current_app.logger.debug("Encoding access token JWT")
    current_app.logger.debug("{}".format(result))
    versions_token = ""
    try:
        versions_token = jwt.encode(result, get_private_key(satellite), algorithm="RS256", headers=header)
    except Exception as ex:
        current_app.logger.debug('Could not encode JWT for versions_token: {}'.format(ex))
        abort(500)

    current_app.logger.debug("==> {}".format(versions_token))
    return {
        'versions_token' : versions_token
    }, 200

