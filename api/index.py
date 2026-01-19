from flask import Flask, request, jsonify, make_response, session
from collections import defaultdict
import random
import string
import json
import os
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

groups = defaultdict(list)

def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        return json.loads(user_data)
    return {'name': '', 'favorite_groups': [], 'current_group': ''}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)
    session.permanent = True

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
        button.enabled{background:#0f0;}
        #nameSection,#groupSection{display:none;}
        #chatSection{display:none;flex-direction:column;height:100%;}
        #messages{max-height:50vh;overflow-y:auto;padding:10px;border:1px solid #333;margin:10px 0;}
        .msg{display:flex;margin:5px 0;flex-wrap:wrap;}
        .msg strong{color:#0f0;}
        .private{font-size:12px;color:#888;}
        .joined-ind{color:#0f0;font-size:12px;}
        #inputRow{display:flex;gap:10px;align-items:end;}
        #messageInput{flex:1;}
    </style>
</head>
<body>
    <div class="container">
        <div id="nameSection">
            <input id="nameInput" placeholder="Enter your name" autofocus maxlength="20">
            <br><br><button onclick="saveName()">Start Chatting</button>
        </div>
        
        <div id="groupSection">
            <select id="groupSelect" onchange="joinGroup()">
                <option value="">Select or create group</option>
            </select>
            <br><br>
            <button id="copyInvite" onclick="copyInvite()" style="display:none;background:#0066cc;">Copy Invite Link</button>
            <br><br>
            <button onclick="createGroup()" style="background:#cc6600;">New Private Group</button>
            <div id="joinStatus"></div>
        </div>
        
        <div id="chatSection">
            <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
                <strong id="currentGroupDisplay"></strong>
                <button id="copyInviteChat" onclick="copyInvite()" style="font-size:12px;padding:6px;">📋</button>
            </div>
            <div id="messages"></div>
            <div id="inputRow">
                <input id="messageInput" placeholder="Type message..." disabled maxlength="500">
                <button id="sendBtn" onclick="sendMessage()" disabled>Send</button>
            </div>
        </div>
    </div>
    <script>
        let currentGroup = '';
        let userName = '';

        function init() {
            const hash = window.location.hash.slice(1);
            if (hash && hash.match(/^[A-Z0-9]{10}$/)) {
                currentGroup = hash;
                document.getElementById('joinStatus').innerHTML = `✅ Joined group ${currentGroup}`;
            }
            
            fetchName().then(() => {
                if (userName) {
                    showGroups();
                    if (currentGroup) {
                        setTimeout(() => joinGroupDirect(currentGroup), 500);
                    }
                } else {
                    showName();
                }
            });
            
            setInterval(loadMessages, 2000);
        }

        async function fetchName() {
            try {
                const res = await fetch('/api/user');
                const data = await res.json();
                userName = data.name || '';
                currentGroup = data.currentGroup || '';
            } catch(e) {}
        }

        async function saveName() {
            userName = document.getElementById('nameInput').value.trim() || 'Anonymous';
            try {
                await fetch('/api/save-user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: userName, favorite_groups: []}),
                    credentials: 'include'
                });
            } catch(e) {}
            showGroups();
        }

        async function loadGroups() {
            try {
                const res = await fetch('/api/groups', {credentials: 'include'});
                const data = await res.json();
                const select = document.getElementById('groupSelect');
                const currentOpt = select.querySelector(`[value="${currentGroup}"]`);
                select.innerHTML = '<option value="">Your private groups</option>';
                data.groups.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g.code;
                    opt.textContent = `${g.code} (private)`;
                    select.appendChild(opt);
                });
                if (currentOpt) select.value = currentGroup;
            } catch(e) {}
        }

        function showName() { 
            document.getElementById('nameSection').style.display = 'block'; 
        }
        
        function showGroups() {
            document.getElementById('groupSection').style.display = 'block';
            loadGroups();
        }
        
        function enableChat() {
            document.getElementById('chatSection').style.display = 'flex';
            document.getElementById('groupSection').style.display = 'none';
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('sendBtn').classList.add('enabled');
            document.getElementById('messageInput').classList.add('enabled');
            document.getElementById('currentGroupDisplay').textContent = currentGroup || 'No group';
            loadMessages();
        }

        async function joinGroupDirect(code) {
            currentGroup = code;
            await saveUserData();
            await loadGroups();
            enableChat();
        }

        async function createGroup() {
            try {
                const res = await fetch('/api/create-group', {method: 'POST', credentials: 'include'});
                const data = await res.json();
                currentGroup = data.code;
                await saveUserData();
                await loadGroups();
                enableChat();
            } catch(e) {
                alert('Create failed');
            }
        }

        async function joinGroup() {
            const code = document.getElementById('groupSelect').value;
            if (code) {
                currentGroup = code;
                await saveUserData();
                enableChat();
            }
        }

        async function saveUserData() {
            try {
                await fetch('/api/save-user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({current_group: currentGroup}),
                    credentials: 'include'
                });
            } catch(e) {}
        }

        function copyInvite() {
            if (currentGroup) {
                const inviteUrl = `${window.location.origin}/#${currentGroup}`;
                navigator.clipboard.writeText(inviteUrl).then(() => {
                    const btn = document.getElementById('copyInvite') || document.getElementById('copyInviteChat');
                    const original = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => btn.textContent = original, 2000);
                });
            }
        }

        async function sendMessage() {
            const msg = document.getElementById('messageInput').value.trim();
            if (msg && currentGroup) {
                try {
                    await fetch('/api/send', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({group: currentGroup, msg: msg}),
                        credentials: 'include'
                    });
                    document.getElementById('messageInput').value = '';
                    loadMessages();
                } catch(e) {}
            }
        }

        async function loadMessages() {
            if (!currentGroup) return;
            try {
                const res = await fetch(`/api/messages/${currentGroup}`, {credentials: 'include'});
                const msgs = await res.json();
                const div = document.getElementById('messages');
                div.innerHTML = msgs.map(m => 
                    `<div class="msg"><strong>${m.user}:</strong> ${m.msg} <small style="color:#888;">${m.time}</small></div>`
                ).join('');
                div.scrollTop = div.scrollHeight;
            } catch(e) {}
        }

        // Enter to send
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !document.getElementById('messageInput').disabled) {
                sendMessage();
            }
        });

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
    data = request.json or {}
    user_data = get_user_data()
    user_data.update(data)
    save_user_data(user_data)
    return jsonify({'status': 'saved'})

@app.route('/api/groups')
def get_groups():
    data = get_user_data()
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
    if code not in user_data['favorite_groups']:
        user_data['favorite_groups'].append(code)
    save_user_data(user_data)
    resp = make_response(jsonify({'code': code}))
    return resp

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    group = data.get('group')
    msg = data.get('msg', '')[:500]
    if group and msg:
        user_data = get_user_data()
        msg_data = {
            'user': user_data['name'] or 'Anonymous',
            'msg': msg,
            'time': datetime.now().strftime('%-I:%M %p')
        }
        groups[group].append(msg_data)
        if len(groups[group]) > 50:
            groups[group] = groups[group][-50:]
    return jsonify({'status': 'sent'})

@app.route('/api/messages/<code>')
def get_messages(code):
    msgs = groups.get(code, [])
    return jsonify(msgs)

if __name__ == '__main__':
    app.run(debug=True)
