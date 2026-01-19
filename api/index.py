from flask import Flask, request, jsonify
import random
import string
import json
import os

app = Flask(__name__)

# Global shared groups (public but private via access codes)
SHARED_GROUPS = {}

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    SHARED_GROUPS[code] = []
    return jsonify({'code': code, 'invite': f"https://{request.host}/join/{code}"})

@app.route('/api/join-group/<code>')
def join_group(code):
    if code not in SHARED_GROUPS:
        return jsonify({'error': 'Group not found'}), 404
    return jsonify({'success': True})

@app.route('/api/groups')
def list_groups():
    return jsonify(list(SHARED_GROUPS.keys()))

@app.route('/api/messages/<code>')
def get_messages(code):
    if code not in SHARED_GROUPS:
        return jsonify({'html': '<div>Group not found - ask creator for new invite</div>'})
    
    messages_html = ''
    for msg in SHARED_GROUPS[code][-50:]:
        messages_html += f'<div><strong>{msg["user"]}:</strong> {msg["text"]} <small>{msg.get("timestamp", "Now")}</small></div>'
    return jsonify({'html': messages_html})

@app.route('/api/messages/<code>', methods=['POST'])
def send_message(code):
    data = request.get_json() or {}
    user = data.get('user', 'Anonymous')
    
    if code not in SHARED_GROUPS:
        return jsonify({'error': 'Group not found'}), 404
    
    SHARED_GROUPS[code].append({
        'user': user,
        'text': data.get('text', '').strip(),
        'timestamp': data.get('timestamp', 'Now')
    })
    return jsonify({'status': 'sent'})

@app.route('/join/<code>')
def join_page(code):
    return f'''
<!DOCTYPE html>
<html><head><title>Join {code}</title>
<style>body{{background:#000;color:#e0e0e0;font-family:sans-serif;text-align:center;padding:50px;}}
input{{padding:15px;margin:10px;border:2px solid #444;background:#1a1a1a;color:#e0e0e0;border-radius:10px;}}
button{{padding:15px 30px;background:#0a74da;border:none;color:white;border-radius:10px;cursor:pointer;}}</style>
</head>
<body>
<h1>Join Group: <strong>{code}</strong></h1>
<input id="nameInput" placeholder="Enter your name">
<button onclick="join()">Join Chat</button>
<script>
async function join() {{
    localStorage.setItem('username', document.getElementById('nameInput').value);
    window.location.href = '/';
}}
</script>
</body>
</html>'''

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html>
<head><title>Private Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#000;color:#e0e0e0;height:100vh;overflow:hidden;}.container{max-width:600px;margin:0 auto;height:100vh;display:flex;flex-direction:column;}.header{padding:20px;background:linear-gradient(135deg,#1a1a1a,#2d2d2d);text-align:center;border-bottom:1px solid #444;}.name-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;background:#000;}.name-screen input{padding:15px;font-size:18px;border:2px solid #444;background:#1a1a1a;color:#e0e0e0;border-radius:10px;width:80%;max-width:300px;text-align:center;}.name-screen button{padding:15px 30px;background:#0a74da;border:none;color:white;border-radius:10px;font-size:16px;cursor:pointer;margin-top:20px;}.chat-screen{display:flex;flex-direction:column;}.groups{padding:15px;background:#1a1a1a;border-bottom:1px solid #444;}.groups select{width:100%;padding:10px;background:#2d2d2d;color:#e0e0e0;border:1px solid #444;border-radius:5px;font-size:14px;}.group-info{display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:12px;}.invite-btn{padding:5px 10px;background:#0a84ff;border:none;color:white;border-radius:5px;cursor:pointer;font-size:11px;}.messages{flex:1;overflow-y:auto;padding:20px;background:#0f0f0f;}.message{margin-bottom:10px;padding:10px;background:#1a1a1a;border-radius:10px;}.input-area{padding:20px;background:#1a1a1a;border-top:1px solid #444;display:flex;gap:10px;}.input-area input{flex:1;padding:15px;background:#2d2d2d;color:#e0e0e0;border:1px solid #444;border-radius:20px;font-size:16px;}.input-area button{padding:15px 25px;background:#0a74da;border:none;color:white;border-radius:20px;cursor:pointer;font-size:16px;}.private{font-style:italic;color:#888;}small{color:#888;}button:disabled{background:#444;cursor:not-allowed;}</style>
</head>
<body>
<div id="name-screen" class="name-screen" style="display:none;">
    <h1>Enter Your Name</h1>
    <input id="nameInput" placeholder="Your name..." maxlength="20">
    <button id="setNameBtn">Continue</button>
