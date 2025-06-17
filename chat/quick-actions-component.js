/**
 * Quick Actions Web Component
 * 
 * A self-contained component that displays quick action buttons.
 * No external CSS dependencies, no width issues, no z-index conflicts.
 * 
 * Usage:
 *   <quick-actions></quick-actions>
 * 
 * API:
 *   - Property: actions (array of {id, text, fullTitle})
 *   - Event: action-click (detail: {actionId})
 */
class QuickActionsComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._actions = [];
  }

  connectedCallback() {
    this.render();
  }

  // Public API
  set actions(value) {
    this._actions = value || [];
    this.render();
  }

  get actions() {
    return this._actions;
  }

  render() {
    const hasActions = this._actions.length > 0;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: ${hasActions ? 'block' : 'none'};
          width: 100%;
          box-sizing: border-box;
        }
        
        .container {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: #f7f8fa;
          border-top: 1px solid #e2e8f0;
          max-height: 100px;
          overflow-y: auto;
          align-content: flex-start;
          
          /* Hide scrollbar but keep functionality */
          scrollbar-width: none;
          -ms-overflow-style: none;
        }
        
        .container::-webkit-scrollbar {
          display: none;
        }
        
        .action-btn {
          flex: 0 1 auto;
          padding: 0.4rem 1rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 9999px;
          font-size: 0.875rem;
          font-weight: 500;
          color: #1e293b;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
          font-family: inherit;
        }
        
        .action-btn:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
          transform: translateY(-1px);
        }
        
        .action-btn:active {
          transform: translateY(0);
        }
        
        /* Mobile adjustments */
        @media (max-width: 768px) {
          .container {
            padding: 0.5rem 1rem;
            max-height: 80px;
          }
          
          .action-btn {
            font-size: 0.8125rem;
            padding: 0.35rem 0.875rem;
          }
        }
        
        /* Empty state */
        .empty {
          display: none;
        }
      </style>
      
      <div class="container">
        ${hasActions ? this._actions.map(action => `
          <button 
            class="action-btn" 
            data-action="${action.id}"
            title="${action.fullTitle || action.text}"
          >
            ${action.text}
          </button>
        `).join('') : '<div class="empty"></div>'}
      </div>
    `;
    
    // Event delegation for clicks
    this.shadowRoot.querySelector('.container').addEventListener('click', this.handleClick.bind(this));
  }

  handleClick(event) {
    const button = event.target.closest('.action-btn');
    if (!button) return;
    
    const actionId = button.dataset.action;
    const action = this._actions.find(a => a.id === actionId);
    
    if (action) {
      // Dispatch custom event that parent can listen to
      this.dispatchEvent(new CustomEvent('action-click', {
        detail: { 
          actionId: action.id,
          action: action 
        },
        bubbles: true,
        composed: true // Allow event to cross shadow DOM boundary
      }));
    }
  }

  // Lifecycle cleanup
  disconnectedCallback() {
    // Remove event listeners if needed
  }
}

// Register the component
customElements.define('quick-actions', QuickActionsComponent);

// Example usage:
/*
const quickActions = document.querySelector('quick-actions');

// Set actions
quickActions.actions = [
  { id: 'getting-started', text: 'Getting Started', fullTitle: 'Introduction > Getting Started' },
  { id: 'features', text: 'Features', fullTitle: 'Introduction > Features' }
];

// Listen for clicks
quickActions.addEventListener('action-click', (e) => {
  console.log('Action clicked:', e.detail.actionId);
  // Handle navigation
});
*/