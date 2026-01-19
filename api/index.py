from flask import Flask, request, jsonify, make_response, session
import random
import string
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        return json.loads(user_data)
    return {'name': '', 'favorite_groups': []}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)

@app.route('/api/create-group', methods=['GET', 'POST'])
def create_group():
    user_data = get_user_data()
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    user_data['favorite_groups'].append(code)
    if len(user_data['favorite_groups']) > 10:
        user_data['favorite_groups'] = user_data['favorite_groups'][-10:]
    save_user_data(user_data)
    return jsonify({'code': code})

@app.route('/api/groups', methods=['GET'])
def groups_api():
    user_data = get_user_data()
    return jsonify(user_data['favorite_groups'])

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    user_data = get_user_data()
    if code not in user_data['favorite_groups']:
        return jsonify({'error': 'Private group not found'}), 404
    
    if not hasattr(app, 'private_messages'):
        app.private_messages = {}
    if code not in app.private_messages:
        app.private_messages[code] = []
    
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', user_data['name'] or 'Anonymous')[:20]
        text = data.get('text', '').strip()
        timestamp = data.get('timestamp', 'Now')
        if text:
            app.private_messages[code].append({'user': username, 'text': text, 'timestamp': timestamp})
            if len(app.private_messages[code]) > 500:
                app.private_messages[code] = app.private_messages[code][-500:]
        return jsonify({'status': 'sent'})
    return jsonify(app.private_messages.get(code, [])[-50:])

@app.route('/api/set-name', methods=['POST'])
def set_name():
    data = request.get_json() or {}
    name = data.get('name', '').strip()[:20]
    if name:
        user_data = get_user_data()
        user_data['name'] = name
        save_user_data(user_data)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid name'}), 400

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html><head><title>Private Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#000;color:#e0e0e0;height:100vh;overflow:hidden;}
.container{max
