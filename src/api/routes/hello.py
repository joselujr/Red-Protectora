from flask import jsonify

from api.utils import dev_only

from . import api


@api.route('/hello', methods=['POST', 'GET'])
@dev_only()
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200
