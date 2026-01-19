from flask import Flask, request, jsonify
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-123')

# Storage for groups and messages (in-memory)
groups = {}

@app.route('/api/groups', methods=['GET', 'POST'])
def api_groups():
    if request.method == 'POST':
        data = request.get_json() or {}
        code = data.get('code', '').strip().upper()
        if len(code) != 10:
            return jsonify({'exists': False, 'error': 'Code must be 10 chars'}), 400
        if code not in groups:
            groups[code] = []
        return jsonify({'exists': True})
    return jsonify(list(groups.keys())[:20])

@app.route('/api/create-group', methods=['POST'])
def api_create_group():
    attempts = 0
    while attempts < 100:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if code not in groups:
            groups[code] = []
            return jsonify({'code': code})
        attempts += 1
    return jsonify({'error': 'Failed to create group'}), 500

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def api_messages(code):
    code = code.strip().upper()
    
    if code not in groups:
        return jsonify({'error': 'Group not found'}), 404
    
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', 'Anonymous').strip()
        text = data.get('text', '').strip()
        timestamp = data.get('timestamp', '')
        
        if text and len(text) <= 500:
            msg = {
                'user': username[:20],  # Max 20 chars
                'text': text,
                'timestamp': timestamp
            }
            groups[code].append(msg)
            # Keep only last 500 messages
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
            return jsonify({'status': 'sent'})
        return jsonify({'error': 'Invalid message'}), 400
    
    # GET - return last 50 messages (for speed)
    return jsonify(groups[code][-50:])

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
