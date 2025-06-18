/**
 * Input Group Component
 * 
 * Combines quick actions and chat input into a single cohesive component.
 * They always move and behave together.
 * 
 * Usage:
 *   <input-group></input-group>
 * 
 * API:
 *   - Property: quickActions (array)
 *   - Property: placeholder (string)
 *   - Property: disabled (boolean)
 *   - Event: message-submit (detail: {message})
 *   - Event: action-click (detail: {actionId})
 */
class InputGroupComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Internal state
    this._quickActions = [];
    this._placeholder = 'Ask about tech agents...';
    this._disabled = false;
  }

  connectedCallback() {
    this.render();
    this.attachEventListeners();
  }

  // Public API
  set quickActions(actions) {
    this._quickActions = actions || [];
    this.updateQuickActions();
  }

  get quickActions() {
    return this._quickActions;
  }

  set placeholder(value) {
    this._placeholder = value;
    const input = this.shadowRoot.querySelector('.chat-input');
    if (input) input.placeholder = value;
  }

  set disabled(value) {
    this._disabled = value;
    this.updateDisabledState();
  }

  get disabled() {
    return this._disabled;
  }

  get value() {
    const input = this.shadowRoot.querySelector('.chat-input');
    return input ? input.value : '';
  }

  set value(val) {
    const input = this.shadowRoot.querySelector('.chat-input');
    if (input) input.value = val;
  }

  render() {
    const hasActions = this._quickActions.length > 0;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          background: var(--color-surface, #ffffff);
          border-top: 1px solid var(--color-border, #e2e8f0);
        }
        
        /* Quick actions section */
        .quick-actions {
          display: ${hasActions ? 'flex' : 'none'};
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          flex-wrap: wrap;
          max-height: 80px;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 transparent;
        }
        
        .quick-actions::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        
        .quick-actions::-webkit-scrollbar-track {
          background: transparent;
        }
        
        .quick-actions::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }
        
        .action-btn {
          flex: 0 1 auto;
          padding: 0.375rem 1rem;
          background: var(--color-surface, #ffffff);
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 9999px;
          font-size: 0.875rem;
          font-family: inherit;
          color: var(--color-text, #1e293b);
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
        }
        
        .action-btn:hover:not(:disabled) {
          background: var(--color-bg, #f7f8fa);
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .action-btn:active:not(:disabled) {
          transform: translateY(0);
        }
        
        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        /* Chat input section */
        .chat-input-container {
          padding: 1rem;
          ${hasActions ? 'border-top: 1px solid var(--color-border, #e2e8f0);' : ''}
        }
        
        .input-wrapper {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }
        
        .chat-input {
          flex: 1;
          padding: 0.625rem 1.25rem;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 9999px;
          font-size: 1rem; /* This is 16px, which is safe */
          font-family: inherit;
          color: var(--color-text, #1e293b);
          background: var(--color-surface, #ffffff);
          outline: none;
          transition: all 0.2s ease;
        }
        
        .chat-input:focus {
          border-color: var(--color-primary, #3b82f6);
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .chat-input:disabled {
          background: var(--color-bg, #f7f8fa);
          cursor: not-allowed;
        }
        
        .send-btn {
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: var(--color-primary, #3b82f6);
          color: white;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
          font-size: 1.25rem;
        }
        
        .send-btn:hover:not(:disabled) {
          background: var(--color-primary-dark, #2563eb);
          transform: scale(1.05);
        }
        
        .send-btn:active:not(:disabled) {
          transform: scale(0.95);
        }
        
        .send-btn:disabled {
          background: #cbd5e1;
          cursor: not-allowed;
        }
        
        /* Mobile adjustments */
        @media (max-width: 768px) {
          .quick-actions {
            padding: 0.375rem 0.75rem;
            max-height: 60px;
          }
          
          .action-btn {
            font-size: 0.8125rem;
            padding: 0.3125rem 0.875rem;
          }
          
          .chat-input-container {
            padding: 0.75rem;
          }
          
          .chat-input {
            /* THE ONLY CHANGE IS HERE: Changed from 0.9375rem to 1rem */
            font-size: 1rem; 
            padding: 0.5rem 1rem;
          }
        }
        
        /* Focus trap indicator */
        :host(:focus-within) {
          box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
        }
      </style>
      
      <div class="quick-actions" role="group" aria-label="Quick actions">
        ${this._quickActions.map(action => `
          <button 
            class="action-btn" 
            data-action="${action.id}"
            title="${action.fullTitle || action.text}"
            ${this._disabled ? 'disabled' : ''}
          >
            ${action.text}
          </button>
        `).join('')}
      </div>
      
      <div class="chat-input-container">
        <form class="input-wrapper">
          <input 
            type="text" 
            class="chat-input" 
            placeholder="${this._placeholder}"
            ${this._disabled ? 'disabled' : ''}
            aria-label="Chat input"
          >
          <button 
            type="submit" 
            class="send-btn"
            ${this._disabled ? 'disabled' : ''}
            aria-label="Send message"
          >
            →
          </button>
        </form>
      </div>
    `;
  }

  attachEventListeners() {
    // Quick action clicks
    this.shadowRoot.addEventListener('click', (e) => {
      const actionBtn = e.target.closest('.action-btn');
      if (actionBtn && !this._disabled) {
        const actionId = actionBtn.dataset.action;
        const action = this._quickActions.find(a => a.id === actionId);
        
        this.dispatchEvent(new CustomEvent('action-click', {
          detail: { actionId, action },
          bubbles: true,
          composed: true
        }));
      }
    });

    // Form submission
    const form = this.shadowRoot.querySelector('form');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });

    // Enter key handling
    const input = this.shadowRoot.querySelector('.chat-input');
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit();
      }
    });
  }

  handleSubmit() {
    const input = this.shadowRoot.querySelector('.chat-input');
    const message = input.value.trim();
    
    if (message && !this._disabled) {
      this.dispatchEvent(new CustomEvent('message-submit', {
        detail: { message },
        bubbles: true,
        composed: true
      }));
      
      // Clear input after successful submit
      input.value = '';
    }
  }


  // Public methods
  focus() {
    const input = this.shadowRoot.querySelector('.chat-input');
    if (input) input.focus();
  }

  clear() {
    const input = this.shadowRoot.querySelector('.chat-input');
    if (input) input.value = '';
  }

  // Update only the quick actions section without re-rendering the entire component
  updateQuickActions() {
    if (!this.shadowRoot) return;
    
    const quickActionsContainer = this.shadowRoot.querySelector('.quick-actions');
    if (!quickActionsContainer) return;
    
    // Update display style
    const hasActions = this._quickActions.length > 0;
    quickActionsContainer.style.display = hasActions ? 'flex' : 'none';
    
    // Update content
    quickActionsContainer.innerHTML = this._quickActions.map(action => `
      <button 
        class="action-btn" 
        data-action="${action.id}"
        title="${action.fullTitle || action.text}"
        ${this._disabled ? 'disabled' : ''}
      >
        ${action.text}
      </button>
    `).join('');
    
    // Update chat input container border
    const chatInputContainer = this.shadowRoot.querySelector('.chat-input-container');
    if (chatInputContainer) {
      if (hasActions) {
        chatInputContainer.style.borderTop = '1px solid var(--color-border, #e2e8f0)';
      } else {
        chatInputContainer.style.borderTop = '';
      }
    }
  }
  
  // Update disabled state without re-rendering
  updateDisabledState() {
    if (!this.shadowRoot) return;
    
    // Update quick action buttons
    const actionButtons = this.shadowRoot.querySelectorAll('.action-btn');
    actionButtons.forEach(btn => {
      if (this._disabled) {
        btn.setAttribute('disabled', '');
      } else {
        btn.removeAttribute('disabled');
      }
    });
    
    // Update chat input
    const chatInput = this.shadowRoot.querySelector('.chat-input');
    if (chatInput) {
      if (this._disabled) {
        chatInput.setAttribute('disabled', '');
        chatInput.style.background = 'var(--color-bg, #f7f8fa)';
        chatInput.style.cursor = 'not-allowed';
      } else {
        chatInput.removeAttribute('disabled');
        chatInput.style.background = 'var(--color-surface, #ffffff)';
        chatInput.style.cursor = '';
      }
    }
    
    // Update send button
    const sendButton = this.shadowRoot.querySelector('.send-btn');
    if (sendButton) {
      if (this._disabled) {
        sendButton.setAttribute('disabled', '');
        sendButton.style.background = '#cbd5e1';
        sendButton.style.cursor = 'not-allowed';
      } else {
        sendButton.removeAttribute('disabled');
        sendButton.style.background = 'var(--color-primary, #3b82f6)';
        sendButton.style.cursor = 'pointer';
      }
    }
  }
}

// Register the component
customElements.define('input-group', InputGroupComponent);

// Example usage:
/*
const inputGroup = document.querySelector('input-group');

// Set quick actions
inputGroup.quickActions = [
  { id: 'start', text: 'Getting Started' },
  { id: 'api', text: 'API Reference' }
];

// Listen for events
inputGroup.addEventListener('message-submit', (e) => {
  console.log('Message:', e.detail.message);
});

inputGroup.addEventListener('action-click', (e) => {
  console.log('Action:', e.detail.actionId);
});

// Control state
inputGroup.disabled = false;
inputGroup.placeholder = 'Type your question...';
*/