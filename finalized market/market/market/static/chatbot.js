/* ============================================================
   AI CHATBOT JS — right side above WhatsApp
   ============================================================ */
(function () {
    'use strict';

    const PANEL_HTML = `
<button class="ai-chat-btn" id="aiChatBtn" onclick="toggleAIChat()" title="AI Assistant">
    <span class="ai-badge">AI</span>
    <i class="fa-solid fa-robot"></i>
</button>

<div class="ai-chat-panel" id="aiChatPanel">
    <div class="chat-header">
        <div class="chat-header-icon">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="chat-header-info">
            <div class="name">Market AI Assistant</div>
            <div class="status" id="aiStatus">&#9679; Online</div>
        </div>
        <button class="chat-close" onclick="toggleAIChat()">&times;</button>
    </div>

    <div class="chat-messages" id="chatMessages">
        <div class="msg ai">
            Hi! I am your Market AI assistant.<br>
            Ask me about products, prices, or get a <b>price comparison</b> with other shops!
        </div>
    </div>

    <div class="chat-suggestions" id="chatSuggestions">
        <button class="chip" onclick="sendChip('What vegetables are available?')">Vegetables</button>
        <button class="chip" onclick="sendChip('Compare tomato price with other shops')">Price Compare</button>
        <button class="chip" onclick="sendChip('What oils do you sell?')">Oils</button>
        <button class="chip" onclick="sendChip('How do I place an order?')">Order Help</button>
    </div>

    <div class="chat-input-row">
        <input class="chat-input" id="chatInput" type="text"
               placeholder="Ask anything..."
               onkeydown="if(event.key==='Enter') sendMessage()">
        <button class="chat-send" onclick="sendMessage()">
            <i class="fa-solid fa-paper-plane"></i>
        </button>
    </div>
</div>`;

    document.addEventListener('DOMContentLoaded', function () {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = PANEL_HTML;
        document.body.appendChild(wrapper);
    });

    // ── State ──
    let chatOpen    = false;
    let chatHistory = [];
    let isTyping    = false;

    window.toggleAIChat = function () {
        chatOpen = !chatOpen;
        const panel = document.getElementById('aiChatPanel');
        if (panel) panel.classList.toggle('open', chatOpen);
        if (chatOpen) {
            setTimeout(() => {
                const input = document.getElementById('chatInput');
                if (input) input.focus();
            }, 300);
        }
    };

    window.sendChip = function (text) {
        const input = document.getElementById('chatInput');
        if (input) input.value = text;
        sendMessage();
    };

    window.sendMessage = async function () {
        const input    = document.getElementById('chatInput');
        const messages = document.getElementById('chatMessages');
        if (!input || !messages || isTyping) return;

        const text = input.value.trim();
        if (!text) return;
        input.value = '';

        appendMsg(text, 'user');
        chatHistory.push({ role: 'user', text });

        const suggestions = document.getElementById('chatSuggestions');
        if (suggestions) suggestions.style.display = 'none';

        isTyping = true;
        const typingEl = appendMsg('Thinking...', 'ai typing');

        try {
            const res  = await fetch('/api/chat', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ message: text, history: chatHistory })
            });
            const data = await res.json();

            typingEl.remove();
            isTyping = false;

            const reply = data.reply || data.error || 'Sorry, something went wrong.';
            appendMsg(reply, 'ai');
            chatHistory.push({ role: 'ai', text: reply });

            const status = document.getElementById('aiStatus');
            if (status) {
                if (!data.ai_ready) {
                    status.textContent = 'API key needed';
                    status.style.color = '#ff9800';
                } else {
                    status.textContent = '● Online';
                    status.style.color = '';
                }
            }
        } catch (err) {
            typingEl.remove();
            isTyping = false;
            appendMsg('Network error. Please try again.', 'ai');
        }

        messages.scrollTop = messages.scrollHeight;
    };

    function appendMsg(text, className) {
        const messages = document.getElementById('chatMessages');
        if (!messages) return { remove: () => {} };
        const div = document.createElement('div');
        div.className = `msg ${className}`;
        div.innerHTML = text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }
})();
