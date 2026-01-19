from flask import Flask, request, jsonify
import random
import string
import json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

@app.route('/api/set-name', methods=['POST'])
def set_name():
    data = request.get_json()
    name = data.get('name', '').strip()[:20]
    resp = jsonify({'status': 'ok', 'name': name})
    resp.headers.add('X-User-Name', name)
    return resp

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return jsonify({'code': code, 'invite': f"{request.host}/join/{code}"})

@app.route('/api/join-group/<code>')
def join_group(code):
    return jsonify({'status': 'joined', 'code': code})

@app.route('/api/messages/<code>')
def get_messages(code):
    messages_json = request.headers.get('X-Messages-' + code, '[]')
    try:
        messages = json.loads(messages_json)[-50:]
    except:
        messages = []
    
    messages_html = ''
    for msg in messages:
        time_str = datetime.fromisoformat(msg['timestamp']).strftime('%I:%M:%S %p')
        messages_html += f'<div class="message"><strong>{msg["username"]}:</strong> <span style="opacity:0.7">{time_str}</span> {msg["text"]}</div>'
    return jsonify({'html': messages_html})

@app.route('/api/send-message/<code>', methods=['POST'])
def send_message(code):
    data = request.get_json()
    text = data.get('text', '').strip()[:200]
    username = data.get('username', 'Anonymous')
    
    if text:
        msg = {
            'username': username,
            'text': text,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify({'status': 'sent', 'message': msg})
    return jsonify({'status': 'empty'})

@app.route('/join/<code>')
def join_page(code):
    return f'''
    <!DOCTYPE html>
    <html><head><title>Joining {code}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script>window.groupCode='{code}';setTimeout(()=>window.location.href='/',1500);</script>
    </head><body style="background:#1a1a1a;color:#eee;font-family:Arial;text-align:center;padding-top:100px;">
    <h1>🔒 Joining Group {code}</h1><p>Redirecting...</p>
    </body></html>
    '''

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🔒 Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;font-size:16px;}
        body{background:#1a1a1a;color:#eee;padding:20px;min-height:100vh;}
        .name-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;text-align:center;}
        #nameInput{width:250px;max-width:90vw;padding:12px;border:none;border-radius:8px;background:#333;color:#eee;font-size:16px;}
        #setNameBtn{margin-top:15px;padding:12px 24px;background:#4CAF50;border:none;border-radius:8px;color:white;cursor:pointer;font-size:16px;font-weight:bold;}
        #setNameBtn:hover{background:#45a049;}
        #setNameBtn:active{background:#3d8b40;}
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
        <h1>🔒 Chat</h1>
        <p>Enter your name:</p>
        <input id="nameInput" type="text" placeholder="Your name..." maxlength="20" autofocus>
        <br><br>
        <button id="setNameBtn" onclick="setName()">Continue →</button>
    </div>
    
    <div id="chatScreen" class="chat-screen">
        <div class="header">
            <h2>Groups <span id="nameDisplay"></span></h2>
        </div>
        <div class="groups">
            <select id="groupSelect"><option>Select group or create new</option></select>
            <div id="groupInfo"></div>
            <button id="newGroupBtn">➕ New Group</button>
        </div>
        <div id="messages"></div>
        <div class="input-area">
            <input id="messageInput" type="text" placeholder="Type message..." maxlength="200">
            <button id="sendBtn">Send</button>
        </div>
    </div>

    <script>
        let currentGroup = '';
        let username = localStorage.getItem('chat_username') || '';
        let userGroups = JSON.parse(localStorage.getItem('chat_groups') || '{}');

        // CHECK FOR INVITE LINK
        if (window.groupCode) {
            const code = window.groupCode;
            userGroups[code] = userGroups[code] || [];
            localStorage.setItem('chat_groups', JSON.stringify(userGroups));
            skipToChat(code);
        } else {
            checkSavedName();
        }

        function checkSavedName() {
            if (username) {
                // SKIP NAME SCREEN - GO DIRECTLY TO CHAT
                document.getElementById('nameScreen').style.display = 'none';
                document.getElementById('chatScreen').style.display = 'flex';
                document.getElementById('nameDisplay').textContent = username + ' ';
                loadGroups();
                setInterval(chatLoop, 2000);
            } else {
                // FIRST TIME - SETUP NAME BUTTON
                document.getElementById('nameInput').focus();
            }
        }

        function setName() {
            username = document.getElementById('nameInput').value.trim();
            if (!username) {
                alert('Please enter a name');
                return;
            }
            localStorage.setItem('chat_username', username);
            skipToChat();
        }

        function skipToChat(code = null) {
            document.getElementById('nameScreen').style.display = 'none';
            document.getElementById('chatScreen').style.display = 'flex';
            document.getElementById('nameDisplay').textContent = username + ' ';
            
            if (code) {
                currentGroup = code;
                userGroups[code] = userGroups[code] || [];
                localStorage.setItem('chat_groups', JSON.stringify(userGroups));
            }
            
            loadGroups();
            if (currentGroup) {
                updateGroupInfo(currentGroup);
            }
            setInterval(chatLoop, 2000);
        }

        function chatLoop() {
            if (currentGroup) {
                loadMessages();
                saveGroups();
            }
        }

        function saveGroups() {
            localStorage.setItem('chat_groups', JSON.stringify(userGroups));
        }

        function loadGroups() {
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option>Select group or create new</option>';
            
            Object.keys(userGroups).forEach(code => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = code;
                select.appendChild(option);
            });
            
            if (Object.keys(userGroups).length > 0 && !currentGroup) {
                currentGroup = Object.keys(userGroups)[0];
                select.value = currentGroup;
                updateGroupInfo(currentGroup);
            }
        }

        function updateGroupInfo(code) {
            currentGroup = code;
            document.getElementById('groupInfo').innerHTML = 
                `<div class="group-info">
                    <span>${code}</span>
                    <button class="copy-btn" onclick="copyInvite('${code}')">📋</button>
                </div>`;
            loadMessages();
        }

        async function createGroup() {
            const res = await fetch('/api/create-group', {method: 'POST'});
            const data = await res.json();
            const code = data.code;
            userGroups[code] = userGroups[code] || [];
            saveGroups();
            loadGroups();
            document.getElementById('groupSelect').value = code;
            updateGroupInfo(code);
        }

        async function copyInvite(code) {
            const inviteUrl = `${window.location.origin}/join/${code}`;
            try {
                await navigator.clipboard.writeText(inviteUrl);
                event.target.textContent = '✓';
                setTimeout(() => event.target.textContent = '📋', 1000);
            } catch(e) {
                prompt('Copy this link:', inviteUrl);
            }
        }

        async function loadMessages() {
            if (!currentGroup) return;
            try {
                const messages = userGroups[currentGroup] || [];
                const res = await fetch(`/api/messages/${currentGroup}`, {
                    headers: {'X-Messages-' + currentGroup: JSON.stringify(messages)}
                });
                const data = await res.json();
                document.getElementById('messages').innerHTML = data.html || 
                    '<div style="opacity:0.5;text-align:center;padding:20px;">No messages yet</div>';
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            } catch(e) {}
        }

        async function sendMessage() {
            if (!currentGroup) return;
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (!text) return;
            
            input.disabled = true;
            input.value = 'Sending...';
            
            try {
                const res = await fetch(`/api/send-message/${currentGroup}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text, username})
                });
                const data = await res.json();
                
                if (data.status === 'sent' && data.message) {
                    if (!userGroups[currentGroup]) userGroups[currentGroup] = [];
                    userGroups[currentGroup].push(data.message);
                    saveGroups();
                }
            } catch(e) {}
            
            input.value = '';
            input.disabled = false;
            loadMessages();
        }

        // ✅ BULLETPROOF EVENT LISTENERS
        document.addEventListener('DOMContentLoaded', function() {
            const continueBtn = document.getElementById('setNameBtn');
            const nameInput = document.getElementById('nameInput');
            const newGroupBtn = document.getElementById('newGroupBtn');
            const sendBtn = document.getElementById('sendBtn');
            const groupSelect = document.getElementById('groupSelect');
            const messageInput = document.getElementById('messageInput');

            if (continueBtn) continueBtn.onclick = setName;
            if (nameInput) nameInput.onkeypress = function(e) { if (e.key === 'Enter') setName(); };
            if (newGroupBtn) newGroupBtn.onclick = createGroup;
            if (sendBtn) sendBtn.onclick = sendMessage;
            if (groupSelect) groupSelect.onchange = function() { if (this.value) updateGroupInfo(this.value); };
            if (messageInput) messageInput.onkeypress = function(e) { if (e.key === 'Enter') sendMessage(); };
        });
    </script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
