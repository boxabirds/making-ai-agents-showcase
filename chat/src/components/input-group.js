/**
 * Input Group Component
 * Combines quick actions and chat input
 * No shadow DOM, just clean component architecture
 */
import { BaseComponent, bem } from './base-component.js';
import { state } from '../state-manager.js';
import { escapeHtml, safeHtml } from '../utils/dom-helpers.js';

export class InputGroup extends BaseComponent {
  initialize() {
    this.state = {
      quickActions: [],
      placeholder: 'Ask about the document...',
      value: '',
      disabled: false
    };
    
    super.initialize();
  }
  
  render() {
    const hasActions = this.state.quickActions.length > 0;
    
    this.element.innerHTML = `
      <div class="${bem('input-group')}">
        ${hasActions ? this.renderQuickActions() : ''}
        ${this.renderChatInput()}
      </div>
    `;
  }
  
  renderQuickActions() {
    const actions = this.state.quickActions.map(action => `
      <button 
        class="${bem('input-group', 'action-btn')}"
        data-action-id="${escapeHtml(action.id)}"
        title="${escapeHtml(action.fullTitle || action.text)}"
        ${this.state.disabled ? 'disabled' : ''}
      >
        ${escapeHtml(action.text)}
      </button>
    `).join('');
    
    return `
      <div class="${bem('input-group', 'quick-actions')}" role="group" aria-label="Quick actions">
        ${actions}
      </div>
    `;
  }
  
  renderChatInput() {
    return `
      <div class="${bem('input-group', 'chat-container')}">
        <form class="${bem('input-group', 'form')}">
          <input 
            type="text"
            class="${bem('input-group', 'input')}"
            placeholder="${escapeHtml(this.state.placeholder)}"
            value="${escapeHtml(this.state.value)}"
            ${this.state.disabled ? 'disabled' : ''}
            aria-label="Chat input"
          >
          <button 
            type="submit"
            class="${bem('input-group', 'send-btn')}"
            ${this.state.disabled ? 'disabled' : ''}
            aria-label="Send message"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
            </svg>
          </button>
        </form>
      </div>
    `;
  }
  
  attachEvents() {
    // Quick action clicks
    this.on('.input-group__action-btn', 'click', this.handleActionClick);
    
    // Form submission
    this.on('.input-group__form', 'submit', this.handleSubmit);
    
    // Input changes
    this.on('.input-group__input', 'input', this.handleInputChange);
    
    // Enter key
    this.on('.input-group__input', 'keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit(e);
      }
    });
  }
  
  subscribeToState() {
    // Watch for processing state
    this.watchState('isProcessing', (isProcessing) => {
      this.setDisabled(isProcessing);
    });
    
    // Watch for current section changes to update quick actions
    this.watchState('currentSection', () => {
      this.updateQuickActions();
    });
  }
  
  handleActionClick(e) {
    e.preventDefault();
    
    if (this.state.disabled) return;
    
    const actionId = e.currentTarget.dataset.actionId;
    const action = this.state.quickActions.find(a => a.id === actionId);
    
    if (action) {
      this.element.dispatchEvent(new CustomEvent('action-click', {
        detail: { actionId, action },
        bubbles: true
      }));
    }
  }
  
  handleSubmit(e) {
    e.preventDefault();
    
    if (this.state.disabled) return;
    
    const input = this.$('.input-group__input');
    const message = input.value.trim();
    
    if (message) {
      this.element.dispatchEvent(new CustomEvent('message-submit', {
        detail: { message },
        bubbles: true
      }));
      
      // Clear input
      input.value = '';
      this.state.value = '';
    }
  }
  
  handleInputChange(e) {
    this.state.value = e.target.value;
  }
  
  updateQuickActions() {
    const sections = state.get('sections');
    const currentSectionId = state.get('currentSection');
    
    if (!sections || !currentSectionId) {
      this.setQuickActions([]);
      return;
    }
    
    const currentSection = sections.find(s => s.id === currentSectionId);
    if (currentSection && currentSection.subsections) {
      this.setQuickActions(currentSection.subsections);
    } else {
      this.setQuickActions([]);
    }
  }
  
  // Public API
  setQuickActions(actions) {
    this.setState({ quickActions: actions });
  }
  
  setPlaceholder(placeholder) {
    this.setState({ placeholder });
  }
  
  setDisabled(disabled) {
    this.setState({ disabled });
  }
  
  getValue() {
    return this.state.value;
  }
  
  setValue(value) {
    this.setState({ value });
    const input = this.$('.input-group__input');
    if (input) input.value = value;
  }
  
  focus() {
    const input = this.$('.input-group__input');
    if (input) input.focus();
  }
  
  clear() {
    this.setValue('');
  }
}