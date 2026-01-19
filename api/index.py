from flask import Flask, request, jsonify, make_response, session
from collections import defaultdict
import random
import string
import json
import os
from datetime import datetime

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
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;background:#000;color:#e0e0e0;}
        body{height:100vh;overflow:hidden;}
        .container{max-width:480px;margin:0 auto;height:100vh;display:flex;flex-direction:column;padding:10px;}
        input,button,select{font-size:16px;padding:12px;border:1px solid #333;border-radius:8px;background:#111;color:#e0e0e0;}
        button{cursor:pointer;background:#222;margin:5px 0;}
        button:active{background:#444;}
        button.enabled{background:#0f0;color:#000;}
        #nameSection{display:none;}
        #mainUI{display:flex;flex-direction:column;height:100%;gap:10px;}
        #groupControls{display:flex;flex-direction:column;gap:10px;padding:10px;border:1px solid #333;}
        #groupSelect{width:100%;}
        #messages{max-height:55vh;overflow-y:auto;padding:10px;border:1px solid #333;}
        .msg{display:flex;margin:5px 0;flex-wrap:wrap;}
        .msg strong{color:#0f0;}
        .time{color:#888;font-size:12px;}
        .joined-ind{color:#0f0;font-size:12px;}
        #inputRow{display:flex;gap:10px;align-items:end;}
        #messageInput{flex:1;}
        .group-header{display:flex;justify-content:space-between;align-items:center;padding:10px;background:#111;border-radius:8px;}
    </style>
</head>
<body>
    <div class="container">
        <div id="nameSection">
            <input id="nameInput" placeholder="Enter your name" autofocus maxlength="20">
            <br><br><button onclick="saveName()">Start Chatting</button>
        </div>
        
        <div id="mainUI" style="display:none;">
            <div class="group-header">
                <strong id="currentGroupDisplay">No group selected</strong>
                <button id="copyInviteChat" onclick="copyInvite()" style="font-size:14px;padding:8px;">📋 Invite</button>
            </div>
            
            <div id="groupControls">
                <select id="groupSelect" onchange="switchGroup()">
                    <option value="">-- Switch Groups --</option>
                </select>
                <button onclick="createGroup()" style="background:#cc6600;">New Private Group</button>
                <div id="joinStatus"></div>
            </div>
            
            <div id="messages"></div>
            
            <div id="inputRow">
                <input id="messageInput" placeholder="Select a group to chat" disabled maxlength="500">
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
                    showMainUI();
                    if (currentGroup) {
                        setTimeout(() => switchGroup(currentGroup), 500);
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
                    body: JSON.stringify({name: userName}),
                    credentials: 'include'
                });
            } catch(e) {}
            showMainUI();
            loadGroups();
        }

        async function loadGroups() {
            try {
                const res = await fetch('/api/groups', {credentials: 'include'});
                const data = await res.json();
                const select = document.getElementById('groupSelect');
                select.innerHTML = '<option value="">-- Switch Groups --</option>';
                data.groups.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g.code;
                    opt.textContent = `${g.code} (private)`;
                    select.appendChild(opt);
                });
                if (currentGroup) {
                    select.value = currentGroup;
                    updateChatStatus();
                }
            } catch(e) {}
        }

        function showName() { 
            document.getElementById('nameSection').style.display = 'block'; 
        }
        
        function showMainUI() {
            document.getElementById('mainUI').style.display = 'flex';
            document.getElementById('nameSection').style.display = 'none';
            loadGroups();
        }

        function updateChatStatus() {
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const groupDisplay = document.getElementById('currentGroupDisplay');
            
            if (currentGroup) {
                input.disabled = false;
                sendBtn.disabled = false;
                sendBtn.classList.add('enabled');
                input.placeholder = 'Type message...';
                groupDisplay.textContent = currentGroup;
                loadMessages();
            } else {
                input.disabled = true;
                sendBtn.disabled = true;
                sendBtn.classList.remove('enabled');
                input.placeholder = 'Select a group to chat';
                groupDisplay.textContent = 'No group selected';
                document.getElementById('messages').innerHTML = '';
            }
        }

        async function switchGroup(code = null) {
            const selectValue = code || document.getElementById('groupSelect').value;
            if (selectValue) {
                currentGroup = selectValue;
                await saveUserData();
                document.getElementById('groupSelect').value = currentGroup;
                updateChatStatus();
                document.getElementById('joinStatus').innerHTML = `✅ Switched to ${currentGroup}`;
                setTimeout(() => document.getElementById('joinStatus').innerHTML = '', 2000);
            }
        }

        async function createGroup() {
            try {
                const res = await fetch('/api/create-group', {method: 'POST', credentials: 'include'});
                const data = await res.json();
                currentGroup = data.code;
                await saveUserData();
                loadGroups();
                updateChatStatus();
                document.getElementById('joinStatus').innerHTML = `✅ Created ${currentGroup}`;
            } catch(e) {
                document.getElementById('joinStatus').innerHTML = '❌ Create failed';
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
                    const btn = document.getElementById('copyInviteChat');
                    const original = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => btn.textContent = '📋 Invite', 2000);
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
                    `<div class="msg"><strong>${m.user}:</strong> ${m.msg} <span class="time"> ${m.time}</span></div>`
                ).join('');
                div.scrollTop = div.scrollHeight;
            } catch(e) {}
        }

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

# API endpoints (unchanged)
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
