import { MessageHandler, sendChatMessage } from './messageHandler.js';

export function initBot() {
    const botEl = document.getElementById('faq-bot');
    const toggleBtn = document.getElementById('faq-toggle-btn');

    toggleBtn.addEventListener('click', () => {
        botEl.classList.toggle('open');
    });

    const messagesEl = botEl.querySelector('#faq-messages');
    const input = botEl.querySelector('#faq-input');
    const send = botEl.querySelector('#faq-send');
    const messageHandler = new MessageHandler(messagesEl);

    async function sendMsg() {
        const text = input.value.trim();
        if (!text) return;
        messageHandler.addMessage(text, 'user');
        input.value = '';
        messageHandler.addMessage('⏳ Přemýšlím...', 'bot');

        await sendChatMessage(text, messageHandler);
    }

    send.addEventListener('click', sendMsg);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMsg(); });
}