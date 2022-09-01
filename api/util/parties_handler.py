import os
from api.util.token_handler import get_subject_components_full
# Maximum of parties per page
MAX_PER_PAGE = int(os.environ.get('SATELLITE_MAX_PARTIES_PER_PAGE', 10))

# Request must contain at leat one of these parameters
MINIMUM_PARAMETERS = ['name', 'eori', 'certified_only', 'active_only', 'certificate_subject_name']

def to_bool(value):
    if value is None:
        return None
    
    if value.lower() in ['True', 'true']:
        return True
    elif value.lower() in ['False', 'false']:
        return False

    return None

# Check for parameter requirements (returns None if params ok)
def check_invalid_parameters(request):

    # Check for minimum parameters
    ok = False
    for p in MINIMUM_PARAMETERS:
        opt_param = request.args.get(p)
        if opt_param:
            ok = True
            break
    if not ok:
        return "At least one parameter needs to be specified"

    # Check certificate_subject_name vs eori
    opt_param = request.args.get('certificate_subject_name')
    if opt_param:
        eori_param = request.args.get('eori')
        if not eori_param:
            return "The certificate_subject_name should be used in combination with the eori parameter"
        if eori_param == "*":
            return "The eori parameter should not contain '*' when certificate_subject_name parameter is used"

    # Check booleans
    r_certified = request.args.get('certified_only')
    if (r_certified is not None) and (r_certified != 'null'):
        if to_bool(r_certified) is None:
            return "Invalid value {} for parameter certified_only".format(r_certified)
    r_active = request.args.get('active_only')
    if (r_active is not None) and (r_active != "null"):
        if to_bool(r_active) is None:
            return "Invalid value {} for parameter active_only".format(r_active)

    # Check page parameter > 0
    r_page = request.args.get('page')
    if (r_page is not None):
        try:
            page = r_page
            if not isinstance(r_page, int):
                page = int(r_page)
            if page < 1:
                return "Parameter 'page' must be > 0"
        except Exception as ex:
            return 'Parameter page cannot be converted to int: {}'.format(ex)
        
    return None

# Check certificate_subject_name of party certificate
def check_certificate_subject_name(certificate_subject_name, request_eori, party, app):

    app.logger.debug("Compare requested certificate subject name for {}".format(party['id']))
    
    # Get subject_name components from party certificate
    crt = party['crt']
    crt_subject_components : dict = get_subject_components_full(crt)

    # Split request subject_name components
    r_subject_components = []
    r_sub_array = certificate_subject_name.split(',')
    for s in r_sub_array:
        comp = s.strip().split('=')
        r_subject_components.append(comp)

    app.logger.debug("==> Requested: {}".format(r_subject_components))
    app.logger.debug("==> Certificate: {}".format(crt_subject_components))
      
    # check serial number
    if 'serialNumber' in crt_subject_components:
        if request_eori != crt_subject_components['serialNumber']:
            app.logger.debug("Wrong serialNumber in certificate subject name")
            return False  

    # Iterate over requested subject name attributes
    for r in r_subject_components:
        if r[0].strip() in crt_subject_components:
            if crt_subject_components[r[0].strip()] != r[1].strip():
                app.logger.debug("Certificate subject name does not match")
                return False

    app.logger.debug("Subject certificate name matched")
    return True

# Paginate parties_info
def paginate_parties(parties_info, page):

    # All parties
    full_data = parties_info['data']

    # Directly return empty list
    if len(full_data) < 1:
        return parties_info

    # Get subset
    page = int(page)
    start = (page-1)*MAX_PER_PAGE
    end = page * MAX_PER_PAGE
    data = parties_info['data'][int(start):int(end)]

    # Replace and return
    parties_info['data'] = data
    return parties_info

# Build parties_info
def get_parties_info(request, config, app):

    # Return object
    parties_info = {
        'count': 0,
        'data': []
    }

    # Iterate over parties
    if 'parties' not in config:
        app.logger.error('No parties specified in config')
        return parties_info
    for p in config['parties']:

        app.logger.debug("Compare request to participant: {}".format(p['id']))

        # Check for name
        r_name = request.args.get('name')
        if (r_name is not None) and (r_name != "*") and (r_name != p['name']):
            continue

        # Check for eori
        r_eori = request.args.get('eori')
        if (r_eori is not None) and (r_eori != "*") and (r_eori != p['id']):
            continue

        # Check for certifications
        r_certified = to_bool(request.args.get('certified_only'))
        if r_certified is not None:
            app.logger.debug("Check for requested participant certification")
            if (r_certified == True) and ('certifications' not in p):
                continue
            elif (r_certified == False) and ('certifications' in p):
                continue
                
        # Check for status
        r_active = to_bool(request.args.get('active_only'))
        if r_active is not None:
            app.logger.debug("Check for requested participant status")
            if (r_active == True) and (p['status'] != "Active"):
                continue
            elif (r_active == False) and (p['status'] == "Active"):
                continue

        # Check certificate_subject_name
        r_certificate_subject_name = request.args.get('certificate_subject_name')
        if r_certificate_subject_name is not None:
            if not check_certificate_subject_name(r_certificate_subject_name, r_eori, p, app):
                continue

        # Append data
        app.logger.debug("Participant '{}' passed, adding to result list".format(p['id']))
        parties_info['count'] += 1
        party = {
            'party_id': p['id'],
            'party_name': p['name'],
            "adherence": {
                "end_date": p['end_date'],
                "start_date": p['start_date'],
                "status": p['status']
            }
        }
        if 'certifications' in p:
            party['certifications'] = p['certifications']
        if 'capability_url' in p:
            party['capability_url'] = p['capability_url']
        parties_info['data'].append(party)
        
    # Return data
    return parties_info
