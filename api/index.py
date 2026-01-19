from flask import Flask, request, jsonify, send_from_directory
import os
import random
import string

app = Flask(__name__)
groups = {}

@app.route('/')
def index():
    try:
        return send_from_directory('public', 'index.html')
    except:
        return '''
<!DOCTYPE html>
<html>
<head><title>Black Group Chat</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:sans-serif;background:#000;color:#e0e0e0;height:100vh;overflow:hidden;}
.container{max-width:900px;margin:0 auto;height:100vh;display:flex;flex-direction:column;}
.name-screen{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;background:#000;}
.name-container{text-align:center;padding:2rem;}
.name-container h2{font-size:2.5rem;margin-bottom:2rem;color:#fff;}
#nameInput{background:#1a1a1a;border:2px solid #333;border-radius:12px;padding:1rem 1.5rem;font-size:1.2rem;color:#e0e0e0;width:300px;margin-bottom:1.5rem;}
#nameInput:focus{outline:none;border-color:#00ff88;}
#setNameBtn{background:linear-gradient(135deg,#00ff88,#00cc6a);border:none;border-radius:12px;padding:1rem 2.5rem;font-size:1.2rem;font-weight:600;color:#000;cursor:pointer;}
.chat-screen{display:none;height:100vh;}.header{background:#111;padding:1rem 2rem;border-bottom:1px solid #333;}
.group-section{background:#1a1a1a;padding:1rem 2rem;border-bottom:1px solid #333;display:flex;gap:1rem;align-items:center;}
#groupSelect{flex:1;background:#2a2a2a;border:1px solid #444;border-radius:8px;padding:0.8rem;color:#e0e0e0;}
.btn{background:#00ff88;border:none;border-radius:8px;padding:0.8rem 1.5rem;color:#000;font-weight:600;cursor:pointer;}
.messages{flex:1;overflow-y:auto;padding:2rem;background:#000;}
.message{margin-bottom:1.5rem;}
.message .user{font-weight:600;color:#00ff88;margin-bottom:0.3rem;font-size:0.9rem;}
.message .text{background:#1a1a1a;padding:1rem 1.5rem;border-radius:18px;display:inline-block;max-width:70%;}
.input-section{background:#1a1a1a;padding:1.5rem 2rem;border-top:1px solid #333;display:flex;gap:1rem;}
#messageInput{flex:1;background:#2a2a2a;border:1px solid #444;border-radius:25px;padding:1rem 1.5rem;color:#e0e0e0;font-size:1rem;}
#sendBtn{width:60px;height:50px;border-radius:50%;font-size:1.2rem;}
</style></head>
<body><div class="container">
<div id="name-screen" class="name-screen"><div class="name-container">
<h2>Enter Your Name</h2><input id="nameInput" placeholder="Your name" maxlength="20">
<button id="setNameBtn">Start Chatting</button></div></div>
<div id="chat-screen" class="chat-screen"><div class="header"><h2 id="currentGroup">No Group</h2></div>
<div class="group-section"><select id="groupSelect"><option value="">Select or create group</option></select>
<button id="createGroupBtn" class="btn">New Group</button></div><div id="messages" class="messages"></div>
<div class="input-section"><input id="messageInput" placeholder="Type a message..." disabled>
<button id="sendBtn" disabled>Send</button></div></div></div>
<script>
let user="",currentGroup="";document.addEventListener("DOMContentLoaded",()=>{document.getElementById("setNameBtn").onclick=setName;document.getElementById("nameInput").onkeypress=e=>e.key==="Enter"&&setName()});
async function setName(){user=document.getElementById("nameInput").value.trim().substring(0,20);if(!user)return alert("Please enter a name");document.getElementById("name-screen").style.display="none";document.getElementById("chat-screen").style.display="flex";document.getElementById("messageInput").disabled=false;loadGroups();setInterval(loadGroups,3e4);setInterval(()=>currentGroup&&loadMessages(),3e3)}
async function loadGroups(){try{const e=await fetch("/api/groups"),t=await e.json();document.getElementById("groupSelect").innerHTML='<option value="">Select or create group</option>';t.forEach(e=>{const t=document.createElement("option");t.value=e,t.textContent=e,document.getElementById("groupSelect").appendChild(t)})}catch(e){}}
document.getElementById("createGroupBtn").onclick=async()=>{try{const e=await fetch("/api/create-group",{method:"POST"}),t=await e.json();joinGroup(t.code)}catch(e){alert("Failed to create group")}};document.getElementById("groupSelect").onchange=e=>e.target.value&&joinGroup(e.target.value);document.getElementById("sendBtn").onclick=sendMessage;document.getElementById("messageInput").onkeypress=e=>e.key==="Enter"&&sendMessage();
async function joinGroup(e){currentGroup=e,document.getElementById("currentGroup").textContent=e,document.getElementById("sendBtn").disabled=false,loadMessages()}
async function loadMessages(){if(!currentGroup)return;try{const e=await fetch("/api/messages/"+currentGroup),t=await e.json();document.getElementById("messages").innerHTML=t.map(e=>`<div class="message"><div class="user">${escapeHtml(e.user)} <span style="color:#888;font-size:0.8rem">${e.timestamp}</span></div><div class="text">${escapeHtml(e.text)}</div></div>`).join(""),document.getElementById("messages").scrollTop=document.getElementById("messages").scrollHeight}catch(e){}}
async function sendMessage(){const e=document.getElementById("messageInput").value.trim();if(!e||!currentGroup||!user)return;try{const t=await fetch("/api/messages/"+currentGroup,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:e,timestamp:new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}),username:user})});t.ok&&(document.getElementById("messageInput").value="",loadMessages())}catch(e){alert("Failed to send")}}function escapeHtml(e){const t=document.createElement("div");return t.textContent=e,t.innerHTML}
</script></body></html>
        ''', 200

@app.route('/api/groups', methods=['GET', 'POST'])
def groups():
    if request.method == 'POST':
        data = request.get_json() or {}
        code = data.get('code', '').strip().upper()
        if len(code) == 10:
            if code not in groups:
                groups[code] = []
            return jsonify({'exists': True, 'code': code})
        return jsonify({'exists': False}), 400
    return jsonify(list(groups.keys())[:20])

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    groups[code] = []
    return jsonify({'code': code})

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
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
        return jsonify({'status': 'sent'})
    return jsonify(groups[code][-50:])
