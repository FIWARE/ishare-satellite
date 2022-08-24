from flask import Blueprint, Response, current_app, abort, request
from api.util.token_handler import validate_jwt, validate_client_id, get_x5c_chain
from api.util.config_handler import get_certificates, get_private_key
import jwt
import time, os

# Duration of the created access_token
ACCESS_TOKEN_DURATION = int(os.environ.get('SATELLITE_ACCESS_TOKEN_DURATION', 3600))

# Blueprint
token_endpoint = Blueprint("token_endpoint", __name__, url_prefix="/token")

# POST /token
@token_endpoint.route("", methods = ['POST'])
def index():

    # Load config
    satellite = current_app.config['satellite']

    # Get request parameters
    request_token = ""
    request_id = ""
    request_grant_type = ""
    request_scope = ""
    request_assertion_type = ""
    try:
        request_token = request.form.get('client_assertion')
        if len(request_token) < 1:
            current_app.logger.debug('Empty Authorization header')
            abort(400)
        current_app.logger.debug('Received client_assertion: {}'.format(request_token))
        request_id = request.form.get('client_id')
        request_grant_type = request.form.get('grant_type')
        request_scope = request.form.get('scope')
        request_assertion_type = request.form.get('client_assertion_type')
    except Exception as ex:
        current_app.logger.debug('Could not retrieve request parameters: {}'.format(ex))
        abort(400)
    
    # Validate scope
    if "iSHARE" not in request_scope:
        current_app.logger.debug('Missing iSHARE scope in request')
        abort(400, description="Missing iSHARE scope in request")

    # Validate grant_type
    if request_grant_type != 'client_credentials':
        current_app.logger.debug('Wrong grant_type={} in request'.format(request_grant_type))
        abort(400, description='Wrong grant_type={} in request'.format(request_grant_type))

    # Validate assertion_type
    if request_assertion_type != 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer':
        current_app.logger.debug('Wrong client_assertion_type={} in request'.format(request_grant_type))
        abort(400, description='Wrong client_assertion_type={} in request'.format(request_grant_type))

    # Check client_id against parties list
    if not validate_client_id(request_id, satellite):
        current_app.logger.debug('Unknown client_id in request')
        abort(400, description='Unknown client_id in request')

    # Validate and verify JWT
    if not validate_jwt(request_token, satellite, current_app, required_issuer=request_id):
        current_app.logger.debug('iSHARE JWT could not be validated')
        abort(400, description='iSHARE JWT could not be validated')
        
    # Build return object
    result = {
        'scope': 'iSHARE',
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_DURATION
    }

    # Build access token
    nbf = int(str(time.time()).split('.')[0])
    exp = nbf + ACCESS_TOKEN_DURATION
    access_token = {
        'aud': satellite['id'],
        'iss': satellite['id'],
        'client_id': request_id,
        'nbf': nbf,
        'exp': exp,
        'scope': ["iSHARE"]
    }
    header = {
        'x5c': get_x5c_chain(get_certificates(satellite))
    }
    
    # Encode JWT
    current_app.logger.debug("Encoding access token JWT")
    result['access_token'] = jwt.encode(access_token, get_private_key(satellite), algorithm="RS256", headers=header)

    # Return
    current_app.logger.debug('Returning access token')
    return result, 200
