from flask import Flask, request, jsonify, session
import random
import string
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'dev-secret-key')

groups = {}

@app.route('/api/create-group', methods=['GET', 'POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups[code] = []
    return jsonify({'code': code})

@app.route('/api/groups', methods=['GET'])
def groups_api():
    return jsonify(list(groups.keys()))

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    if code not in groups:
        groups[code] = []
    
    if request.method
