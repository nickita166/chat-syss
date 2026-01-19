from flask import Flask, request, jsonify
import random
import string

app = Flask(__name__)
groups = {}

@app.route('/api/create-group', methods=['GET', 'POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups[code] = []
    return jsonify({'code': code})

@app.route('/api/groups', methods=['GET'])
def groups_api():
    return jsonify(list(groups.keys())[:20])

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    if code not in groups:
        return jsonify({'error': 'Group not found'}), 404
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', 'Anonymous')[:20]
        text = data.get('text', '').strip()
        timestamp = data.get('timestamp', 'Now')
        if text:
            groups[code].append({'user': username, 'text': text, 'timestamp': timestamp})
        return jsonify({'status': 'sent'})
    return jsonify(groups[code][-50:])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html>
<head><title>Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:sans-serif;background:#000;color:#fff;height:100vh;}
input,select,button{background:#111;border:1px solid #333;color:#fff;padding:10px;border-radius:5px;}
button{background:#00ff88;color:#000;border:none;cursor:pointer;}
.container{max-width:800px;margin:0 auto;padding:20px;height:100vh;display:flex;flex-direction:column;}
#name-screen{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;}
#chat-screen{display:none;flex-direction:column;height:100vh;}
#messages{flex:1;overflow-y:auto;padding:20px;background:#000;}
.message{margin-bottom:15px;}
.user{color:#00ff88;font-weight:bold;}
.text{background:#1a1a1a;padding:10px;border-radius:10px;display:inline-block;}
</style></head>
<body>
<div class="container">
<div id="name-screen">
<h1>Enter Name</h1>
<input id="nameInput" placeholder="Your name" maxlength="20">
<button id="setNameBtn">Start</button>
</div>
<div id="chat-screen">
<div><h2 id="currentGroup">No Group</h2></div>
<div><select id="groupSelect"><option>Select group</option></select><button id="createGroupBtn">New</button></div>
<div id="messages"></div>
<div><input id="messageInput" placeholder="Message" disabled><button id="sendBtn" disabled>Send</button></div>
</div></div>
<script>
let user="",currentGroup="";
document.getElementById("setNameBtn").onclick=()=>{user=document.getElementById("nameInput").value.trim();if(user){document.getElementById("name-screen").style.display="none";document.getElementById("chat-screen").style.display="flex";document.getElementById("messageInput").disabled=false;loadGroups();setInterval(loadGroups,5000);setInterval(()=>{if(currentGroup)loadMessages()},2000)}};
document.getElementById("createGroupBtn").onclick=async()=>{try{const res=await fetch("/api/create-group");const data=await res.json();joinGroup(data.code)}catch(e){alert("Failed")}};
document.getElementById("groupSelect").onchange=e=>e.target.value&&joinGroup(e.target.value);
document.getElementById("sendBtn").onclick=sendMessage;
document.getElementById("messageInput").onkeypress=e=>e.key=="Enter"&&sendMessage();
async function loadGroups(){try{const res=await fetch("/api/groups");const codes=await res.json();const select=document.getElementById("groupSelect");select.innerHTML="<option>Select group</option>";codes.forEach(code=>{const opt=document.createElement("option");opt.value=code;opt.text=code;select.appendChild(opt)})}catch(e){}}
function joinGroup(code){currentGroup=code;document.getElementById("currentGroup").textContent=code;document.getElementById("sendBtn").disabled=false;loadMessages()}
async function loadMessages(){if(!currentGroup)return;try{const res=await fetch("/api/messages/"+currentGroup);const msgs=await res.json();const container=document.getElementById("messages");container.innerHTML=msgs.map(m=>`<div class="message"><div class="user">${m.user}: ${m.timestamp}</div><div class="text">${m.text}</div></div>`).join("");container.scrollTop=container.scrollHeight}catch(e){}}
async function sendMessage(){const text=document.getElementById("messageInput").value.trim();if(!text||!currentGroup||!user)return;try{await fetch("/api/messages/"+currentGroup,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,timestamp:new Date().toLocaleTimeString(),username:user})});document.getElementById("messageInput").value="";loadMessages()}catch(e){alert("Send failed")}}
</script>
</body></html>'''
