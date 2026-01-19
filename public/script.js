let currentGroup = '';
let user = 'Anonymous';
let authenticated = true;

function init() {
    // Skip login check - go straight to chat
    showChat();
    loadGroups();
    
    currentGroup = localStorage.getItem('currentGroup') || '';
    if (currentGroup) {
        document.getElementById('codeInput').value = currentGroup;
        joinGroup(currentGroup);
    }
    
    setInterval(loadGroups, 30000);
}

function showChat() {
    document.getElementById('login-prompt').style.display = 'none';
    document.getElementById('chat-section').style.display = 'block';
    document.getElementById('header').style.display = 'flex';
    document.querySelectorAll('button:not(.logout), input, select').forEach(el => el.disabled = false);
    document.getElementById('user-display').textContent = `Logged in as ${user}`;
}

async function loadGroups() {
    try {
        const res = await fetch('/api/groups');
        const codes = await res.json();
        const select = document.getElementById('groupSelect');
        select.innerHTML = '<option>Select a group...</option>';
        codes.forEach(code => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = code;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('Failed to load groups');
    }
}

async function createGroup() {
    try {
        const res = await fetch('/api/create-group', { method: 'POST' });
        const data = await res.json();
        joinGroup(data.code);
    } catch (e) {
        alert('Failed to create group');
    }
}

async function joinGroup(code = null) {
    const inputCode = code || document.getElementById('codeInput').value.trim().toUpperCase();
    if (!inputCode || inputCode.length !== 10) {
        alert('Enter valid 10-character code');
        return;
    }

    try {
        await fetch('/api/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: inputCode })
        });
        
        currentGroup = inputCode;
        localStorage.setItem('currentGroup', currentGroup);
        document.getElementById('groupSelect').value = inputCode;
        document.getElementById('groupCode').textContent = `Group: ${currentGroup}`;
        document.getElementById('codeInput').value = '';
        loadMessages();
    } catch (e) {
        alert('Failed to join group');
    }
}

async function loadMessages() {
    if (!currentGroup) return;
    try {
        const res = await fetch(`/api/messages/${currentGroup}`);
        const messages = await res.json();
        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = messages.map(msg => `
            <div class="message">
                <div>
                    <span class="user">${escapeHtml(msg.user)}</span>
                    <span class="time">${msg.timestamp || ''}</span>
                </div>
                <div class="text">${escapeHtml(msg.text)}</div>
            </div>
        `).join('');
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (e) {
        console.error('Failed to load messages');
    }
}

document.getElementById('msgForm').onsubmit = async (e) => {
    e.preventDefault();
    if (!currentGroup) return;
    
    const input = document.getElementById('msgInput');
    const text = input.value.trim();
    if (!text) return;
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    try {
        await fetch(`/api/messages/${currentGroup}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, timestamp })
        });
        input.value = '';
        loadMessages();
    } catch (e) {
        alert('Failed to send message');
    }
};

document.getElementById('groupSelect').onchange = (e) => {
    if (e.target.value) joinGroup(e.target.value);
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

setInterval(() => {
    if (currentGroup) loadMessages();
}, 3000);

window.onload = init;
