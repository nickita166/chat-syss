from flask import Flask, request, jsonify, make_response
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production')

# In-memory storage for groups and messages
groups = {}  # {code: [{'user': 'name', 'text': 'msg', 'timestamp': '12:34 PM'}]}

@app.route('/api/groups', methods=['GET', 'POST'])
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
def create_group():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if code not in groups:
            groups[code] = []
            return jsonify({'code': code})

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    if code not in groups:
        return jsonify({'error': 'Group not found'}), 404
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', 'Anonymous')
        msg_data = {
            'user': username,
            'text': data.get('text', '').strip(),
            'timestamp': data.get('timestamp', '')
        }
        if msg_data['text']:
            groups[code].append(msg_data)
            # Keep only last 500 messages
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
        return jsonify({'status': 'sent'})
    
    # Return last 500 messages
    return jsonify(groups[code][-500:])

if __name__ == '__main__':
    app.run(debug=True)
