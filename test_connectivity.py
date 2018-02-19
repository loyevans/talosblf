"""

******************** WARNING: TEST CODE! DO NOT USE ********************

Script tests for connectivity to both Cisco Tetration and Infoblox
endpoints. The bulk of the work in this script is handling all of the
errors that might arise.

Author: Doron Chosnek, Cisco Systems, February 2018
"""

# pylint: disable=invalid-name

import json
import os
import requests.packages.urllib3

# needed for Tetration
from tetpyclient import RestClient

# needed for Infoblox
from infoblox_client import connector
from infoblox_client import exceptions as ib_e

# ============================================================================
# Functions
# ----------------------------------------------------------------------------

def test_infoblox():
    '''
    Function attempts to connect to Infoblox. Arguments are retrieved from
    environment variables. The bulk of the work in this function is error
    handling. It returns a tuple that has a status code and an error message
    (which will be an empty string if there are no errors)
    '''

    # defaults are document here:
    # https://github.com/infobloxopen/infoblox-client/blob/master/infoblox_client/connector.py
    infoblox_opts = {
        'host': os.environ['INFOBLOX_HOST'],
        'username': os.environ['INFOBLOX_USER'],
        'password': os.environ['INFOBLOX_PWD'],
        'ssl_verify': False,
        'silent_ssl_warnings': True, # change from default
        'http_request_timeout': 3,   # change from default
        'http_pool_connections': 10,
        'http_pool_maxsize': 10,
        'max_retries': 2,            # change from default
        'wapi_version': os.environ['INFOBLOX_WAPI_VERSION'],
        'max_results': 2,            # change from default
        'log_api_calls_as_info': False,
        'paging': False
    }

    status = 100
    return_msg = "Infoblox connectivity verified."
    conn = connector.Connector(infoblox_opts)

    try:
        result = conn.get_object('networkview')
    except ib_e.InfobloxBadWAPICredential:
        return_msg = "Infoblox: invalid credentials"
        status = 400
    except ib_e.InfobloxTimeoutError:
        return_msg = "Infoblox: timeout"
        status = 400
    except:
        return_msg = "Infoblox: unknown error connecting to Infoblox"
        status = 400
    else:
        # if the result is None then we've hit a valid IP that is not an
        # Infoblox instance
        if result is None:
            return_msg = "Infoblox: Invalid endpoint. Check IB IP address."
            status = 400
        # if the result is not a list, we have some kind of invalid result
        elif type(result) is not list:
            return_msg = "Infoblox: " + str(result)
            status = 400

    return (status, return_msg)

def test_tetration():
    '''
    Function attempts to connect to Tetration. Arguments are retrieved from
    environment variables. The bulk of the work in this function is error
    handling. It returns a tuple that has a status code and an error message
    (which will be an empty string if there are no errors)
    '''
    status = 100
    return_msg = "Tetration connectivity verified."

    restclient = RestClient(
        os.environ['TETRATION_ENDPOINT'],
        api_key=os.environ['TETRATION_API_KEY'],
        api_secret=os.environ['TETRATION_API_SECRET'],
        verify=False
    )

    requests.packages.urllib3.disable_warnings()

    try:
        resp = restclient.get('/openapi/v1/filters/inventories')

    # most likely a DNS issue
    except requests.exceptions.ConnectionError as c_error:
        status = 404
        return_msg = "Error connecting to Tetration endpoint"
    except:
        status = 400
        return_msg = "Unknown error connecting to Tetration"
    else:
        # this doesn't work if the Tetration endpoint is specified as a valid
        # website (but not a TA endpoint) because it returns all of the HTML
        # for the whole website and it takes a long time to timeout
        if resp.status_code == 200:
            status = 100
        if resp.status_code >= 400:
            status = resp.status_code
            return_msg = "Tetration " + str(resp.text).rstrip()

    return (status, return_msg)

# ============================================================================
# Main
# ----------------------------------------------------------------------------

pigeon = {
    "status_code": 0,
    "data": {},
    "message": ""
}

error_flag = False

for c in [test_infoblox(), test_tetration()]:
    pigeon['status_code'], pigeon['message'] = c
    error_flag = True if c[0] >= 400 else error_flag
    if os.getenv('DEBUG'):
        print (json.dumps(pigeon, indent=4))
    else:
        print (json.dumps(pigeon))

if not error_flag:
    pigeon['status_code'] = 200
    pigeon['message'] = "All connectivity verified."
    if os.getenv('DEBUG'):
        print (json.dumps(pigeon, indent=4))
    else:
        print (json.dumps(pigeon))

