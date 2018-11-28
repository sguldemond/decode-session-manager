from uuid import uuid4

active_sessions = []

def init_session(attribute_request, description):
    new_session_id = str(uuid4())
    new_session = {'id': new_session_id, 
                   'request': attribute_request,
                   'description': description,
                   'data': None,
                   'status': 'INITIALIZED'}
    active_sessions.append(new_session)
    return new_session_id


def get_session(session_id):
    for session in active_sessions:
        if session['id'] == session_id:
            if session['status'] == 'INITIALIZED':
                session['status'] = 'STARTED'
                return session
            else:
                return session

    return "Session not found"


def get_session_status(session_id):
    for session in active_sessions:
        if session['id'] == session_id:
            return session['status']

    return "Session not found"


def append_session_data(session_id, data, status):
    for session in active_sessions:
        if session['id'] == session_id:
            session['data'] = data
            session['status'] = status

            return session
    # TODO: return error if session doesn't exist
    # could be helper method used across session manager


def end_session(session_id):
    for session in active_sessions:
        if session['id'] == session_id:
            session_to_end = session
            break

    if session_to_end is None:
        return "Session not found"

    active_sessions.remove(session_to_end)
    print("Session ended with ID: " + session_to_end['id'])

    return "Session ended"

