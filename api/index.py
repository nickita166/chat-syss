from flask import Flask, request, jsonify
import random
import string
from collections import defaultdict

app = Flask(__name__)

SHARED_GROUPS = defaultdict(list)

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
        return jsonify({'html': '<div class="message">Group not found - get new invite</div>'})
    
    messages_html = ''
    messages = SHARED_GROUPS[code][-50:]
    for msg in messages:
        messages_html += f'<div class="message"><strong>{msg.get("user", "Anon")}:</strong> {msg.get("text", "")} <small>{msg.get("timestamp", "Now")}</small></div>'
    
    return jsonify({'html': messages_html or '<div class="message">No messages yet</div>'})

@app.route('/api/messages/<code>', methods=['POST'])
def send_message(code):
    data = request.get_json() or {}
    SHARED_GROUPS[code].append({
        'user': data.get('user', 'Anonymous'),
        'text': data.get('text', '').strip(),
        'timestamp': data.get('timestamp', 'Now')
    })
    return jsonify({'status': 'sent'})

@app.route('/join/<code>')
def join_page(code):
    return f'''
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>Join {code}</title>
<style>body{{background:#000;color:#e0e0e0;font-family:sans-serif;padding:20px;text-align:center;}}input{{padding:15px;border:2px solid #444;background:#1a1a1a;color:#e0e0e0;border-radius:10px;width:90%;max-width:300px;font-size:18px;}}button{{padding:15px 30px;background:#0a74da;border:none;color:white;border-radius:10px;font-size:16px;cursor:pointer;}}</style></head>
<body><h1>Join: <strong>{code}</strong></h1><input id="nameInput" placeholder="Your name"><button onclick="localStorage.setItem('username',document.getElementById('nameInput').value);window.location.href='/'">Join Chat</button>
<script>if(localStorage.getItem('username'))window.location.href='/';</script></body></html>'''

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}html{font-size:16px;-webkit-text-size-adjust:none;}body{font-family:sans-serif;background:#000;color:#e0e0e0;height:100vh;overflow:hidden;}.container{max-width:600px;margin:0 auto;height:100vh;display:flex;flex-direction:column;}.header{padding:20px;background:#1a1a1a;text-align:center;border-bottom:1px solid #444;}.name-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;background:#000;}.name-screen input{padding:15px;font-size:18px;border:2px solid #444;background:#1a1a1a;color:#e0e0e0;border-radius:10px;width:90%;max-width:300px;margin:10px 0;}.chat-screen{display:flex;flex-direction:column;height:100vh;}.groups{padding:15px;background:#1a1a1a;border-bottom:1px solid #444;}.groups select{width:100%;padding:12px;background:#2d2d2d;color:#e0e0e0;border:1px solid #444;border-radius:8px;font-size:16px;margin-bottom:10px;}.group-info{display:flex;justify-content:space-between;align-items:center;font-size:14px;}.invite-btn{padding:8px 16px;background:#0a84ff;border:none;color:white;border-radius:6px;cursor:pointer;font-size:13px;}.messages{flex:1;overflow-y:auto;padding:20px;background:#0f0f0f;}.message{margin-bottom:12px;padding:12px;background:#1a1a1a;border-radius:12px;}.input-area{padding:20px;background:#1a1a1a;border-top:1px solid #444;display:flex;gap:10px;}.input-area input{flex:1;padding:15px;background:#2d2d2d;color:#e0e0e0;border:1px solid #444;border-radius:20px;font-size:16px;}.input-area button{padding:15px 25px;background:#0a74da;border:none;color:white;border-radius:20px;cursor:pointer;font-size:16px;}button:disabled{background:#444;}</style></head>
<body>
<div id="name-screen" class="name-screen"><h1>Private Chat</h1><input id="nameInput" placeholder="Name..." maxlength="20"><button id="setNameBtn">Go</button></div>
<div id="chat-screen" class="chat-screen" style="display:none;">
<div class="header"><h2>Groups</h2><div id="currentUser"></div></div>
<div class="groups"><select id="groupSelect"><option>Loading...</option></select><div id="groupInfo" style="display:none;"></div><button onclick="createGroup()">New Group</button></div>
<div id="messages" class="messages">Pick a group</div>
<div class="input-area"><input id="messageInput" placeholder="Message..." disabled><button id="sendBtn" onclick="sendMessage()" disabled>Send</button></div>
</div>
<script>
let currentGroup='',username=localStorage.getItem('username')||'';let nameScreen=document.getElementById('name-screen'),chatScreen=document.getElementById('chat-screen');
function init(){username?(nameScreen.style.display='none',chatScreen.style.display='flex',document.getElementById('currentUser').textContent=`You: ${username}`,loadGroupsAndMessages()):(nameScreen.style.display='flex',chatScreen.style.display='none');document.getElementById('setNameBtn').onclick=setName;document.getElementById('nameInput').onkeypress=e=>e.key=='Enter'&&setName();document.getElementById('nameInput').focus();}
function setName(){username=document.getElementById('nameInput').value.trim();username&&(localStorage.setItem('username',username),nameScreen.style.display='none',chatScreen.style.display='flex',document.getElementById('currentUser').textContent=`You: ${username}`,loadGroupsAndMessages());}
async function loadGroupsAndMessages(){await loadGroups();if(currentGroup)loadMessages();}
async function loadGroups(){try{const res=await fetch('/api/groups'),groups=await res.json();document.getElementById('groupSelect').innerHTML=groups.map(g=>`<option value="${g}">${g}</option>`).join('')||'<option>Create a group!</option>'}catch(e){console.error(e)}}
async function loadMessages(){if(!currentGroup)return;try{const res=await fetch(`/api/messages/${currentGroup}`),data=await res.json();document.getElementById('messages').innerHTML=data.html;document.getElementById('messages').scrollTop=document.getElementById('messages').scrollHeight}catch(e){console.error(e)}}
function updateGroupInfo(code){document.getElementById('groupInfo').style.display='flex';document.getElementById('groupInfo').innerHTML=`<div class="group-info"><span>${code}</span><button class="invite-btn" onclick="copyInvite('${window.location.origin}/join/${code}')">📋 Copy</button></div>`;}
async function createGroup(){try{const res=await fetch('/api/create-group',{method:'POST'}),data=await res.json();await loadGroups();document.getElementById('groupSelect').value=data.code;document.getElementById('groupSelect').dispatchEvent(new Event('change'))}catch(e){alert('Error')}}
function copyInvite(invite){navigator.clipboard.writeText(invite).then(()=>alert('Copied!')).catch(()=>prompt('Copy:',invite));}
document.getElementById('groupSelect').onchange=e=>{const val=e.target.value;val?(updateGroupInfo(val),currentGroup=val,document.getElementById('messageInput').disabled=document.getElementById('sendBtn').disabled=false,loadMessages()):(document.getElementById('groupInfo').style.display='none',currentGroup='',document.getElementById('messageInput').disabled=document.getElementById('sendBtn').disabled=true)};
async function sendMessage(){const text=document.getElementById('messageInput').value.trim();if(!text||!currentGroup||!username)return;const btn=document.getElementById('sendBtn');btn.disabled=true;btn.textContent='Sending...';try{await fetch(`/api/messages/${currentGroup}`,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{text,user:username,timestamp:new Date().toLocaleTimeString()}})}});document.getElementById('messageInput').value='';loadMessages()}finally{btn.disabled=false;btn.textContent='Send';document.getElementById('messageInput').focus()}}
document.getElementById('messageInput').onkeypress=e=>e.key=='Enter'&&sendMessage();setInterval(loadMessages,2500);window.onload=init;
</script></body></html>'''

if __name__=='__main__':
    app.run(debug=True)
