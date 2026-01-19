from flask import Flask, request, jsonify, make_response
from functools import wraps
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')

users = {}
groups = {}

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session')
        if not session_id or session_id not in users:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip() if data else ''
    
    if not username or len(username) > 20:
        return jsonify({'success': False, 'error': 'Invalid username'}), 400
    
    session_id = f"user_{random.randint(1000,9999)}"
    users[session_id] = username
    
    response = make_response(jsonify({'success': True, 'user': username}))
    response.set_cookie('session', session_id, httponly=True, samesite='Lax', max_age=86400*30)
    return response

@app.route('/api/user', methods=['GET'])
def get_user():
    session_id = request.cookies.get('session')
    username = users.get(session_id)
    if not username:
        return jsonify({'user': None, 'authenticated': False})
    return jsonify({'user': username, 'authenticated': True})

@app.route('/api/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session')
    if session_id in users:
        del users[session_id]
    response = make_response(jsonify({'success': True}))
    response.delete_cookie('session')
    return response

@app.route('/api/groups', methods=['GET'])
@app.route('/api/groups', methods=['POST'])
@require_login
def groups():
    if request.method == 'POST':
        data = request.get_json()
        code = data.get('code', '').strip().upper() if data else ''
        if len(code) != 10:
            return jsonify({'exists': False, 'error': 'Code must be 10 characters'}), 400
        if code not in groups:
            groups[code] = []
        return jsonify({'exists': True})
    return jsonify(list(groups.keys())[:20])

@app.route('/api/create-group', methods=['POST'])
@require_login
def create_group():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if code not in groups:
            groups[code] = []
            return jsonify({'code': code})

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
@require_login
def messages(code):
    if code not in groups:
        return jsonify({'error': 'Group not found'}), 404
    
    if request.method == 'POST':
        data = request.get_json()
        session_id = request.cookies.get('session')
        user = users.get(session_id, 'Anonymous')
        msg_data = {
            'user': user,
            'text': data.get('text', '').strip(),
            'timestamp': data.get('timestamp', '')
        }
        if msg_data['text']:
            groups[code].append(msg_data)
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
        return jsonify({'status': 'sent'})
    
    return jsonify(groups[code][-500:])

if __name__ == '__main__':
    app.run(debug=True)
