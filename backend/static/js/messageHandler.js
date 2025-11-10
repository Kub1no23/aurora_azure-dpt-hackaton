export class MessageHandler {
    constructor(messagesEl) {
        this.messagesEl = messagesEl;
    }

    addMessage(text, cls, source) {
        const el = document.createElement('div');
        el.className = 'msg ' + cls;
        el.textContent = text;
        this.messagesEl.appendChild(el);
        if (source) {
            const s = document.createElement('div');
            s.className = 'source';
            s.textContent = source;
            this.messagesEl.appendChild(s);
        }
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    removeLoadingMessage() {
        const lastBots = this.messagesEl.querySelectorAll('.msg.bot');
        if (lastBots.length) {
            const last = lastBots[lastBots.length - 1];
            if (last && last.textContent.includes('⏳')) {
                last.remove();
                const possibleSource = this.messagesEl.querySelector('.source');
                if (possibleSource && possibleSource.previousSibling === last) {
                    possibleSource.remove();
                }
            }
        }
    }
}

export async function sendChatMessage(text, messageHandler) {
    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const j = await resp.json();

        messageHandler.removeLoadingMessage();

        if (j.answer) {
            messageHandler.addMessage(j.answer, 'bot', `source: ${j.source || 'unknown'}`);
        } else if (j.error) {
            messageHandler.addMessage('Chyba: ' + j.error, 'bot');
        } else {
            messageHandler.addMessage('Žádná odpověď.', 'bot');
        }
    } catch (e) {
        messageHandler.addMessage('Chyba komunikace se serverem: ' + (e.message || e), 'bot');
    }
}