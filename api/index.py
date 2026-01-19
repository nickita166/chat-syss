from flask import Flask, request, jsonify
import random
import string

app = Flask(__name__)
groups = {}

# API ROUTES FIRST (CRITICAL ORDER)
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
            groups[code].append({
                'user': username,
                'text': text, 
                'timestamp': timestamp
            })
            if len(groups[code]) > 500:
                groups[code] = groups[code][-500:]
        return jsonify({'status': 'sent'})
    
    return jsonify(groups[code][-50:])

# Catch-all route LAST
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
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
            padding: 1.2rem 1.5rem; font-size: 1.2rem; color: #e0e0e0; width: 320px; margin-bottom: 1.5rem;
        }
        #nameInput:focus { outline: none; border-color: #00ff88; }
        #setNameBtn { 
            background: linear-gradient(135deg, #00ff88, #00cc6a); border: none; border-radius: 12px; 
            padding: 1.2rem 2.5rem; font-size: 1.2rem; font-weight: 600; color: #000; cursor: pointer; 
        }
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
        #messageInput { flex: 1; background: #2a2a2a; border: 1px solid #444; border-radius: 25px; padding: 1rem 1.5rem; color: #e0e0e0; }
        #sendBtn { width: 60px; height: 50px; border-radius: 50%; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Name Screen -->
        <div id="name-screen" class="name-screen">
            <div class="name-container">
                <h2>Enter Your Name</h2>
                <input id="nameInput" placeholder="Your name (max 20 chars)" maxlength="20">
                <button id="setNameBtn">Start Chatting</button>
            </div>
        </div>
        
        <!-- Chat Screen -->
        <div id="chat-screen" class="chat-screen">
            <div class="header">
                <h2 id="currentGroup">No Group Selected</h2>
            </div>
            <div class="group-section">
                <select id="groupSelect">
                    <option value="">Select or create group</option>
                </select>
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
        let user = '';
        let currentGroup = '';

        // Initialize app
        function init() {
            const nameInput = document.getElementById('nameInput');
            const setNameBtn = document.getElementById('setNameBtn');
            
            nameInput.focus();
            setNameBtn.onclick = setName;
            nameInput.onkeypress = (e) => e.key === 'Enter' && setName();
            
            // Chat event handlers
            document.getElementById('createGroupBtn').onclick = createGroup;
            document.getElementById('groupSelect').onchange = (e) => {
                if (e.target.value) joinGroup(e.target.value);
            };
            document.getElementById('sendBtn').onclick = sendMessage;
            document.getElementById('messageInput').onkeypress = (e) => e.key === 'Enter' && sendMessage();
        }

        function setName() {
            user = document.getElementById('nameInput').value.trim().slice(0, 20);
            if (!user) {
                alert('Please enter a name');
                return;
            }
            
            document.getElementById('name-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'flex';
            loadGroups();
            
            // Auto-refresh
            setInterval(loadGroups, 10000);
            setInterval(() => { if (currentGroup) loadMessages(); }, 2000);
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
            } catch (e) {
                console.error('Load groups failed');
            }
        }

        async function createGroup() {
            try {
                const res = await fetch('/api/create-group');
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
            document.getElementById('messageInput').disabled = false;  // ENABLE HERE
            loadMessages();
        }

        async function loadMessages() {
            if (!currentGroup) return;
            try {
                const res = await fetch('/api/messages/' + currentGroup);
                const messages = await res.json();
                const container = document.getElementById('messages');
                container.innerHTML = messages.map(msg => `
                    <div class="message">
                        <div class="user">${escapeHtml(msg.user)} <span style="color:#888;font-size:0.8rem">${msg.timestamp}</span></div>
                        <div class="text">${escapeHtml(msg.text)}</div>
                    </div>
                `).join('');
                container.scrollTop = container.scrollHeight;
            } catch (e) {
                console.error('Load messages failed');
            }
        }

        async function sendMessage() {
            const text = document.getElementById('messageInput').value.trim();
            if (!text || !currentGroup || !user) return;
            
            try {
                await fetch('/api/messages/' + currentGroup, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
                        username: user
                    })
                });
                document.getElementById('messageInput').value = '';
                loadMessages();
            } catch (e) {
                alert('Failed to send message');
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Start app
        window.onload = init;
    </script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
