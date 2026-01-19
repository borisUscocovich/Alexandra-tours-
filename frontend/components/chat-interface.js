class ChatInterface extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.localId = "el_tigre_gracia"; // Default for MVP Phase 1
  }

  connectedCallback() {
    this.render();
    this.messagesContainer = this.shadowRoot.getElementById('messages');
    this.input = this.shadowRoot.getElementById('chatInput');
    this.sendBtn = this.shadowRoot.getElementById('sendBtn');

    this.setupEvents();
    // Initial welcome
    this.addMessage("Hola, soy tu camarero virtual. ¿En qué puedo ayudarte?", 'bot');
  }

  setupEvents() {
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  async sendMessage() {
    const rawText = this.input.value.trim();
    if (!rawText) return;

    // Security: Basic Client-side sanitization
    const safeText = this.escapeHtml(rawText);

    // UI Update
    this.addMessage(safeText, 'user');
    this.input.value = '';
    this.input.disabled = true;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          local_id: this.localId,
          message: rawText // Pydantic on backend will strictly validate/sanitize this too
        })
      });

      if (!response.ok) throw new Error('Network error');

      const data = await response.json();
      this.addMessage(data.response, 'bot');

      // Audio Feature (Lola speaks)
      this.playAudio(data.response);

    } catch (err) {
      console.error(err);
      this.addMessage("Lo siento, hubo un error conectando con el servicio.", 'bot error');
    } finally {
      this.input.disabled = false;
      this.input.focus();
    }
  }

  async playAudio(text) {
    // Only play if text is reasonable length to avoid huge costs/latency
    if (text.length > 200) return;

    try {
      const response = await fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
      }
    } catch (e) {
      console.warn("Audio playback failed:", e);
    }
  }

  addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.innerHTML = text; // Previously sanitized if user, or from trusted bot
    this.messagesContainer.appendChild(msgDiv);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: rgba(22, 33, 62, 0.9);
        }
        #messages {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .message {
          max-width: 80%;
          padding: 0.8rem 1rem;
          border-radius: 12px;
          line-height: 1.4;
          animation: fadein 0.3s;
        }
        .bot {
          align-self: flex-start;
          background: #2c3e50;
          color: #ecf0f1;
        }
        .user {
          align-self: flex-end;
          background: #ff6b6b;
          color: white;
        }
        .error {
          border: 1px solid red;
        }
        .input-area {
          padding: 1rem;
          background: #1a1a2e;
          display: flex;
          gap: 0.5rem;
        }
        input {
          flex: 1;
          background: #0f1523;
          border: 1px solid #2c3e50;
          color: white;
          padding: 0.8rem;
          border-radius: 25px;
          outline: none;
        }
        button {
          background: #4ecdc4;
          border: none;
          width: 44px;
          height: 44px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s;
        }
        button:active { transform: scale(0.9); }
        .mic-active { background: #ff6b6b; animation: pulse 1.5s infinite; }
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.4); }
          70% { box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }
          100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
        }
        @keyframes fadein {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      </style>
      <div id="messages"></div>
      <div class="input-area">
        <button id="micBtn">🎤</button>
        <input type="text" id="chatInput" placeholder="Escribe o habla..." autocomplete="off">
        <button id="sendBtn">➤</button>
      </div>
    `;
  }

  setupEvents() {
    super.setupEvents(); // Call existing setup if any (removed super call if not extending custom class logic properly)
    // Re-bind basic events
    this.sendBtn = this.shadowRoot.getElementById('sendBtn');
    this.input = this.shadowRoot.getElementById('chatInput');
    this.micBtn = this.shadowRoot.getElementById('micBtn');

    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    // Voice Input Setup
    this.micBtn.addEventListener('click', () => this.toggleVoiceInput());

    // Auto-Welcome Audio (Once user interaction allows)
    // We listen for the first click anywhere to enable audio context usually
    this.hasWelcomed = false;
    document.body.addEventListener('click', () => {
      if (!this.hasWelcomed) {
        this.hasWelcomed = true;
        // Re-play the initial welcome message in audio
        const welcomeText = "Hola, soy tu camarero virtual. ¿En qué puedo ayudarte?";
        this.playAudio(welcomeText);
      }
    }, { once: true });
  }

  toggleVoiceInput() {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Tu navegador no soporta entrada de voz (prueba Chrome/Android).");
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
      return;
    }

    this.isListening = true;
    this.micBtn.classList.add('mic-active');

    this.recognition = new webkitSpeechRecognition();
    this.recognition.lang = 'es-ES';
    this.recognition.interimResults = false;
    this.recognition.maxAlternatives = 1;

    this.recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      this.input.value = text;
      this.sendMessage(); // Auto-send
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.micBtn.classList.remove('mic-active');
    };

    this.recognition.onerror = (e) => {
      console.error("Speech error", e);
      this.isListening = false;
      this.micBtn.classList.remove('mic-active');
    };

    this.recognition.start();
  }
}

customElements.define('chat-interface', ChatInterface);
