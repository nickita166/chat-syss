from flask import Flask, request, jsonify, make_response, session
import random
import string
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'devkey-change-production')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 365  # 1 year

def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        try:
            return json.loads(user_data)
        except:
            pass
    return {'name': '', 'favorite_groups': []}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)
    session.modified = True

def get_groups():
    groups_data = session.get('groups', '{}')
    try:
        return json.loads(groups_data) if groups_data else {}
    except:
        return {}

def save_groups(groups_data):
    session['groups'] = json.dumps(groups_data)
    session.modified = True

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/set-name', methods=['POST'])
def set_name():
    data = request.get_json()
    user_data = get_user_data()
    user_data['name'] = data.get('name', '').strip()[:20]
    save_user_data(user_data)
    resp = make_response(jsonify({'status': 'ok'}))
    resp.set_cookie('sessionid', session.sid, max_age=31536000)
    return resp

@app.route('/api/groups')
def get_groups_api():
    user_data = get_user_data()
    groups = get_groups()
    return jsonify({'groups': list(groups.keys()), 'favorite_groups': user_data['favorite_groups']})

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups = get_groups()
    groups[code] = []
    save_groups(groups)
    user_data = get_user_data()
    if code not in user_data['favorite_groups']:
        user_data['favorite_groups'].append(code)
        save_user_data(user_data)
    resp = make_response(jsonify({'code': code}))
    resp.set_cookie('sessionid', session.sid, max_age=31536000)
    return resp

@app.route('/api/join-group/<code>')
def join_group(code):
    groups = get_groups()
    if code not in groups:
        groups[code] = []
        save_groups(groups)
    user_data = get_user_data()
    if code not in user_data['favorite_groups']:
        user_data['favorite_groups'].append(code)
        save_user_data(user_data)
    resp = make_response(jsonify({'status': 'joined'}))
    resp.set_cookie('sessionid', session.sid, max_age=31536000)
    return resp

@app.route('/api/messages/<code>')
def get_messages(code):
    groups = get_groups()
    messages = groups.get(code, [])[-50:]
    user_data = get_user_data()
    username = user_data['name'] or 'Anonymous'
    
    messages_html = ''
    for msg in messages:
        time_str = datetime.fromisoformat(msg['timestamp']).strftime('%I:%M:%S %p')
        messages_html += f'<div class="message"><strong>{msg["username"]}:</strong> <span style="opacity:0.7">{time_str}</span> {msg["text"]}</div>'
    
    resp = make_response(jsonify({'html': messages_html}))
    resp.set_cookie('sessionid', session.sid, max_age=31536000)
    return resp

