from flask import Flask, request, jsonify
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-change-me')
groups = {}  # {code: [{'user': 'name', 'text': 'msg', 'timestamp': '12:34'}]}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return open('public/index.html').read()

@app.route('/api/groups', methods=['GET', 'POST'])
def groups():
    if request.method == 'POST':
        data = request.get_json() or {}
        code = data.get('code', '').strip().upper()
        if len(code) == 10:
            if code not in groups:
                groups[code] = []
            return jsonify({'exists': True, 'code': code})
        return jsonify({'exists': False}), 400
    return jsonify(list(groups.keys())[:20])

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups[code] = []
    return jsonify({'code': code})

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    if code not in groups:
        return jsonify({'error': 'Group not found'}), 404
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', 'Anonymous')[:20]
        text = data.get('text', '').strip()
        timestamp = data.get('timestamp', 'Now')
        
        if text:
            groups[code].append({
                'user': username,
                'text': text,
                'timestamp': timestamp
            })
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
        return jsonify({'status': 'sent'})
    
    return jsonify(groups[code][-50:])

if __name__ == '__main__':
    app.run(debug=True)
