from flask import Flask, request, jsonify, session
import random
import string
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRETKEY', 'devkey-change-production')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:20]
        if name:
            session['username'] = name
            return '''
<!DOCTYPE html>
<html>
<head>
<title>Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial;font-size:16px;}
body{background:#111;color:#eee;padding:20px;}
#chatScreen{flex-direction:column;height:100vh;max-width:600px;margin:0 auto;}
.header{padding:20px;background:#222;text-align:center;}
.groups{padding:15px;background:#333;}
#groupSelect{width:100%;padding:12px;border:none;border-radius:6px;background:#444;color:#eee;margin-bottom:10px;}
#groupInfo{margin-bottom:10px;}
.group-info{background:#444;padding:10px;border-radius:6px;display:flex;align-items:center;}
.copy-btn{background:#666;color:white;border:none;border-radius:50%;width:35px;height:35px;font-size:16px;cursor:pointer;margin-left:10px;}
#newGroupBtn{width:100%;padding:12px;background:#4CAF50;border:none;border-radius:6px;color:white;cursor:pointer;}
#messages{flex:1;overflow-y:auto;padding:15px;background:#222;}
.message{margin-bottom:12px;padding:10px;background:#333;border-radius:6px;}
.input-area{padding:15px;background:#333;}
#messageInput{width:calc(100% - 70px);padding:12px;border:none;border-radius:6px;background:#444;color:#eee;}
#sendBtn{width:65px;padding:12px;background:#2196F3;border:none;border-radius:6px;color:white;cursor:pointer;}
#nameDisplay{color:#4CAF50;font-weight:bold;}
@media (max-width:480px){body{padding:10px;}}
</style>
</head>
<body>
<div id="chatScreen" style="display:flex;">
<div class="header">
<h2>Groups <span id="nameDisplay">' + name + '</span></h2>
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
let currentGroup = "";
let username = "' + name + '"; 
let groups = JSON.parse(localStorage.getItem("groups") || "{}");

// Load groups on start
loadGroups();

function loadGroups(){
    const select = document.getElementById("groupSelect");
    select.innerHTML = '<option value="">Select or create group</option>';
    Object.keys(groups).forEach(code => {
        const option = document.createElement("option");
        option.value = code;
        option.textContent = code;
        select.appendChild(option);
    });
}

document.getElementById("groupSelect").onchange = function(){
    if(this.value) showGroupInfo(this.value);
};

function showGroupInfo(code){
    currentGroup = code;
    document.getElementById("groupInfo").innerHTML = 
        `<div class="group-info">
            <span>${code}</span>
            <button class="copy-btn" onclick="copyInvite('${code}')">📋</button>
        </div>`;
    loadMessages();
}

document.getElementById("newGroupBtn").onclick = function(){
    fetch("/api/create-group", {method: "POST"})
    .then(r=>r.json())
    .then(data=>{
        const code = data.code;
        groups[code] = [];
        localStorage.setItem("groups", JSON.stringify(groups));
        loadGroups();
        document.getElementById("groupSelect").value = code;
        showGroupInfo(code);
    });
};

function copyInvite(code){
    const url = window.location.origin + "/join/" + code;
    navigator.clipboard.writeText(url);
    event.target.innerText = "✓";
    setTimeout(()=>event.target.innerText="📋", 1000);
}

document.getElementById("sendBtn").onclick = sendMessage;
document.getElementById("messageInput").onkeypress = function(e){
    if(e.key === "Enter") sendMessage();
};

function sendMessage(){
    if(!currentGroup) return;
    const input = document.getElementById("messageInput");
    const text = input.value.trim();
    if(!text) return;
    
    input.disabled = true;
    input.value = "Sending...";
    
    fetch("/api/send-message/" + currentGroup, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text, username})
    })
    .then(r=>r.json())
    .then(data=>{
        if(data.status === "sent" && data.message){
            if(!groups[currentGroup]) groups[currentGroup] = [];
            groups[currentGroup].push(data.message);
            localStorage.setItem("groups", JSON.stringify(groups));
        }
        input
