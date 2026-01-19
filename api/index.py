from flask import Flask, request, jsonify
import random
import string
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/api/create-group', methods=['POST'])
def create_group():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return jsonify({'code': code, 'invite': f"{request.host}/join/{code}"})

@app.route('/api/messages/<code>')
def get_messages(code):
    messages_json = request.headers.get('X-Messages-' + code, '[]')
    try:
        messages = json.loads(messages_json)[-50:]
    except:
        messages = []
    
    messages_html = ''
    for msg in messages:
        try:
            time_str = datetime.fromisoformat(msg['timestamp']).strftime('%I:%M:%S %p')
        except:
            time_str = 'now'
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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<script>window.groupCode='{code}';setTimeout(()=>{{window.location.href='/'}},1000);</script>
</head><body style="background:#111;color:#eee;font-family:Arial;text-align:center;padding-top:100px;">
<h1>Joining {code}</h1><p>Redirecting...</p></body></html>'''

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '''
<!DOCTYPE html>
<html>
<head>
<title>Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial;font-size:16px;}
body{background:#111;color:#eee;padding:20px;}
#nameScreen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:70vh;}
#nameInput{{width:280px;max-width:90vw;padding:15px;border:none;border-radius:8px;background:#333;color:#fff;}}
#continueBtn{{padding:15px 30px;background:#4CAF50;border:none;border-radius:8px;color:white;font-size:18px;font-weight:bold;cursor:pointer;margin-top:20px;}}
#continueBtn:hover{{background:#45a049;}}
#chatScreen{{display:none;flex-direction:column;height:100vh;max-width:600px;margin:0 auto;}}
.header{{padding:20px;background:#222;text-align:center;}}
.groups{{padding:15px;background:#333;}}
#groupSelect{{width:100%;padding:12px;border:none;border-radius:6px;background:#444;color:#eee;margin-bottom:10px;}}
#groupInfo{{margin-bottom:10px;}}
.group-info{{background:#444;padding:10px;border-radius:6px;display:flex;align-items:center;}}
.copy-btn{{background:#666;color:white;border:none;border-radius:50%;width:35px;height:35px;font-size:16px;cursor:pointer;margin-left:10px;}}
#newGroupBtn{{width:100%;padding:12px;background:#4CAF50;border:none;border-radius:6px;color:white;cursor:pointer;}}
#messages{{flex:1;overflow-y:auto;padding:15px;background:#222;}}
.message{{margin-bottom:12px;padding:10px;background:#333;border-radius:6px;}}
.input-area{{padding:15px;background:#333;}}
#messageInput{{width:calc(100% - 70px);padding:12px;border:none;border-radius:6px;background:#444;color:#eee;}}
#sendBtn{{width:65px;padding:12px;background:#2196F3;border:none;border-radius:6px;color:white;cursor:pointer;}}
#nameDisplay{{color:#4CAF50;font-weight:bold;}}
@media (max-width:480px){{body{padding:10px;}}}
</style>
</head>
<body>

<div id="nameScreen">
<h1>🔒 Chat</h1>
<p>Enter your name:</p>
<input id="nameInput" type="text" placeholder="Your name" maxlength="20">
<br><br>
<button id="continueBtn">Continue →</button>
</div>

<div id="chatScreen" style="display:none;">
<div class="header">
<h2>Groups <span id="nameDisplay"></span></h2>
</div>
<div class="groups">
<select id="groupSelect"><option value="">Select or create group</option></select>
<div id="groupInfo"></div>
<button id="newGroupBtn">➕ New Group</button>
</div>
<div id="messages">Select a group to start chatting</div>
<div class="input-area">
<input id="messageInput" type="text" placeholder="Type message..." maxlength="200">
<button id="sendBtn">Send</button>
</div>
</div>

<script>
let currentGroup = '';
let username = localStorage.getItem('username') || '';
let groups = JSON.parse(localStorage.getItem('groups') || '{}');

// CREATE BUTTON AFTER SCRIPT LOADS
document.getElementById('continueBtn').onclick = function() {{
    let name = document.getElementById('nameInput').value.trim();
    if(name.length < 1) {{
        alert('Enter a name!');
        return;
    }}
    localStorage.setItem('username', name);
    username = name;
    document.getElementById('nameScreen').style.display = 'none';
    document.getElementById('chatScreen').style.display = 'flex';
    document.getElementById('nameDisplay').innerText = username;
    loadGroups();
}};

// CHECK INVITE OR SAVED NAME
if(window.groupCode){{
    groups[window.groupCode] = [];
    localStorage.setItem('groups', JSON.stringify(groups));
    username = localStorage.getItem('username') || 'Guest';
    document.getElementById('nameScreen').style.display = 'none';
    document.getElementById('chatScreen').style.display = 'flex';
    document.getElementById('nameDisplay').innerText = username;
    currentGroup = window.groupCode;
    loadGroups();
}} else if(username){{
    document.getElementById('nameScreen').style.display = 'none';
    document.getElementById('chatScreen').style.display = 'flex';
    document.getElementById('nameDisplay').innerText = username;
    loadGroups();
}}

function loadGroups(){{
    const select = document.getElementById('groupSelect');
    select.innerHTML = '<option value="">Select or create group</option>';
    Object.keys(groups).forEach(code => {{
        const option = document.createElement('option');
        option.value = code;
        option.textContent = code;
        select.appendChild(option);
    }});
    if(currentGroup && groups[currentGroup]){{
        select.value = currentGroup;
        showGroupInfo(currentGroup);
    }}
}}

document.getElementById('groupSelect').onchange = function(){{
    if(this.value) showGroupInfo(this.value);
}};

function showGroupInfo(code){{
    currentGroup = code;
    document.getElementById('groupInfo').innerHTML = 
        `<div class="group-info">
            <span>${{code}}</span>
            <button class="copy-btn" onclick="copyInvite('${{code}}')">📋</button>
        </div>`;
    loadMessages();
}}

document.getElementById('newGroupBtn').onclick = function(){{
    fetch('/api/create-group', {{method: 'POST'}})
    .then(r=>r.json())
    .then(data=>{{
        const code = data.code;
        groups[code] = [];
        localStorage.setItem('groups', JSON.stringify(groups));
        loadGroups();
        document.getElementById('groupSelect').value = code;
        showGroupInfo(code);
    }});
}};

function copyInvite(code){{
    const url = window.location.origin + '/join/' + code;
    navigator.clipboard.writeText(url).then(()=>{{
        event.target.innerText = '✓';
        setTimeout(()=>event.target.innerText='📋', 1000);
    }});
}}

document.getElementById('sendBtn').onclick = sendMessage;
document.getElementById('messageInput').onkeypress = function(e){{
    if(e.key === 'Enter') sendMessage();
}};

function sendMessage(){{
    if(!currentGroup) return;
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if(!text) return;
    
    input.disabled = true;
    input.value = 'Sending...';
    
    fetch('/api/send-message/' + currentGroup, {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{text, username}})
    }})
    .then(r=>r.json())
    .then(data=>{{
        if(data.status === 'sent' && data.message){{
            if(!groups[currentGroup]) groups[currentGroup] = [];
            groups[currentGroup].push(data.message);
            localStorage.setItem('groups', JSON.stringify(groups));
        }}
        input.value = '';
        input.disabled = false;
        loadMessages();
    }});
}}

function loadMessages(){{
    if(!currentGroup) return;
    const messages = groups[currentGroup] || [];
    fetch('/api/messages/' + currentGroup, {{
        headers: {{'X-Messages-'+currentGroup: JSON.stringify(messages)}}
    }})
    .then(r=>r.json())
    .then(data=>{{
        document.getElementById('messages').innerHTML = data.html || 
            '<div style="opacity:0.5;text-align:center;padding:40px;">No messages yet</div>';
        document.getElementById('messages').scrollTop = 99999;
    }});
}}

setInterval(()=>{{
    if(currentGroup) loadMessages();
}}, 2000);
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
