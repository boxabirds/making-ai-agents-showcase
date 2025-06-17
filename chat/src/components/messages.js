/**
 * Messages Component
 * Displays chat messages with user/assistant distinction
 * Handles typing indicators and artifact references
 */
import { BaseComponent, bem } from './base-component.js';
import { state } from '../state-manager.js';
import { escapeHtml, safeHtml } from '../utils/dom-helpers.js';

export class Messages extends BaseComponent {
  initialize() {
    this.state = {
      messages: [],
      isTyping: false,
      autoScroll: true
    };
    
    super.initialize();
  }
  
  render() {
    this.element.innerHTML = `
      <div class="${bem('messages')}">
        <div class="${bem('messages', 'container')}" role="log" aria-live="polite" aria-label="Chat messages">
          ${this.renderMessages()}
          ${this.renderTypingIndicator()}
        </div>
      </div>
    `;
    
    // Auto-scroll to bottom if enabled
    if (this.state.autoScroll) {
      this.scrollToBottom();
    }
    
    // Highlight any code blocks after render
    setTimeout(() => this.highlightCodeBlocks(), 0);
  }
  
  renderMessages() {
    if (this.state.messages.length === 0) {
      return `
        <div class="${bem('messages', 'empty')}">
          <p>No messages yet. Start a conversation!</p>
        </div>
      `;
    }
    
    return this.state.messages.map((message, index) => 
      this.renderMessage(message, index)
    ).join('');
  }
  
  renderMessage(message, index) {
    const isUser = message.type === 'user';
    const messageClass = bem('messages', 'message', isUser ? 'user' : 'assistant');
    const timeStr = this.formatTime(message.timestamp);
    
    return `
      <div class="${messageClass}" data-message-id="${message.id || index}">
        <div class="${bem('messages', 'avatar')}">
          ${isUser ? this.renderUserAvatar() : this.renderAssistantAvatar()}
        </div>
        <div class="${bem('messages', 'content')}">
          <div class="${bem('messages', 'header')}">
            <span class="${bem('messages', 'author')}">${isUser ? 'You' : 'Assistant'}</span>
            <time class="${bem('messages', 'time')}" datetime="${new Date(message.timestamp).toISOString()}">
              ${timeStr}
            </time>
          </div>
          <div class="${bem('messages', 'body')}">
            ${this.renderMessageContent(message)}
          </div>
          ${message.artifacts ? this.renderArtifacts(message.artifacts) : ''}
        </div>
      </div>
    `;
  }
  
  renderMessageContent(message) {
    // Handle different content types
    if (message.html) {
      return safeHtml(message.html);
    }
    
    if (message.markdown) {
      return this.renderMarkdown(message.markdown);
    }
    
    // Plain text
    return `<p>${escapeHtml(message.text)}</p>`;
  }
  
