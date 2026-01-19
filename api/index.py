from flask import Flask, request, jsonify, make_response, session
import random
import string
import json
import os
import uuid
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

DB_PATH = '/tmp/chats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        favorite_groups TEXT DEFAULT '[]'
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        group_code TEXT NOT NULL,
        username TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )''')
    return conn

def get_user_id():
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    return user_id

@app.route('/api/set-name', methods=['POST'])
def set_name():
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name or len(name) > 20:
            return jsonify({'error': 'Invalid name'}), 400
        
        user_id = get_user_id()
        session['username'] = name  # ← FIX 1: Store name in session
        
        conn = get_db_connection()
        existing = conn.execute('SELECT favorite_groups FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if existing:
            conn.execute('UPDATE users SET name = ? WHERE user_id = ?', (name, user_id))
        else:
            conn.execute('INSERT INTO users (user_id, name, favorite_groups) VALUES (?, ?, ?)', 
                        (user_id, name, '[]'))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception:
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/create-group', methods=['POST'])
def create_group():
    try:
        user_id = get_user_id()
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        conn = get_db_connection()
        existing = conn.execute('SELECT favorite_groups FROM users WHERE user_id = ?', (user_id,)).fetchone()
        groups = json.loads(existing['favorite_groups']) if existing else []
        groups.append(code)
        
        if existing:
            conn.execute('UPDATE users SET favorite_groups = ? WHERE user_id = ?', 
                        (json.dumps(groups), user_id))
        else:
            conn.execute('INSERT INTO users (user_id, name, favorite_groups) VALUES (?, ?, ?)', 
                        (user_id, session.get('username', ''), json.dumps(groups)))
        
        conn.commit()
        conn.close()
        return jsonify({'code': code})
    except Exception:
        return jsonify({'error': 'Create failed'}), 500

@app.route('/api/groups', methods=['GET'])
def groups_api():
    try:
        user_id = get_user_id()
        conn = get_db_connection()
        user = conn.execute('SELECT favorite_groups FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        groups = json.loads(user['favorite_groups']) if user else []
        return jsonify(groups)
    except Exception:
        return jsonify([])

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    try:
        user_id = get_user_id()
        conn = get_db_connection()
        
        if request.method == 'POST':
            data = request.get_json() or {}
            text = data.get('text', '').strip()
            if not text:
                conn.close()
                return jsonify({'error': 'Empty message'}), 400
            
            username = session.get('username', 'Anonymous')  # ← FIX 2: Use session username
            timestamp = datetime.now().strftime('%I:%M:%S %p')  # ← FIX 3: 12hr AM/PM
            
            conn.execute('INSERT INTO messages (user_id, group_code, username, text, timestamp) VALUES (?, ?, ?, ?, ?)',
                        (user_id, code, username, text, timestamp))
            conn.commit()
            conn.close()
            return jsonify({'status': 'sent'})
        
        # GET messages
        msgs = conn.execute('''
            SELECT username, text, timestamp 
            FROM messages 
            WHERE user_id = ? AND group_code = ? 
            ORDER BY id DESC 
            LIMIT 50
        ''', (user_id, code)).fetchall()
        conn.close()
        
        messages_html = ''
        for msg in reversed(msgs):
            messages_html += f'<div class="message"><strong>{msg["username"]}:</strong> <span style="opacity:0.7">{msg["timestamp"]}</span> {msg["text"]}</div>'
        
        return jsonify({'html': messages_html})
    except Exception:
        return jsonify({'html': 'Error loading messages'})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html><head><title>🔒 Private SQLite Chat</title>
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
</style></head>
<body>
<div class="container">
<div id="name-screen" class="name-screen">
<h1>🔒 Private SQLite Chat</h1>
<input id="nameInput" placeholder="Enter your name..." maxlength="20">
<button id="setNameBtn" class="btn">Start Chatting</button>
<div class="status">Chats persist forever (SQLite /tmp)</div>
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
            btn.className='group-btn';
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
            body:JSON.stringify({text,timestamp:new Date().toLocaleTimeString()})
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
