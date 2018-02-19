"""
The purpose of this script is to call other scripts. There are no arguments to
this script. An environment variable named ACTION defines which action should
be taken (which script to run).
"""

import subprocess
import os
import json

def print_message(message):
    '''
    prints a JSON object with indentation if the DEBUG environment variable
    is set and without indentation if it is not set
    '''
    if os.getenv('DEBUG'):
        print (json.dumps(message, indent=4)
    else:
        print (json.dumps(message))

# return a message that the container has started
pigeon = {
    "status_code": 100,
    "data": {},
    "message": "Container has started."
}
print_message(pigeon)

if os.getenv('ACTION'):

    if os.environ['ACTION'] == 'TEST_CONNECTIVITY':
        subprocess.call(["python", "test_connectivity.py"])
    elif os.environ['ACTION'] == 'VERIFY_PARAMETERS':
        pigeon['message'] = "Requested action VERIFY_PARAMETERS not implemented."
        pigeon['status_code'] = 400
        print_message(pigeon)
    elif os.environ['ACTION'] == 'RUN_INTEGRATION':
        # pigeon['message'] = "Requested action RUN_INTEGRATION not implemented."
        # pigeon['status_code'] = 400
        # print_message(pigeon)
        subprocess.call(["python", "test_connectivity.py"])
    elif os.environ['ACTION'] == 'CUSTOM':
        pigeon['message'] = "Requested action CUSTOM not implemented."
        pigeon['status_code'] = 400
        print_message(pigeon)
    else:
        pigeon['message'] = "Requested action not recognized."
        pigeon['status_code'] = 404
        print_message(pigeon)
else:
    pigeon['message'] = "The ACTION environment variable is not defined."
    pigeon['status_code'] = 404
    print_message(pigeon)

# print a message that the container has completed its work
pigeon['message'] = "Container is stopping."
pigeon['status_code'] = 100
print_message(pigeon)
