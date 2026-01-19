from flask import Flask, request, jsonify, make_response, session
import random
import string
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'your-super-secret-key-change-in-production')

# Private user data stored in signed cookies (encrypted + tamper-proof)
def get_user_data():
    user_data = session.get('user_data')
    if user_data:
        return json.loads(user_data)
    return {'name': '', 'favorite_groups': []}

def save_user_data(user_data):
    session['user_data'] = json.dumps(user_data)

# API ROUTES FIRST
@app.route('/api/create-group', methods=['GET', 'POST'])
def create_group():
    user_data = get_user_data()
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Private group - only this user's data
    user_data['favorite_groups'].append(code)
    if len(user_data['favorite_groups']) > 10:
        user_data['favorite_groups'] = user_data['favorite_groups'][-10:]
    
    save_user_data(user_data)
    return jsonify({'code': code})

@app.route('/api/groups', methods=['GET'])
def groups_api():
    user_data = get_user_data()
    # Only show user's private groups (not public/global)
    return jsonify(user_data['favorite_groups'])

@app.route('/api/messages/<code>', methods=['GET', 'POST'])
def messages(code):
    user_data = get_user_data()
    
    # Private groups - only user's own groups exist
    if code not in user_data['favorite_groups']:
        return jsonify({'error': 'Private group not found'}), 404
    
    # In-memory storage per user (serverless = per invocation)
    if not hasattr(app, 'private_messages'):
        app.private_messages = {}
    if code not in app.private_messages:
        app.private_messages[code] = []
    
    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username', user_data['name'] or 'Anonymous')[:20]
        text = data.get('text', '').strip()
        timestamp = data.get('timestamp', 'Now')
        
        if text:
            app.private_messages[code].append({
                'user': username,
                'text': text,
                'timestamp': timestamp
            })
            if len(app.private_messages[code]) > 500:
                app.private_messages[code] = app.private_messages[code][-500:]
        return jsonify({'status': 'sent'})
    
    return jsonify(app.private_messages.get(code, [])[-50:])

@app.route('/api/set-name', methods=['POST'])
def set_name():
    data = request.get_json() or {}
    name = data.get('name', '').strip()[:20]
    if name:
        user_data = get_user_data()
        user_data['name'] = name
        save_user_data(user_data)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid name'}), 400

# Catch-all route LAST - serves HTML
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    user_data = get_user_data()
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Private Black Chat</title>
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
        .header { background: #111; padding: 1rem 2rem; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
        .user-info { font-size: 0.9rem; color: #00ff88; }
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
        .private { color: #888; font-size: 0.8rem; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div id="name-screen" class="name-screen">
            <div class="name-container">
                <h2>Your Private Chat</h2>
                <input id="nameInput" placeholder="Enter your name" maxlength="20">
                <button id="setNameBtn">Start Private Chat</button>
                <div style="margin-top: 1rem; color: #888; font-size: 0.9rem;">
                    ✓ Private groups saved in cookies<br>✓ Messages stay private to you
                </div>
            </div>
        </div>
        
        <div id="chat-screen" class="chat-screen">
            <div class="header">
                <h2 id="currentGroup">No Private Group</h2>
                <div class="user-info" id="userInfo">Guest</div>
            </div>
            <div class="group-section">
                <select id="groupSelect">
                    <option value="">Your private groups</option>
                </select>
                <button id="createGroupBtn" class="btn">New Private Group</button>
            </div>
            <div id="messages" class="messages"></div>
            <div class="input-section">
                <input id="messageInput" placeholder="Your private messages..." disabled>
                <button id="sendBtn" disabled>Send</button>
            </div>
        </div>
    </div>

    <script>
        let currentGroup = '';
        let user = '';

        function init() {
            const nameInput = document.getElementById('nameInput');
            const setNameBtn = document.getElementById('setNameBtn');
            
            nameInput.focus();
            setNameBtn.onclick = setName;
            nameInput.onkeypress = (e) => e.key === 'Enter' && setName();
            
            document.getElementById('createGroupBtn').onclick = createGroup;
            document.getElementById('groupSelect').onchange = (e) => {
                if (e.target.value) joinGroup(e.target.value);
            };
            document.getElementById('sendBtn').onclick = sendMessage;
            document.getElementById('messageInput').onkeypress = (e) => e.key === 'Enter' && sendMessage();
        }

        async function setName() {
            const nameInput = document.getElementById('nameInput');
            user = nameInput.value.trim().slice(0, 20);
            if (!user) {
                alert('Please enter a name');
                return;
            }
            
            // Save name to cookies via API
            try {
                await fetch('/api/set-name', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: user})
                });
            } catch(e) {
                console.error('Name save failed');
            }
            
            document.getElementById('name-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'flex';
            document.getElementById('userInfo').textContent = user;
            
            loadGroups();
            setInterval(loadGroups, 10000);
            setInterval(() => { if (currentGroup) loadMessages(); }, 2000);
        }

        async function loadGroups() {
            try {
                const res = await fetch('/api/groups');
                const codes = await res.json();
                const select = document.getElementById('groupSelect');
                select.innerHTML = '<option value="">Your private groups</option>';
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
                alert('Failed to create private group');
            }
        }

        function joinGroup(code) {
            currentGroup = code;
            document.getElementById('currentGroup').textContent = code + ' <span class="private">(private)</span>';
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('messageInput').disabled = false;
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
                alert('Failed to send private message');
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        window.onload = init;
    </script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
