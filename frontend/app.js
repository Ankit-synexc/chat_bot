// ── Config ──────────────────────────────────────────────
const API_BASE_URL = 'https://chat-bot-ados.onrender.com';

// ── DOM refs ─────────────────────────────────────────────
const chatArea          = document.getElementById('chat-area');
const welcomeScreen     = document.getElementById('welcome-screen');
const messagesContainer = document.getElementById('messages-container');
const chatForm          = document.getElementById('chat-form');
const chatInput         = document.getElementById('chat-input');
const sendBtn           = document.getElementById('send-btn');
const newChatBtn        = document.getElementById('new-chat-btn');

// ── State ─────────────────────────────────────────────────
let isStreaming = false;

// ── Textarea: auto-resize + enable send button ────────────
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 130) + 'px';
    sendBtn.disabled = chatInput.value.trim().length === 0 || isStreaming;
});

// Enter = submit, Shift+Enter = newline
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) chatForm.dispatchEvent(new Event('submit'));
    }
});

// ── Suggestion chips ──────────────────────────────────────
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        chatInput.value = chip.dataset.question;
        chatInput.dispatchEvent(new Event('input')); // trigger resize + enable btn
        chatForm.dispatchEvent(new Event('submit'));
    });
});

// ── New Chat button ───────────────────────────────────────
newChatBtn.addEventListener('click', () => {
    if (isStreaming) return;
    messagesContainer.innerHTML = '';
    welcomeScreen.style.display = 'flex';
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;
    chatInput.focus();
});

// ── Message rendering ─────────────────────────────────────
function hideWelcome() {
    welcomeScreen.style.display = 'none';
}

function createMessageEl(role) {
    hideWelcome();

    const wrap   = document.createElement('div');
    wrap.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    messagesContainer.appendChild(wrap);
    chatArea.scrollTop = chatArea.scrollHeight;

    return bubble;
}

function showTyping() {
    const bubble = createMessageEl('bot');
    bubble.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>`;
    return bubble;
}

// ── Submit handler ────────────────────────────────────────
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query || isStreaming) return;

    // Lock UI
    isStreaming    = true;
    sendBtn.disabled = true;
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show user message
    const userBubble = createMessageEl('user');
    userBubble.textContent = query;

    // Show typing indicator
    const botBubble = showTyping();

    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/query/ask/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // No Authorization header, no session_id — anonymous request
            body: JSON.stringify({ question: query, top_k: 5, stream: true })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error (${res.status})`);
        }

        // Clear typing indicator; start streaming
        botBubble.innerHTML = '';
        let fullResponse = '';

        const reader  = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';                // ← fix: proper SSE line buffer

        outer: while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process all complete lines in the buffer
            let newlineIdx;
            while ((newlineIdx = buffer.indexOf('\n')) !== -1) {
                const line = buffer.slice(0, newlineIdx).trimEnd();
                buffer     = buffer.slice(newlineIdx + 1);

                if (!line.startsWith('data: ')) continue;
                const raw = line.slice(6).trim();
                if (raw === '[DONE]') break outer;

                try {
                    const parsed = JSON.parse(raw);

                    // ← fix: read 'delta', not 'token'
                    if (typeof parsed.delta === 'string' && parsed.delta) {
                        fullResponse += parsed.delta;
                        botBubble.innerHTML = marked.parse(fullResponse);
                        chatArea.scrollTop  = chatArea.scrollHeight;
                    }

                    if (parsed.done === true) break outer;
                } catch (_) {
                    // Partial JSON — wait for more data
                }
            }
        }

        // Final render pass
        if (fullResponse.trim()) {
            botBubble.innerHTML = marked.parse(fullResponse);
        } else if (!botBubble.textContent.trim()) {
            botBubble.innerHTML = '<em style="color:var(--text-muted)">No response received.</em>';
        }

    } catch (err) {
        console.error('Chat error:', err);
        botBubble.innerHTML = `<span style="color:#f87171">Error: ${err.message}</span>`;
    } finally {
        isStreaming = false;
        sendBtn.disabled = chatInput.value.trim().length === 0;
        chatArea.scrollTop = chatArea.scrollHeight;
        chatInput.focus();
    }
});

// ── Focus on load ─────────────────────────────────────────
chatInput.focus();
