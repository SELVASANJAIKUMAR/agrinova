(function () {
    const toggle = document.getElementById('chat-toggle');
    const panel = document.getElementById('chat-panel');
    const closeBtn = document.getElementById('chat-close');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const messages = document.getElementById('chat-messages');

    if (!toggle || !panel) return;

    let history = [];

    toggle.addEventListener('click', () => panel.classList.toggle('d-none'));
    if (closeBtn) closeBtn.addEventListener('click', () => panel.classList.add('d-none'));

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function renderSafeMarkdown(text) {
        if (!text) return '';
        let escaped = escapeHtml(text);
        escaped = escaped.replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1">$1</h6>');
        escaped = escaped.replace(/^## (.*$)/gim, '<h5 class="fw-bold mt-2 mb-1">$1</h5>');
        escaped = escaped.replace(/^# (.*$)/gim, '<h4 class="fw-bold mt-2 mb-1">$1</h4>');
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/^\s*[-*]\s+(.*$)/gim, '<li class="ms-3">$1</li>');
        escaped = escaped.replace(/\n/g, '<br>');
        return escaped;
    }

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = 'chat-msg ' + type;
        if (type === 'bot') {
            div.innerHTML = renderSafeMarkdown(text);
        } else {
            div.textContent = text;
        }
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }


    function getCsrfToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';
        history.push({ role: 'user', content: text });

        sendBtn.disabled = true;
        try {
            const resp = await fetch('/chatbot/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ message: text, history: history }),
            });
            const data = await resp.json();
            if (resp.ok) {
                addMessage(data.response, 'bot');
                history.push({ role: 'assistant', content: data.response });
            } else {
                addMessage(data.error || 'Something went wrong.', 'error');
            }
        } catch (e) {
            addMessage('Network error. Please try again.', 'error');
        }
        sendBtn.disabled = false;
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (input) input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
})();
