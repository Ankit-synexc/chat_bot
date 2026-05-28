// Configure your backend URL here (e.g. for Render)
const API_BASE_URL = 'http://127.0.0.1:8000';

// State
let token = localStorage.getItem('access_token');
let user = null;

// DOM Elements
const screens = {
    auth: document.getElementById('auth-screen'),
    app: document.getElementById('app-screen')
};
const views = {
    chat: document.getElementById('chat-section'),
    admin: document.getElementById('admin-section')
};
const navBtns = {
    chat: document.getElementById('nav-chat'),
    admin: document.getElementById('nav-admin')
};

// Initialization
async function init() {
    if (token) {
        await fetchUserProfile();
    } else {
        showScreen('auth');
    }
}

// Navigation
function showScreen(screenName) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[screenName].classList.add('active');
}

function showView(viewName) {
    Object.values(views).forEach(v => v.classList.remove('active'));
    Object.values(navBtns).forEach(b => b.classList.remove('active'));
    
    views[viewName].classList.add('active');
    navBtns[viewName].classList.add('active');
    
    if (viewName === 'admin') {
        loadDocuments();
    }
}

navBtns.chat.addEventListener('click', () => showView('chat'));
navBtns.admin.addEventListener('click', () => showView('admin'));

document.getElementById('logout-btn').addEventListener('click', () => {
    token = null;
    user = null;
    localStorage.removeItem('access_token');
    showScreen('auth');
    document.getElementById('chat-history').innerHTML = `
        <div class="message system-message">
            <div class="message-content">
                Welcome to the Synexc AI Knowledge Portal. How can I assist you today?
            </div>
        </div>
    `;
});

// Authentication
async function fetchUserProfile() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Invalid token');
        
        user = await res.json();
        document.getElementById('user-greeting').textContent = `Hello, ${user.username}`;
        
        if (user.is_admin) {
            navBtns.admin.classList.remove('hidden');
        } else {
            navBtns.admin.classList.add('hidden');
        }
        
        showScreen('app');
        showView('chat');
    } catch (err) {
        console.error(err);
        token = null;
        localStorage.removeItem('access_token');
        showScreen('auth');
    }
}

document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const isLogin = e.submitter.id === 'login-btn';
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');
    errorEl.textContent = '';
    errorEl.className = 'error-message';

    try {
        if (isLogin) {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            
            const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Login failed');
            }
            
            const data = await res.json();
            token = data.access_token;
            localStorage.setItem('access_token', token);
            await fetchUserProfile();
        } else {
            // Register
            const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Registration failed');
            }
            
            errorEl.textContent = 'Registration successful! Please login.';
            errorEl.className = 'success-message';
        }
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.className = 'error-message';
    }
});

// Chat Interface
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');

// Auto-resize textarea
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Parse markdown for system messages
    if (role === 'system') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    msgDiv.appendChild(contentDiv);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return contentDiv;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;
    
    appendMessage('user', query);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    const contentDiv = appendMessage('system', '');
    contentDiv.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/query/ask/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ query: query, max_results: 5, stream: true })
        });
        
        if (!res.ok) {
            if (res.status === 401) throw new Error("Unauthorized");
            if (res.status === 429) throw new Error("Rate limit exceeded");
            throw new Error('Failed to fetch response');
        }
        
        contentDiv.innerHTML = '';
        let fullResponse = '';
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.substring(6);
                    if (data === '[DONE]') continue;
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.token) {
                            fullResponse += parsed.token;
                            contentDiv.innerHTML = marked.parse(fullResponse);
                            chatHistory.scrollTop = chatHistory.scrollHeight;
                        }
                    } catch (e) {
                        // ignore parse errors for partial chunks
                    }
                }
            }
        }
    } catch (err) {
        contentDiv.innerHTML = `<span style="color: #e11d48;">Error: ${err.message}</span>`;
    }
});

// Admin Interface
const uploadForm = document.getElementById('upload-form');
const docList = document.getElementById('document-list');

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('document-file');
    const file = fileInput.files[0];
    if (!file) return;
    
    const statusEl = document.getElementById('upload-status');
    statusEl.innerHTML = '<div class="success-message">Uploading...</div>';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!res.ok) throw new Error('Upload failed');
        
        statusEl.innerHTML = '<div class="success-message">Upload successful!</div>';
        fileInput.value = '';
        loadDocuments();
        
        setTimeout(() => { statusEl.innerHTML = ''; }, 3000);
    } catch (err) {
        statusEl.innerHTML = `<div class="error-message">Error: ${err.message}</div>`;
    }
});

document.getElementById('refresh-docs-btn').addEventListener('click', loadDocuments);

async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/documents/list`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Failed to fetch documents');
        
        const docs = await res.json();
        docList.innerHTML = '';
        
        if (docs.length === 0) {
            docList.innerHTML = '<li class="doc-item"><p>No documents found.</p></li>';
            return;
        }
        
        docs.forEach(doc => {
            const li = document.createElement('li');
            li.className = 'doc-item';
            
            const date = new Date(doc.upload_date).toLocaleDateString();
            
            li.innerHTML = `
                <div class="doc-info">
                    <h4>${doc.filename}</h4>
                    <p>ID: ${doc.id} | Chunks: ${doc.chunks_count} | Uploaded: ${date}</p>
                </div>
                <button class="btn btn-small btn-danger" onclick="deleteDocument('${doc.id}')">Delete</button>
            `;
            docList.appendChild(li);
        });
    } catch (err) {
        docList.innerHTML = `<li class="doc-item error-message">Error loading documents: ${err.message}</li>`;
    }
}

window.deleteDocument = async function(docId) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/documents/${docId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Failed to delete document');
        
        loadDocuments();
    } catch (err) {
        alert(err.message);
    }
}

// Start
init();
