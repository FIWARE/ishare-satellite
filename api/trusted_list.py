from flask import Blueprint, Response, current_app, abort, request
from api.util.token_handler import validate_jwt, get_authorization_header, get_subject_components, load_certificate, get_x5c_chain
from api.util.config_handler import get_private_key, get_certificates
import uuid
import time, os
import jwt

# Encoding of the certificate fingerprint
FINGERPRINT_ENCODING = os.environ.get('SATELLITE_FINGERPRINT_ENCODING', 'UTF-8')

# Duration of the created response token
RESPONSE_TOKEN_DURATION = int(os.environ.get('SATELLITE_RESPONSE_TOKEN_DURATION', 30))

# Blueprint
trusted_list = Blueprint("trusted_list", __name__, url_prefix="/trusted_list")

# GET /trusted_list
@trusted_list.route("")
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

    # Build return object
    result = {
        'trusted_list': []
    }

    # Build trusted list
    current_app.logger.debug("Build trusted list")
    try:
        conf_list = satellite['trusted_list']

        # Iterate over trusted_list from config file
        for c in conf_list:
            entry = {}

            # Set status and validity
            entry['status'] = c['status']
            entry['validity'] = c['validity']

            # Load certificate and get subject
            subject_components = get_subject_components(c['crt'])
            sub = ''
            if len(subject_components) > 0:
                sub = '{} = {}'.format(subject_components[0][0], subject_components[0][1])
                for s in subject_components[1:]:
                    sub = '{},{} = {}'.format(sub,s[0], s[1])
            entry['subject'] = sub

            # Create SHA256 fingerprint
            cert = load_certificate(c['crt'])
            fingerprint = cert.digest('sha256').decode(FINGERPRINT_ENCODING).replace(':','')
            entry['certificate_fingerprint'] = fingerprint

            # Append trusted CA
            result['trusted_list'].append(entry)
            
    except KeyError as ke:
        current_app.logger.error('Could not load trusted list, config key not found: {}'.format(ke))
        abort(500)
    except Exception as ex:
        current_app.logger.error('Could not load trusted list: {}'.format(ex))
        abort(500)
        
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
    current_app.logger.debug("Encoding trusted_list_token JWT")
    current_app.logger.debug("{}".format(result))
    tl_token = ""
    try:
        tl_token = jwt.encode(result, get_private_key(satellite), algorithm="RS256", headers=header)
    except Exception as ex:
        current_app.logger.debug('Could not encode JWT for trusted_list_token: {}'.format(ex))
        abort(500)

    current_app.logger.debug("==> {}".format(tl_token))
    return {
        'trusted_list_token' : tl_token
    }, 200