  renderMarkdown(markdown) {
    if (typeof marked === 'undefined') {
      // Fallback to basic markdown rendering
      return `<p>${escapeHtml(markdown)}</p>`;
    }
    
    try {
      marked.setOptions({
        breaks: true,
        gfm: true,
        highlight: (code, lang) => {
          if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
            try {
              return hljs.highlight(code, { language: lang }).value;
            } catch (e) {
              console.warn('Highlight error:', e);
            }
          }
          return code;
        }
      });
      
      const html = marked.parse(markdown);
      
      // After rendering, highlight any code blocks that weren't highlighted by marked
      setTimeout(() => this.highlightCodeBlocks(), 0);
      
      return html;
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return `<p>${escapeHtml(markdown)}</p>`;
    }
  }
  
  /**
   * Highlight code blocks using highlight.js
   * This handles cases where marked doesn't catch all code blocks
   */
  highlightCodeBlocks() {
    if (typeof hljs === 'undefined') return;
    
    // Find all code blocks in the messages container
    const codeBlocks = this.element.querySelectorAll('pre code:not(.hljs)');
    codeBlocks.forEach(block => {
      try {
        hljs.highlightElement(block);
      } catch (e) {
        console.warn('Failed to highlight code block:', e);
      }
    });
  }
  
  renderArtifacts(artifacts) {
    const items = artifacts.map(artifact => `
      <button 
        class="${bem('messages', 'artifact')}"
        data-artifact-id="${escapeHtml(artifact.id)}"
        title="Click to view ${escapeHtml(artifact.title)}"
      >
        <svg class="${bem('messages', 'artifact-icon')}" viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M9 3v6h6V3h5a2 2 0 012 2v14a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5zm3 0v4h4V3h-4z"/>
        </svg>
        <span>${escapeHtml(artifact.title)}</span>
      </button>
    `).join('');
    
    return `
      <div class="${bem('messages', 'artifacts')}">
        ${items}
      </div>
    `;
  }
  
  renderTypingIndicator() {
    if (!this.state.isTyping) return '';
    
    return `
      <div class="${bem('messages', 'typing')}">
        <div class="${bem('messages', 'avatar')}">
          ${this.renderAssistantAvatar()}
        </div>
        <div class="${bem('messages', 'typing-dots')}">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;
  }
  
  renderUserAvatar() {
    return `
      <svg viewBox="0 0 24 24" width="24" height="24">
        <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
      </svg>
    `;
  }
  
  renderAssistantAvatar() {
    return `
      <svg viewBox="0 0 24 24" width="24" height="24">
        <path fill="currentColor" d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7h1a1 1 0 011 1v3a1 1 0 01-1 1h-1v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1H2a1 1 0 01-1-1v-3a1 1 0 011-1h1a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2M7.5 13A2.5 2.5 0 005 15.5 2.5 2.5 0 007.5 18a2.5 2.5 0 002.5-2.5A2.5 2.5 0 007.5 13m9 0a2.5 2.5 0 00-2.5 2.5 2.5 2.5 0 002.5 2.5 2.5 2.5 0 002.5-2.5 2.5 2.5 0 00-2.5-2.5z"/>
      </svg>
    `;
  }
  
  attachEvents() {
    // Handle artifact clicks
    this.on('.messages__artifact', 'click', this.handleArtifactClick);
    
    // Handle scroll for auto-scroll detection
    const container = this.$('.messages__container');
    if (container) {
      container.addEventListener('scroll', this.handleScroll.bind(this));
    }
  }
  
  subscribeToState() {
    // Watch for new messages
    this.watchState('messages', (messages) => {
      this.setState({ messages });
    });
    
    // Watch for typing indicator
    this.watchState('isProcessing', (isProcessing) => {
      this.setState({ isTyping: isProcessing });
    });
  }
  
  handleArtifactClick(e) {
    e.preventDefault();
    const artifactId = e.currentTarget.dataset.artifactId;
    
    this.element.dispatchEvent(new CustomEvent('artifact-click', {
      detail: { artifactId },
      bubbles: true
    }));
  }
  
  handleScroll(e) {
    const container = e.target;
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
    
    // Update auto-scroll state
    this.state.autoScroll = isAtBottom;
  }
  
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    // Format as date if older than 24 hours
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }
  
  scrollToBottom() {
    const container = this.$('.messages__container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
  
  // Public API
  addMessage(message) {
    const messages = [...this.state.messages, {
      ...message,
      timestamp: message.timestamp || Date.now(),
      id: message.id || `msg-${Date.now()}`
    }];
    
    this.setState({ messages });
    
    // Update global state
    state.set({ messages });
  }
  
  updateMessage(messageId, updates) {
    const messages = this.state.messages.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    );
    
    this.setState({ messages });
    state.set({ messages });
  }
  
  removeMessage(messageId) {
    const messages = this.state.messages.filter(msg => msg.id !== messageId);
    this.setState({ messages });
    state.set({ messages });
  }
  
  clearMessages() {
    this.setState({ messages: [] });
    state.set({ messages: [] });
  }
  
  setTyping(isTyping) {
    this.setState({ isTyping });
  }
}

// Export singleton instance
export const messages = new Messages(document.createElement('div'));