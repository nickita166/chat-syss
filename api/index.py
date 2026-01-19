from flask import Flask, request, jsonify
import random
import string

app = Flask(__name__)
groups = {}

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Black Group Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: #000; color: #e0e0e0; height: 100vh; overflow: hidden;
        }
        .container { max-width: 900px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; }
        .name-screen { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background: #000; }
        .name-container { text-align: center; padding: 2rem; }
        .name-container h2 { font-size: 2.5rem; margin-bottom: 2rem; color: #fff; }
        #nameInput { 
            background: #1a1a1a; border: 2px solid #333; border-radius: 12px; 
            padding: 1rem 1.5rem; font-size: 1.2rem; color: #e0e0e0; width: 300px; margin-bottom: 1.5rem;
            transition: border-color 0.3s;
        }
        #nameInput:focus { outline: none; border-color: #00ff88; }
        #setNameBtn { 
            background: linear-gradient(135deg, #00ff88, #00cc6a); border: none; border-radius: 12px; 
            padding: 1rem 2.5rem; font-size: 1.2rem; font-weight: 600; color: #000; cursor: pointer; 
            transition: transform 0.2s;
        }
        #setNameBtn:hover { transform: scale(1.05); }
        .chat-screen { display: none; height: 100vh; }
        .header { background: #111; padding: 1rem 2rem; border-bottom: 1px solid #333; }
        .group-section { background: #1a1a1a; padding: 1rem 2rem; border-bottom: 1px solid #333; display: flex; gap: 1rem; align-items: center; }
        #groupSelect { flex: 1; background: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 0.8rem; color: #e0e0e0; }
        .btn { background: #00ff88; border: none; border-radius: 8px; padding: 0.8rem 1.5rem; color: #000; font-weight: 600; cursor: pointer; }
        .messages { flex: 1; overflow-y: auto; padding: 2rem; background: #000; }
        .message { margin-bottom: 1.5rem; }
        .message .user { font-weight: 600; color: #00ff88; margin-bottom: 0.3rem; font-size: 0.9rem; }
        .message .text { background: #1a1a1a; padding: 1rem 1.5rem; border-radius: 18px; display: inline-block; max-width: 70%; }
        .input-section { background: #1a1a1a; padding: 1.5rem 2rem; border-top: 1px solid #333; display: flex; gap: 1rem; }
        #messageInput { flex: 1; background: #2a2a2a; border: 1px solid #444; border-radius: 25px; padding: 1rem 1.5rem; color: #e0e0e0; font-size: 1rem; }
        #sendBtn { width: 60px; height: 50px; border-radius: 50%; font-size: 1.2rem; }
    </style>
</head>
<body>
    <div class="container">
        <div id="name-screen" class="name-screen">
            <div class="name-container">
                <h2>Enter Your Name</h2>
                <input id="nameInput" placeholder="Your name (max 20 chars)" maxlength="20" autofocus>
                <button id="setNameBtn">Start Chatting</button>
            </div>
        </div>
        <div id="chat-screen" class="chat-screen">
            <div class="header"><h2 id="currentGroup">No Group</h2></div>
            <div class="group-section">
                <select id="groupSelect"><option value="">Select or create group</option></select>
                <button id="createGroupBtn" class="btn">New Group</button>
            </div>
            <div id="messages" class="messages"></div>
            <div class="input-section">
                <input id="messageInput" placeholder="Type a message..." disabled>
                <button id="sendBtn" disabled>Send</button>
            </div>
        </div>
    </div>
    <script>
        let user = '', currentGroup = '';
        
        // Fix: Proper event listeners after DOM loads
        document.addEventListener('DOMContentLoaded', function() {
            const nameInput = document.getElementById('nameInput');
            const setNameBtn = document.getElementById('setNameBtn');
            
            // Focus input automatically
            nameInput.focus();
            
            // Button click
            setNameBtn.addEventListener('click', setName);
            
            // Enter key
            nameInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') setName();
            });
        });
        
        function setName() {
            user = document.getElementById('nameInput').value.trim().substring(0, 20);
            if (!user) return alert('Please enter a name');
            
            document.getElementById('name-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'flex';
            document.getElementById('messageInput').disabled = false;
            
            loadGroups();
            setInterval(loadGroups, 30000);
            setInterval(() => { if (currentGroup) loadMessages(); }, 3000);
        }
        
        async function loadGroups() {
            try {
                const res = await fetch('/api/groups');
                const codes = await res.json();
                const select = document.getElementById('groupSelect');
                select.innerHTML = '<option value="">Select or create group</option>';
                codes.forEach(code => {
                    const option = document.createElement('option');
                    option.value = code;
                    option.textContent = code;
                    select.appendChild(option);
                });
            } catch (e) {}
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('createGroupBtn').addEventListener('click', createGroup);
            document.getElementById('groupSelect').addEventListener('change', function(e) {
                if (e.target.value) joinGroup(e.target.value);
            });
            document.getElementById('sendBtn').addEventListener('click', sendMessage);
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        });
        
        async function createGroup() {
            try {
                const res = await fetch('/api/create-group', { method: 'POST' });
                const data = await res.json();
                joinGroup(data.code);
            } catch (e) {
                alert('Failed to create group');
            }
        }
        
        function joinGroup(code) {
            currentGroup = code;
            document.getElementById('currentGroup').textContent = code;
            document.getElementById('sendBtn').disabled = false;
            loadMessages();
        }
        
        async function loadMessages() {
            if (!currentGroup) return;
            try {
                const res = await fetch('/api/messages/' + currentGroup);
                const messages = await res.json();
                const container = document.getElementById('messages');
                container.innerHTML = messages.map(msg => 
                    `<div class="message">
                        <div class="user">${escapeHtml(msg.user)} <span style="color:#888;font-size:0.8rem">${msg.timestamp}</span></div>
                        <div class="text">${escapeHtml(msg.text)}</div>
                    </div>`
                ).join('');
                container.scrollTop = container.scrollHeight;
            } catch (e) {}
        }
        
        async function sendMessage() {
            const text = document.getElementById('messageInput').value.trim();
            if (!text || !currentGroup || !user) return;
            try {
                const res = await fetch('/api/messages/' + currentGroup, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                        username: user
                    })
                });
                if (res.ok) {
                    document.getElementById('messageInput').value = '';
                    loadMessages();
                }
            } catch (e) {
                alert('Failed to send');
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
    '''
    
# Keep all API routes exactly the same (groups, create-group, messages)
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
