from flask import Flask, request, jsonify, make_response, session
import random
import string
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        return json.loads(user_data)
    return {'name': '', 'favorite_groups': []}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)

def get_user_groups():
    groups_data = session.get('groups', '{}')
    return json.loads(groups_data) if groups_data else {}

def save_user_groups(groups_data):
    session['groups'] = json.dumps(groups_data)

@app.route('/api/set-name', methods=['POST'])
def set_name():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if name and len(name) <= 20:
        user_data = get_user_data()
        user_data['name'] = name
        session['username'] = name  # For messages
        save_user_data(user_data)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid name'}), 400

@app.route('/api/create-group', methods=['POST'])
def create_group():
    user_groups = get_user_groups()
    user_data = get_user_data()
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    user_groups[code] = []
    save_user_groups(user_groups)
    
    if 'favorite_groups' not in user_data:
        user_data['favorite_groups'] = []
    if code not in user_data['favorite_groups']:
        user_data['favorite_groups'].append(code)
    save_user_data(user_data)
    
    return jsonify({'code': code})

@app.route('/api/groups', methods=['GET'])
def groups_api():
    user_data = get_user_data()
    return jsonify(user_data.get('favorite_groups', []))

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    user_groups = get_user_groups()
    
    if code not in user_groups:
        user_groups[code] = []
        save_user_groups(user_groups)
    
    if request.method == 'POST':
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Empty message'}), 400
        
        username = session.get('username', 'Anonymous')
        timestamp = datetime.now().strftime('%I:%M:%S %p')
        
        user_groups[code].append({
            'username': username,
            'text': text,
            'timestamp': timestamp
        })
        save_user_groups(user_groups)
        return jsonify({'status': 'sent'})
    
    messages_html = ''
    for msg in user_groups[code][-50:]:
        messages_html += f'<div class="message"><strong>{msg["username"]}:</strong> <span style="opacity:0.7">{msg["timestamp"]}</span> {msg["text"]}</div>'
    
    return jsonify({'html': messages_html})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html><head><title>🔒 Private Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui;background:#000;color:#e0e0e0;height:100vh;overflow:hidden;}
.container{max-width:800px;margin:0 auto;height:100vh;display:flex;flex-direction:column;}
.name-screen{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;gap:20px;}
.chat-screen{display:none;flex-direction:column;height:100vh;}
.header{background:#111;padding:15px;border-bottom:1px solid #333;display:flex;justify-content:space-between;align-items:center;}
.groups{flex-grow:1;overflow-x:auto;padding:0 15px;max-width:400px;}
.group-btn{background:#333;color:#e0e0e0;border:none;padding:8px 12px;margin:2px;border-radius:20px;font-size:12px;cursor:pointer;white-space:nowrap;}
.group-btn:hover{background:#555;}
.group-btn.active{background:#007acc;}
.messages{flex:1;overflow-y:auto;padding:20px 15px;background:#000;}
.message{margin-bottom:12px;padding:8px;background:#111;border-radius:8px;}
.message strong{color:#007acc;}
.input-area{display:flex;padding:15px;background:#111;border-top:1px solid #333;gap:10px;}
#messageInput{flex:1;background:#222;color:#e0e0e0;border:1px solid #444;border-radius:20px;padding:12px 16px;font-size:14px;}
#sendBtn{background:#007acc;color:white;border:none;border-radius:20px;padding:12px 20px;cursor:pointer;font-weight:500;flex-shrink:0;}
#nameInput{background:#222;color:#e0e0e0;border:1px solid #444;border-radius:8px;padding:20px;font-size:18px;width:300px;max-width:90vw;text-align:center;}
.btn{background:#007acc;color:white;border:none;border-radius:8px;padding:15px 30px;font-size:16px;cursor:pointer;}
.btn:hover{background:#005a99;}
.status{color:#888;font-size:12px;}
.private::after{content:" 🔒 private";opacity:0.7;font-size:0.8em;}
</style></head>
<body>
<div class="container">
<div id="name-screen" class="name-screen">
<h1>🔒 Private Chat</h1>
<input id="nameInput" placeholder="Enter your name..." maxlength="20">
<button id="setNameBtn" class="btn">Start Chatting</button>
<div class="status">Your data persists in signed cookies</div>
</div>
<div id="chat-screen" class="chat-screen">
<div class="header">
<div>Your Groups:</div>
<button id="newGroupBtn" class="group-btn">+ New Group</button>
</div>
<div id="groupsList" class="groups"></div>
<div id="messages" class="messages">Select a group to start chatting</div>
<div class="input-area">
<input id="messageInput" placeholder="Type a message..." disabled>
<button id="sendBtn" disabled>Send</button>
</div>
</div>
</div>
<script>
let currentGroup=null,user='';

async function init(){
    document.getElementById('setNameBtn').onclick=setName;
    document.getElementById('nameInput').addEventListener('keypress',e=>e.key==='Enter'&&setName());
    document.getElementById('nameInput').focus();
    loadGroups();  // Load existing groups on startup
}

async function setName(){
    user=document.getElementById('nameInput').value.trim();
    if(!user)return;
    
    const res=await fetch('/api/set-name',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user})});
    if(res.ok){
        document.getElementById('name-screen').style.display='none';
        document.getElementById('chat-screen').style.display='flex';
        loadGroups();
    }
}

async function loadGroups(){
    try{
        const res=await fetch('/api/groups');
        const groups=await res.json();
        const list=document.getElementById('groupsList');
        list.innerHTML='';
        groups.forEach(code=>{
            const btn=document.createElement('button');
            btn.className='group-btn private';
            btn.textContent=code;
            btn.onclick=()=>joinGroup(code);
            list.appendChild(btn);
        });
    }catch(e){
        console.error('Load groups failed');
    }
}

async function createGroup(){
    try{
        const res=await fetch('/api/create-group',{method:'POST',headers:{'Content-Type':'application/json'}});
        const data=await res.json();
        if(data.code){
            loadGroups();
            setTimeout(()=>joinGroup(data.code),100);
        }
    }catch(e){
        console.error('Create failed');
    }
}

function joinGroup(code){
    currentGroup=code;
    document.querySelectorAll('.group-btn').forEach(btn=>btn.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('messageInput').disabled=false;
    document.getElementById('sendBtn').disabled=false;
    document.getElementById('messageInput').focus();
    loadMessages();
}

async function loadMessages(){
    if(!currentGroup)return;
    try{
        const res=await fetch(`/api/messages/${currentGroup}`);
        const data=await res.json();
        document.getElementById('messages').innerHTML=data.html||'No messages yet';
        document.getElementById('messages').scrollTop=document.getElementById('messages').scrollHeight;
    }catch(e){
        console.error('Load messages failed');
    }
}

async function sendMessage(){
    if(!currentGroup)return;
    const text=document.getElementById('messageInput').value.trim();
    if(!text)return;
    try{
        await fetch(`/api/messages/${currentGroup}`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({text})
        });
        document.getElementById('messageInput').value='';
        loadMessages();
    }catch(e){
        console.error('Send failed');
    }
}

document.getElementById('newGroupBtn').onclick=createGroup;
document.getElementById('sendBtn').onclick=sendMessage;
document.getElementById('messageInput').addEventListener('keypress',e=>e.key==='Enter'&&sendMessage());
setInterval(loadMessages,2000);
window.onload=init;
</script></body></html>    '''

if __name__ == '__main__':
    app.run(debug=True)