@app.route('/api/send-message/<code>', methods=['POST'])
def send_message(code):
    data = request.get_json()
    groups = get_groups()
    if code not in groups:
        groups[code] = []
    
    user_data = get_user_data()
    username = user_data['name'] or 'Anonymous'
    msg = {
        'username': username,
        'text': data.get('text', '').strip()[:200],
        'timestamp': datetime.now().isoformat()
    }
    if msg['text']:
        groups[code].append(msg)
        save_groups(groups)
    
    resp = make_response(jsonify({'status': 'sent'}))
    resp.set_cookie('sessionid', session.sid, max_age=31536000)
    return resp

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return make_response('''
<!DOCTYPE html>
<html>
<head>
    <title>🔒 Private Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;font-size:16px;}
        body{background:#1a1a1a;color:#eee;padding:20px;min-height:100vh;}
        .name-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;}
        #nameInput{width:250px;max-width:90vw;padding:12px;border:none;border-radius:8px;background:#333;color:#eee;font-size:16px;}
        #setNameBtn{margin-top:15px;padding:12px 24px;background:#4a4a4a;border:none;border-radius:8px;color:#eee;cursor:pointer;font-size:16px;}
        #setNameBtn:hover{background:#666;}
        .chat-screen{display:none;flex-direction:column;height:100vh;max-width:600px;margin:0 auto;}
        .header{padding:15px;background:#2a2a2a;text-align:center;border-radius:8px 8px 0 0;}
        .groups{padding:15px;background:#333;border-radius:0 0 8px 8px;}
        #groupSelect{width:100%;padding:12px;border:none;border-radius:6px;background:#444;color:#eee;font-size:16px;margin-bottom:10px;}
        #groupInfo{display:flex;align-items:center;margin-bottom:10px;}
        .group-info{background:#444;padding:8px 12px;border-radius:6px;display:flex;align-items:center;}
        .copy-btn{background:#666;color:white;border:none;border-radius:50%;width:32px;height:32px;font-size:14px;cursor:pointer;margin-left:8px;display:flex;align-items:center;justify-content:center;}
        .copy-btn:hover{background:#888;}
        #newGroupBtn{width:100%;padding:12px;background:#4CAF50;border:none;border-radius:6px;color:white;cursor:pointer;font-size:16px;}
        #newGroupBtn:hover{background:#45a049;}
        #messages{flex:1;overflow-y:auto;padding:15px;background:#2a2a2a;max-height:calc(100vh - 200px);}
        .message{margin-bottom:12px;padding:8px;background:#333;border-radius:6px;}
        .input-area{padding:15px;background:#333;border-radius:8px 8px 0 0;}
        #messageInput{width:calc(100% - 70px);padding:12px;border:none;border-radius:6px;background:#444;color:#eee;font-size:16px;}
        #sendBtn{width:60px;padding:12px;background:#2196F3;border:none;border-radius:6px;color:white;cursor:pointer;font-size:16px;}
        #sendBtn:hover{background:#1976D2;}
        #nameDisplay{font-weight:bold;color:#4CAF50;}
        @media (max-width:480px){.chat-screen{padding:10px;}.header h2{font-size:20px;}}
    </style>
</head>
<body>
    <div id="nameScreen" class="name-screen">
        <h1>🔒 Private Chat</h1>
        <p>Enter your name to start</p>
        <input id="nameInput" type="text" placeholder="Your name..." maxlength="20">
        <br><button id="setNameBtn">Continue →</button>
    </div>
    
    <div id="chatScreen" class="chat-screen">
        <div class="header">
            <h2>Private Groups <span id="nameDisplay"></span></h2>
        </div>
        <div class="groups">
            <select id="groupSelect"><option>Select group or create new</option></select>
            <div id="groupInfo"></div>
            <button id="newGroupBtn">➕ New Private Group</button>
        </div>
        <div id="messages"></div>
        <div class="input-area">
            <input id="messageInput" type="text" placeholder="Type message..." maxlength="200">
            <button id="sendBtn">Send</button>
        </div>
    </div>

    <script>
        let currentGroup = '';
        
        async function init(){
            document.getElementById('setNameBtn').onclick = setName;
            document.getElementById('nameInput').addEventListener('keypress', e => e.key === 'Enter' && setName());
            document.getElementById('nameInput').focus();
        }
        
        async function setName(){
            const name = document.getElementById('nameInput').value.trim();
            if(!name) return;
            
            await fetch('/api/set-name', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name}),
                credentials: 'include'
            });
            
            document.getElementById('nameScreen').style.display = 'none';
            document.getElementById('chatScreen').style.display = 'flex';
            document.getElementById('nameDisplay').textContent = name + ' ';
            loadGroups();
            setInterval(loadMessages, 2000);
        }
        
        async function loadGroups(){
            try {
                const res = await fetch('/api/groups', {credentials: 'include'});
                const data = await res.json();
                const select = document.getElementById('groupSelect');
                select.innerHTML = '<option>Select group or create new</option>';
                
                data.favorite_groups.forEach(code => {
                    const option = document.createElement('option');
                    option.value = code;
                    option.textContent = code;
                    select.appendChild(option);
                });
                
                if(data.favorite_groups.length > 0){
                    select.value = data.favorite_groups[0];
                    updateGroupInfo(data.favorite_groups[0]);
                }
            } catch(e) {console.error('Load groups error:', e);}
        }
        
        function updateGroupInfo(code){
            currentGroup = code;
            document.getElementById('groupInfo').innerHTML = 
                `<div class="group-info">
                    <span>${code}</span>
                    <button class="copy-btn" onclick="copyInvite('${code}')">📋</button>
                </div>`;
            loadMessages();
        }
        
        async function createGroup(){
            const res = await fetch('/api/create-group', {method: 'POST', credentials: 'include'});
            const data = await res.json();
            loadGroups();
            document.getElementById('groupSelect').value = data.code;
            updateGroupInfo(data.code);
        }
        
        async function copyInvite(code){
            navigator.clipboard.writeText(`${window.location.origin}/#${code}`);
            const btn = event.target;
            const original = btn.textContent;
            btn.textContent = '✓';
            setTimeout(() => btn.textContent = original, 1000);
        }
        
        async function loadMessages(){
            if(!currentGroup) return;
            try {
                const res = await fetch(`/api/messages/${currentGroup}`, {credentials: 'include'});
                const data = await res.json();
                document.getElementById('messages').innerHTML = data.html || '<div style="opacity:0.5;text-align:center;padding:20px;">No messages yet</div>';
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            } catch(e) {console.error('Load messages error:', e);}
        }
        
        async function sendMessage(){
            if(!currentGroup) return;
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if(!text) return;
            
            input.disabled = true;
            input.value = 'Sending...';
            
            await fetch(`/api/send-message/${currentGroup}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text}),
                credentials: 'include'
            });
            
            input.value = '';
            input.disabled = false;
            loadMessages();
        }
        
        document.getElementById('newGroupBtn').onclick = createGroup;
        document.getElementById('sendBtn').onclick = sendMessage;
        document.getElementById('groupSelect').onchange = function(){
            if(this.value) updateGroupInfo(this.value);
        };
        document.getElementById('messageInput').addEventListener('keypress', e => e.key === 'Enter' && sendMessage());
        
        window.onload = init;
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
