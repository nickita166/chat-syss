from flask import Flask, request, jsonify, session
import random
import string
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-for-local-only')

users = {}
groups = {}

def require_login(f):
    def wrapper(*args, **kwargs):
        session_id = request.cookies.get('session')
        if not session_id or session_id not in users:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', '').strip()
    if not username or len(username) > 20:
        return jsonify({'success': False, 'error': 'Invalid username'}), 400
    
    session_id = f"user_{random.randint(1000,9999)}"
    users[session_id] = username
    response = jsonify({'success': True, 'user': username})
    response.set_cookie('session', session_id, httponly=True, samesite='Lax', max_age=86400*30)  # 30 days
    return response

@app.route('/user', methods=['GET'])
def get_user():
    session_id = request.cookies.get('session')
    username = users.get(session_id, None)
    if not username:
        return jsonify({'user': None, 'authenticated': False}), 401
    return jsonify({'user': username, 'authenticated': True})

@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session')
    if session_id in users:
        del users[session_id]
    response = jsonify({'success': True})
    response.delete_cookie('session')
    return response

@app.route('/groups', methods=['GET'])
@app.route('/create-group', methods=['POST'])
@app.route('/messages/<code>', methods=['GET', 'POST'])
@require_login
def protected_endpoints(*args, **kwargs):
    # These routes now require login via decorator
    if request.endpoint == 'protected_endpoints.groups':
        if request.method == 'POST':
            code = request.json.get('code', '').strip().upper()
            if len(code) != 10:
                return jsonify({'exists': False, 'error': 'Code must be 10 characters'}), 400
            if code not in groups:
                groups[code] = []
            return jsonify({'exists': True})
        return jsonify(list(groups.keys())[:20])
    
    if request.endpoint == 'protected_endpoints.create-group':
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if code not in groups:
                groups[code] = []
                return jsonify({'code': code})
    
    if request.endpoint == 'protected_endpoints.messages':
        code = kwargs['code']
        if code not in groups:
            return jsonify({'error': 'Group not found'}), 404
        
        if request.method == 'POST':
            data = request.json
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