</div>
<div id="chat-screen" class="container chat-screen">
    <div class="header">
        <h2>Private Chat</h2>
        <div id="currentUser">Not logged in</div>
    </div>
    <div class="groups">
        <select id="groupSelect"><option>Loading groups...</option></select>
        <div id="groupInfo"></div>
        <button onclick="createGroup()">New Private Group</button>
    </div>
    <div id="messages" class="messages">Select a group to chat</div>
    <div class="input-area">
        <input id="messageInput" placeholder="Type a message..." disabled>
        <button id="sendBtn" onclick="sendMessage()" disabled>Send</button>
    </div>
</div>

<script>
let currentGroup = '';
let username = localStorage.getItem('username') || '';

function init(){
    if(username){
        document.getElementById('name-screen').style.display = 'none';
        document.getElementById('chat-screen').style.display = 'flex';
        document.getElementById('currentUser').textContent = `Logged in as: ${username}`;
        loadGroups();
        setInterval(loadMessages, 2000);
    } else {
        document.getElementById('name-screen').style.display = 'flex';
    }
    
    document.getElementById('setNameBtn').onclick = setName;
    document.getElementById('nameInput').addEventListener('keypress', e => e.key === 'Enter' && setName());
    document.getElementById('nameInput').focus();
}

function setName(){
    username = document.getElementById('nameInput').value.trim();
    if(username){
        localStorage.setItem('username', username);
        document.getElementById('name-screen').style.display = 'none';
        document.getElementById('chat-screen').style.display = 'flex';
        document.getElementById('currentUser').textContent = `Logged in as: ${username}`;
        loadGroups();
    }
}

async function loadGroups(){
    const res = await fetch('/api/groups');
    const groups = await res.json();
    const select = document.getElementById('groupSelect');
    select.innerHTML = groups.map(g => `<option value="${g}">${g}</option>`).join('') || '<option>No public groups</option>';
}

function updateGroupInfo(code){
    document.getElementById('groupInfo').innerHTML = `
        <div class="group-info">
            <span>${code}</span>
            <button class="invite-btn" onclick="copyInvite('${window.location.origin}/join/${code}')">Copy Invite</button>
        </div>
    `;
}

async function createGroup(){
    const res = await fetch('/api/create-group', {method: 'POST'});
    const data = await res.json();
    await loadGroups();
    document.getElementById('groupSelect').value = data.code;
    joinGroup(data.code);
}

async function copyInvite(invite){
    await navigator.clipboard.writeText(invite);
    alert('Invite copied!');
}

document.getElementById('groupSelect').onchange = function(){
    if(this.value) {
        updateGroupInfo(this.value);
        joinGroup(this.value);
    }
};

function joinGroup(code){
    currentGroup = code;
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('messageInput').focus();
    loadMessages();
}

async function loadMessages(){
    if(!currentGroup) return;
    const res = await fetch(`/api/messages/${currentGroup}`);
    const data = await res.json();
    document.getElementById('messages').innerHTML = data.html || '<div>No messages yet</div>';
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

async function sendMessage(){
    const text = document.getElementById('messageInput').value.trim();
    if(!text || !currentGroup) return;
    
    await fetch(`/api/messages/${currentGroup}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text, user: username, timestamp: new Date().toLocaleTimeString()})
    });
    
    document.getElementById('messageInput').value = '';
    loadMessages();
}

document.getElementById('messageInput').addEventListener('keypress', e => {
    if(e.key === 'Enter') sendMessage();
});

window.onload = init;
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
