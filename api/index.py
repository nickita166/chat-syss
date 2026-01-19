from flask import Flask, request, jsonify, make_response, session
from collections import defaultdict
import random
import string
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

# In-memory storage (Vercel serverless resets, but sessions persist user data)
groups = defaultdict(list)

def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        return json.loads(user_data)
    return {'name': '', 'favorite_groups': []}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)
    session.permanent = True  # Persist across sessions

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🔒 Private Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;background:#000;color:#e0e0e0;}
        body{height:100vh;overflow:hidden;}
        .container{max-width:480px;margin:0 auto;height:100vh;display:flex;flex-direction:column;padding:10px;}
        input,button{font-size:16px;padding:12px;border:1px solid #333;border-radius:8px;background:#111;color:#e0e0e0;}
        button{cursor:pointer;background:#222;}
        button:active{background:#444;}
        #nameSection,#groupSection{display:none;}
        #chatSection{display:none;flex-direction:column;height:100%;}
        #messages{max-height:60vh;overflow-y:auto;padding:10px;border:1px solid #333;margin:10px 0;}
        .msg{display:flex;margin:5px 0;}
        .msg strong{color:#0f0;}
        .private{font-size:12px;color:#888;}
        #goBtn{display:none;}
    </style>
</head>
<body>
    <div class="container">
        <div id="nameSection">
            <input id="nameInput" placeholder="Enter your name" autofocus>
            <br><button onclick="saveName()">Start Chatting</button>
        </div>
        <div id="groupSection">
            <select id="groupSelect"><option>Your private groups</option></select>
            <br><button id="copyInvite" onclick="copyInvite()">Copy Invite Link</button>
            <br><button onclick="createGroup()">New Private Group</button>
        </div>
        <div id="chatSection">
            <div id="messages"></div>
            <input id="messageInput" placeholder="Type message..." disabled>
            <button id="sendBtn" onclick="sendMessage()" disabled>Send</button>
        </div>
    </div>
    <script>
        let currentGroup = '';
        let userName = '';

        function init() {
            fetchName().then(() => {
                if (userName) showGroups(); else showName();
            });
            setInterval(loadMessages, 2000);
        }

        async function fetchName() {
            const res = await fetch('/api/user');
            const data = await res.json();
            userName = data.name;
            currentGroup = data.currentGroup || '';
            if (currentGroup) loadGroups().then(showChat);
        }

        async function saveName() {
            userName = document.getElementById('nameInput').value || 'Anonymous';
            await fetch('/api/save-user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: userName, favorite_groups: []}),
                credentials: 'include'
            });
            showGroups();
        }

        async function loadGroups() {
            const res = await fetch('/api/groups', {credentials: 'include'});
            const data = await res.json();
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option>Your private groups</option>';
            data.groups.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g.code;
                opt.textContent = `${g.code} ${g.private ? '(private)' : ''}`;
                select.appendChild(opt);
            });
        }

        function showName() { document.getElementById('nameSection').style.display = 'block'; }
        function showGroups() {
            document.getElementById('groupSection').style.display = 'block';
            loadGroups();
        }
        function showChat() {
            document.getElementById('chatSection').style.display = 'flex';
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('groupSelect').onchange = joinGroup;
            loadMessages();
        }

        async function createGroup() {
            const res = await fetch('/api/create-group', {method: 'POST', credentials: 'include'});
            const data = await res.json();
            currentGroup = data.code;
            await saveUserData();
            await loadGroups();
            document.getElementById('groupSelect').value = data.code;
            showChat();
        }

        async function joinGroup() {
            const code = document.getElementById('groupSelect').value;
            if (code) {
                currentGroup = code;
                await saveUserData();
                loadMessages();
            }
        }

        function copyInvite() {
            const code = currentGroup;
            if (code) {
                navigator.clipboard.writeText(`https://${window.location.host}/#${code}`);
                document.getElementById('copyInvite').textContent = 'Copied!';
                setTimeout(() => document.getElementById('copyInvite').textContent = 'Copy Invite Link', 2000);
            }
        }

        async function saveUserData() {
            await fetch('/api/save-user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({current_group: currentGroup}),
                credentials: 'include'
            });
        }

        async function sendMessage() {
            const msg = document.getElementById('messageInput').value;
            if (msg && currentGroup) {
                await fetch('/api/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({group: currentGroup, msg: msg}),
                    credentials: 'include'
                });
                document.getElementById('messageInput').value = '';
                loadMessages();
            }
        }

        async function loadMessages() {
            if (!currentGroup) return;
            const res = await fetch(`/api/messages/${currentGroup}`, {credentials: 'include'});
            const msgs = await res.json();
            const div = document.getElementById('messages');
            div.innerHTML = msgs.map(m => 
                `<div class="msg"><strong>${m.user}:</strong> ${m.msg} <small>${m.time}</small></div>`
            ).join('');
            div.scrollTop = div.scrollHeight;
        }

        window.onload = init;
    </script>
</body>
</html>
    '''

@app.route('/api/user')
def get_user():
    data = get_user_data()
    resp = make_response(jsonify({'name': data['name'], 'currentGroup': data.get('current_group', '')}))
    return resp

@app.route('/api/save-user', methods=['POST'])
def save_user():
    data = request.json
    user_data = get_user_data()
    user_data.update(data)
    save_user_data(user_data)
    return jsonify({'status': 'saved'})

@app.route('/api/groups')
def get_groups():
    data = get_user_data()
    # Simulate user's private groups
    user_groups = data.get('favorite_groups', [])
    resp = make_response(jsonify({'groups': [{'code': g, 'private': True} for g in user_groups[:10]]}))
    return resp

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups[code] = []
    user_data = get_user_data()
    if 'favorite_groups' not in user_data:
        user_data['favorite_groups'] = []
    user_data['favorite_groups'].append(code)
    save_user_data(user_data)
    resp = make_response(jsonify({'code': code}))
    return resp

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    if data['group'] in groups:
        msg_data = {
            'user': get_user_data()['name'] or 'Anonymous',
            'msg': data['msg'][:500],
            'time': datetime.now().strftime('%-I:%M %p')
        }
        groups[data['group']].append(msg_data)
        if len(groups[data['group']]) > 50:
            groups[data['group']] = groups[data['group']][-50:]
    return jsonify({'status': 'sent'})

@app.route('/api/messages/<code>')
def get_messages(code):
    msgs = groups.get(code, [])
    return jsonify(msgs)

if __name__ == '__main__':
    app.run(debug=True)
