from flask import Flask, Response, json, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, close_room
import random

import session_manager
from session_status import SessionStatus

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)


@app.route('/')
def hello():
    return "Hello Decode!"


@socketio.on('join_room')
def socket_onboarding(data):
    join_room(data['room'])


@app.route('/init_onboarding', methods=['POST'])
def init_onboarding_request():
    # TODO: check who is requesting onboarding session, ip check/zenroom?
    # print("Not yet checked who is requesting onboarding session!")

    request_type = "onboarding"
    description = "I want to start onboarding session"

    session_id = session_manager.init_session(request_type, description)
    return json_response({'session_id': session_id})


@app.route("/attach_public_key", methods=['POST'])
def attach_public_key():
    data = request.get_data()
    data_json = json.loads(data)
    public_key = data_json['public_key']
    session_id = data_json['session_id']

    data = {"public_key": public_key}

    session_status = SessionStatus.GOT_PUB_KEY.value
    session = session_manager.append_session_data(session_id, data, session_status)
    
    socketio.emit('status_update', {'status': session_status}, room=session['id'])

    return json_response({"response": session})


@app.route("/attach_encrypted_data", methods=['POST'])
def attach_encrypted_data():
    data = request.get_data()
    data_json = json.loads(data)
    encrypted_data = data_json['encrypted_data']
    session_id = data_json['session_id']

    data = {"encrypted": encrypted_data}
    session_status = SessionStatus.GOT_ENCR_DATA.value
    session = session_manager.append_session_data(session_id, data, session_status)

    socketio.emit('status_update', {'status': session_status}, room=session['id'])
    
    # close_room(session['id'])

    return json_response({"response": session})


@app.route('/init_disclosure', methods=['POST'])
def init_disclosure_request():
    data = request.get_data()
    data_json = json.loads(data)
    attribute_request = data_json['attribute_request']
    description = data_json['description']

    session_id = session_manager.init_session(attribute_request, description)
    return json_response({'session_id': session_id})


@app.route('/get_session', methods=['POST'])
def get_session():
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']

    response = session_manager.get_session(session_id)
    return json_response({'response': response})


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
