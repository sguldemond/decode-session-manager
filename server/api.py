from flask import Flask, Response, json, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, close_room
import random
import logging

import session_manager
from session_status import SessionStatus

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


@app.route('/')
def hello():
    return "Hello Decode!"


@socketio.on('join_room')
def socket_onboarding(data):
    """
    Socket endpoint for joining a SocketIO room.
    The room name is always an active session ID.
    It can be joined by a MRTD scanner and a single client PWA during the onboarding process.
    Or by two client PWAs during a disclosure process.

    :param dict data: data attached when emited to this socket endpoint, must contain active session ID
    """
    #TODO:
    # checking if session ID is valid, respond if it isn't, handle response in clients
    
    session_id = data['session_id']
    join_room(session_id)

    logging.info("Room [{0}] joined by client [{1}]".format(session_id, request.sid))


@app.route('/init_onboarding', methods=['POST'])
def init_onboarding_request():
    """
    Endpoint called exclusively by the MRTD scanner to initialize a session

    :return: session id of newly created session
    :rtype: uuid4 string
    """
    # TODO: check who is requesting onboarding session, ip check/zenroom?
    # print("Not yet checked who is requesting onboarding session!")

    request_type = "onboarding"
    description = "I want to start onboarding session"

    session_id = session_manager.init_session(request_type, description)

    logging.info("New session was initialized [{}]".format(session_id))

    return json_response({'session_id': session_id})


@app.route("/attach_public_key", methods=['POST'])
def attach_public_key():
    """
    Endpoint called by client PWA in order to attach a public key to a session.
    Method will emit a status update to notify the MRTD scanner of this change.
    
    Request data must contain:
    - ['session_id']: Session ID of active session to attach public key to
    - ['public_key']: The public key

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    public_key = data_json['public_key']

    data = {"public_key": public_key}

    session_status = SessionStatus.GOT_PUB_KEY.value
    session = session_manager.append_session_data(session_id, data, session_status)

    logging.info("Public key was attached to session [{}]".format(session_id))
    
    socketio.emit('status_update', {'status': session_status}, room=session['id'])

    return json_response({"response": session})


@app.route("/attach_encrypted_data", methods=['POST'])
def attach_encrypted_data():
    """
    Endpoint called by MRTD scanner exclusively to attach encrypted data to a session.
    Method will emit a status update to notify the client PWA of this change.

    Request data must contain:
    - ['session_id']: Session ID of active session to attach encrypted data to
    - ['encrypted_data']: The encrypted data

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    encrypted_data = data_json['encrypted_data']

    data = {"encrypted": encrypted_data}
    session_status = SessionStatus.GOT_ENCR_DATA.value
    session = session_manager.append_session_data(session_id, data, session_status)

    logging.info("Encrypted data was attached to session [{}]".format(session_id))

    socketio.emit('status_update', {'status': session_status}, room=session['id'])
    
    # close_room(session['id'])

    return json_response({"response": session})


@app.route('/get_session', methods=['POST'])
def get_session():
    """
    Endpoint called for retrieving entire session, can be called by MRTD scanner and client PWA.

    Request data must contain:
    - ['session_id']: Session ID of session to be returned

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']

    session = session_manager.get_session(session_id)

    logging.info("Returning session [{}]".format(session_id))

    return json_response({'response': session})


@app.route('/init_disclosure', methods=['POST'])
def init_disclosure_request():
    data = request.get_data()
    data_json = json.loads(data)
    attribute_request = data_json['attribute_request']
    description = data_json['description']

    session_id = session_manager.init_session(attribute_request, description)

    #TODO: logging

    return json_response({'session_id': session_id})


@app.route('/get_session_status', methods=['POST'])
def get_session_status():
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']

    # TODO: rename 'response' > 'status'
    response = session_manager.get_session_status(session_id)
    return json_response({'response': response})


# NOT FUNCTIONAL:
# @app.route('/accept_request', methods=['POST'])

# NOT FUNCTIONAL:
# @app.route('/deny_request', methods=['POST'])


@app.route('/get_active_sessions', methods=['GET'])
def get_active_sessions():
    return json_response(session_manager.active_sessions)


def json_response(data):
    response = Response(
        response=json.dumps(data),
        status=200,
        mimetype='application/json',
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
