from flask import Blueprint, Response, current_app, abort, request
from api.util.token_handler import validate_jwt, get_authorization_header, get_x5c_chain
from api.util.parties_handler import check_invalid_parameters, get_parties_info, paginate_parties
from api.util.config_handler import get_private_key, get_certificates
import uuid
import time, os
import jwt

# Duration of the created response token
RESPONSE_TOKEN_DURATION = int(os.environ.get('SATELLITE_RESPONSE_TOKEN_DURATION', 30))

# Blueprint
parties = Blueprint("parties", __name__, url_prefix="/parties")

# GET /parties
@parties.route("")
def index():

    # Load config
    satellite = current_app.config['satellite']

    # Check parameters
    p_check = check_invalid_parameters(request)
    if p_check:
        current_app.logger.debug("Request parameters invalid: {}".format(p_check))
        abort(400, 'Invalid request parameters: {}'.format(p_check))

    # Get Authorization header
    request_token = get_authorization_header(request)
    if not request_token:
        current_app.logger.debug('Could not retrieve Authorization header')
        abort(401, description='Could not retrieve Authorization header')

    # Validate and verify JWT
    if not validate_jwt(request_token, satellite, current_app, required_issuer=satellite['id']):
        current_app.logger.debug('iSHARE JWT access_token could not be validated')
        abort(401, description='iSHARE JWT access_token could not be validated')

    # Build return object
    result = {}

    # Build parties data
    current_app.logger.debug("Build parties data")
    parties_info = get_parties_info(request, satellite, current_app)

    # Paginate
    r_page = request.args.get('page')
    if (r_page is not None):
        current_app.logger.debug("Paginate --> page: {}".format(r_page))
        parties_info = paginate_parties(parties_info, r_page)
    else:
        current_app.logger.debug("Paginate --> page: 1")
        parties_info = paginate_parties(parties_info, 1)

    # Set parties_info
    result['parties_info'] = parties_info

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
        current_app.logger.debug('Could not decode JWT to extract result aud parameter: {}'.format(ex))
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
    current_app.logger.debug("Encoding parties_token JWT")
    current_app.logger.debug("{}".format(result))
    p_token = ""
    try:
        p_token = jwt.encode(result, get_private_key(satellite), algorithm="RS256", headers=header)
    except Exception as dec_ex:
        current_app.logger.debug('Could not encode JWT for parties_token: {}'.format(dec_ex))
        abort(500)

    current_app.logger.debug("==> {}".format(p_token))
    return {
        'parties_token' : p_token
    }, 200

