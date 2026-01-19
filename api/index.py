from flask import Flask, request, jsonify
import random
import string

app = Flask(__name__)

groups = {}

@app.route('/api/groups', methods=['GET', 'POST'])
def groups():
    if request.method == 'POST':
        data = request.get_json() or {}
        code = data.get('code', '').strip().upper()
        if len(code) == 10:
            if code not in groups:
                groups[code] = []
            return jsonify({'exists': True})
        return jsonify({'exists': False}), 400
    return jsonify(list(groups.keys())[:20])

@app.route('/api/create
