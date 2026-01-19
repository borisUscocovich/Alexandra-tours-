class OnboardingFlow extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.currentStep = 0;
        this.steps = [
            { title: "Bienvenido", text: "Descubre la historia oculta de este lugar." },
            { title: "IA Contextual", text: "Tu camarero personal que conoce tus gustos." },
            { title: "Sin App", text: "Todo sucede aquí, sin descargar nada." }
        ];
    }

    connectedCallback() {
        this.render();
        this.setupEvents();
    }

    setupEvents() {
        const btn = this.shadowRoot.getElementById('nextBtn');
        btn.addEventListener('click', () => {
            this.currentStep++;
            if (this.currentStep < this.steps.length) {
                this.updateSlide();
            } else {
                this.dispatchEvent(new CustomEvent('onboarding-complete', {
                    bubbles: true,
                    composed: true
                }));
            }
        });
    }

    updateSlide() {
        const data = this.steps[this.currentStep];
        this.shadowRoot.getElementById('title').textContent = data.title;
        this.shadowRoot.getElementById('text').textContent = data.text;
        this.shadowRoot.getElementById('btnText').textContent =
            this.currentStep === this.steps.length - 1 ? "Comenzar" : "Siguiente";

        // Simple indicators
        const dots = this.shadowRoot.querySelectorAll('.dot');
        dots.forEach((d, i) => {
            d.style.opacity = i === this.currentStep ? '1' : '0.3';
        });
    }

    render() {
        this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: flex;
          flex-direction: column;
          height: 100%;
          justify-content: center;
          align-items: center;
          padding: 2rem;
          text-align: center;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        h1 { font-size: 2rem; margin-bottom: 1rem; color: #ff6b6b; }
        p { font-size: 1.1rem; margin-bottom: 3rem; opacity: 0.9; }
        button {
          background: #ff6b6b;
          color: white;
          border: none;
          padding: 1rem 2rem;
          border-radius: 50px;
          font-size: 1rem;
          cursor: pointer;
          transition: transform 0.2s;
        }
        button:active { transform: scale(0.95); }
        .indicators {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 2rem;
        }
        .dot {
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
          transition: opacity 0.3s;
        }
      </style>
      <div class="indicators">
        <div class="dot" style="opacity: 1"></div>
        <div class="dot" style="opacity: 0.3"></div>
        <div class="dot" style="opacity: 0.3"></div>
      </div>
      <h1 id="title">${this.steps[0].title}</h1>
      <p id="text">${this.steps[0].text}</p>
      <button id="nextBtn"><span id="btnText">Siguiente</span></button>
    `;
    }
}

customElements.define('onboarding-flow', OnboardingFlow);
