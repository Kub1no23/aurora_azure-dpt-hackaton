(function () {
  if (window.__faqBotLoaded) return;
  window.__faqBotLoaded = true;

  function createNode(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.firstElementChild;
  }

  const css = `
  #faq-bot-container { position: fixed; right: 18px; bottom: 18px; z-index: 9999; }
  #faq-toggle-btn {
    background: linear-gradient(90deg, #0655E7, #0078D7);
    color: #fff;
    border: none;
    border-radius: 50px;
    padding: 10px 16px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  #faq-bot {
    font-family: Inter, Roboto, Arial, Helvetica, sans-serif;
    width: 360px;
    border: 1px solid #ddd;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    background: #fff;
    display: none;
    flex-direction: column;
    transition: all 0.3s ease;
    margin-top: 10px;
  }
  #faq-bot.open { display: flex; }
  #faq-bot .header { background: linear-gradient(90deg,#0655E7, #0078D7); padding: 12px; color: #fff; font-weight: 700; }
  #faq-bot .messages { height: 320px; overflow: auto; padding: 12px; background: #f9f9fb; }
  #faq-bot .input { display: flex; border-top: 1px solid #eee; }
  #faq-bot input { flex: 1; border: 0; padding: 12px; outline: none; font-size: 14px; }
  #faq-bot button { border: 0; padding: 0 14px; background: transparent; color: #fff; font-weight: 700; cursor: pointer; background: linear-gradient(90deg,#0655E7,#0078D7); }
  .msg { margin: 8px 0; padding: 10px 12px; border-radius: 10px; max-width: 86%; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
  .msg.user { background: #dfefff; margin-left: auto; }
  .msg.bot { background: #ffffff; margin-right: auto; color: #111; border: 1px solid #eee; }
  .source { font-size: 11px; color: #666; margin-top: 6px; }
  `;
  const style = document.createElement('style');
  style.innerHTML = css;
  document.head.appendChild(style);

  function initBot(container) {
    const toggleBtn = createNode(`<button id="faq-toggle-btn" aria-label="Otevřít FAQ bota">Potřebuješ poradit?</button>`);
    const botHtml = `
      <div id="faq-bot" role="region" aria-label="FAQ bot">
        <div class="header">FAQ Bot — máš otázku?</div>
        <div class="messages" id="faq-messages" aria-live="polite"></div>
        <div class="input">
          <input id="faq-input" placeholder="Co zmínit v přihlášce?" aria-label="Zadej dotaz" />
          <button id="faq-send" aria-label="Odeslat">Pošli</button>
        </div>
      </div>
    `;
    const botEl = createNode(botHtml);

    container.appendChild(toggleBtn);
    container.appendChild(botEl);

    toggleBtn.addEventListener('click', () => {
      botEl.classList.toggle('open');
    });

    const messagesEl = botEl.querySelector('#faq-messages');
    const input = botEl.querySelector('#faq-input');
    const send = botEl.querySelector('#faq-send');

    function addMessage(text, cls, source) {
      const el = document.createElement('div');
      el.className = 'msg ' + cls;
      el.textContent = text;
      messagesEl.appendChild(el);
      if (source) {
        const s = document.createElement('div');
        s.className = 'source';
        s.textContent = source;
        messagesEl.appendChild(s);
      }
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function sendMsg() {
      const text = input.value.trim();
      if (!text) return;
      addMessage(text, 'user');
      input.value = '';
      addMessage('⏳ Přemýšlím...', 'bot');

      try {
        const resp = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const j = await resp.json();

        const lastBots = messagesEl.querySelectorAll('.msg.bot');
        if (lastBots.length) {
          const last = lastBots[lastBots.length - 1];
          if (last && last.textContent.includes('⏳')) {
            last.remove();
            const possibleSource = messagesEl.querySelector('.source');
            if (possibleSource && possibleSource.previousSibling === last) {
              possibleSource.remove();
            }
          }
        }

        if (j.answer) {
          addMessage(j.answer, 'bot', `source: ${j.source || 'unknown'}`);
        } else if (j.error) {
          addMessage('Chyba: ' + j.error, 'bot');
        } else {
          addMessage('Žádná odpověď.', 'bot');
        }
      } catch (e) {
        addMessage('Chyba komunikace se serverem: ' + (e.message || e), 'bot');
      }
    }

    send.addEventListener('click', sendMsg);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMsg(); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const container = document.createElement('div');
    container.id = 'faq-bot-container';
    document.body.appendChild(container);
    initBot(container);
  });
})();