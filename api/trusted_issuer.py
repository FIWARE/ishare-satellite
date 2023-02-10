import base64
from distutils.command.config import config
import re
from this import d
from hashlib import sha256
from webbrowser import get
from flask import Blueprint, Response, current_app, abort, request
from api.util.parties_handler import get_parties_info
from api.util.token_handler import validate_jwt, get_authorization_header, get_subject_components, load_certificate, get_x5c_chain
from api.util.config_handler import get_private_key, get_certificates
import json


# Implementation of the EBSI TrustedIssuers-Registry API. See https://api-pilot.ebsi.eu/docs/apis/trusted-issuers-registry/latest#/

# Blueprint
trusted_issuer = Blueprint("trusted_issuer", __name__, url_prefix="/trusted_issuer")

@trusted_issuer.route("/v3/issuers/<did>")
def getIssuer(did: str): 

    current_app.logger.info("Get issuer " + did)

    # Load config
    satellite = current_app.config['satellite']

    parties_list = satellite['parties']
    current_app.logger.info("Get parties")

    result = {
        'did': did,
        'attributes': []
    }

    for c in parties_list:
        if 'did' in c and c['did'] == did:
            # collect the attributes
            if 'crt' in c: 
                result['attributes'].append(getAttribute({'certificate': c['crt']}))
            if 'name' in c: 
                result['attributes'].append(getAttribute({'name': c['name']}))
            if 'status' in c: 
                result['attributes'].append(getAttribute({'status': c['status']}))
            if 'id' in c: 
                result['attributes'].append(getAttribute({'id': c['id']}))
            if 'start_date' in c: 
                result['attributes'].append(getAttribute({'start_date': c['start_date']}))
            if 'end_date' in c: 
                result['attributes'].append(getAttribute({'end_date': c['end_date']}))
            result['attributes'].append(getAttribute({'type': 'attribute', 'name': 'issuer'}))
            return result
    abort(Response("No such issuer found.", 404)) 



def getAttribute(body: dict):
    payloadBytes = json.dumps(body).encode('utf-8')
    return {
        'body': base64.b64encode(payloadBytes).decode('utf-8'),
        'hash': sha256(payloadBytes).hexdigest()
    }



# GET /trusted_issuers
@trusted_issuer.route("/v3/issuers")
def getIssuers():

    # Load config
    satellite = current_app.config['satellite']

    pageAfter = get_with_default(request,'page[after]', -1)
    pageSize = get_with_default(request,'page[size]',100)

    total = 0
    # Build return object
    result = {
        'items': [],
        'total': total,
        'pageSize': pageSize
    }


    if 'host' in satellite: 
        result['self'] = satellite['host'] + 'trusted-issuers-registry/v3/issuers'

    # Build issuers list
    current_app.logger.info("Build issuers list")

    
    parties_list = satellite['parties']

    allParties = []

    # Iterate over trusted_list from config file
    for c in parties_list:
        if 'did' not in c:
            current_app.logger.debug("No did, skip")
            continue

        total += 1

        entry = {
            'did': c['did']
        }

        allParties.append(entry)

    lastIndex = pageAfter + 1 + pageSize 

    if lastIndex > len(allParties):
        lastIndex = len(allParties)

    result['items'] = allParties[pageAfter+1:lastIndex]
    result['total'] = total
    result['pageSize'] = pageSize

    return result

def get_with_default(request, param: str, default: int) -> int:

    paramValue = request.args.get(param)
    if paramValue is None: 
        return default
    else:
        int(paramValue)

    

    
      
