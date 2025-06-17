# Chat Application Refactoring Proposal

## Overview
The current implementation has become tangled due to overlapping concerns between layout, state management, and responsive design. This proposal outlines a clean architecture using Web Components.

## Proposed Component Architecture

### 1. Core Components

```
<chat-app>
  <chat-sidebar></chat-sidebar>
  <chat-messages></chat-messages>
  <quick-actions></quick-actions>
  <chat-input></chat-input>
  <document-viewer></document-viewer>
</chat-app>
```

### 2. Component Responsibilities

#### `<chat-app>` - Main Container
- Manages global state
- Handles responsive layout orchestration
- Coordinates communication between components
- Single source of truth for visibility states

#### `<chat-sidebar>` - Navigation
- Self-contained navigation logic
- Emits `navigate` events
- Manages its own collapse state on mobile

#### `<chat-messages>` - Message Display
- Handles message rendering and scrolling
- Listens for new messages
- Self-contained typing indicator

#### `<quick-actions>` - Context Actions
- Receives actions from parent
- Handles its own layout (no width issues)
- Clear visibility rules

#### `<document-viewer>` - Document Display
- Manages its own tray/modal behavior
- Handles document rendering
- Keyboard navigation isolated here

### 3. State Management

```javascript
class AppState {
  constructor() {
    this.state = {
      currentSection: null,
      currentSubsection: null,
      documentViewerOpen: false,
      sidebarOpen: false,
      messages: [],
      quickActions: [],
      isMobile: window.innerWidth <= 768
    };
    
    this.listeners = new Set();
  }
  
  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }
  
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }
}
```

### 4. Clean CSS Architecture

```css
/* Global tokens only */
:root {
  --spacing-unit: 0.25rem;
  --color-primary: #3b82f6;
  --breakpoint-mobile: 768px;
  /* etc */
}

/* Each component has isolated styles */
/* No cross-component selectors */
/* No body:has() selectors */
/* Clear z-index hierarchy: base(1), overlay(100), modal(200) */
```

### 5. Example Component Implementation

```javascript
class QuickActions extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }
  
  connectedCallback() {
    this.render();
  }
  
  set actions(value) {
    this._actions = value;
    this.render();
  }
  
  render() {
    const hasActions = this._actions?.length > 0;
    
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: ${hasActions ? 'block' : 'none'};
          width: 100%;
        }
        
        .container {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-unit-2);
          padding: var(--spacing-unit-3);
          background: var(--color-surface);
          border-top: 1px solid var(--color-border);
        }
        
        button {
          flex: 0 1 auto;
          padding: var(--spacing-unit-2) var(--spacing-unit-4);
          /* ... */
        }
      </style>
      
      <div class="container">
        ${this._actions?.map(action => `
          <button data-action="${action.id}">
            ${action.text}
          </button>
        `).join('') || ''}
      </div>
    `;
    
    this.shadowRoot.addEventListener('click', this.handleClick.bind(this));
  }
  
  handleClick(e) {
    const button = e.target.closest('button');
    if (button) {
      this.dispatchEvent(new CustomEvent('action-click', {
        detail: { actionId: button.dataset.action },
        bubbles: true
      }));
    }
  }
}

customElements.define('quick-actions', QuickActions);
```

### 6. Benefits of This Approach

1. **Isolation**: Each component is self-contained
2. **Predictable**: Clear data flow and event handling
3. **Maintainable**: Easy to understand and modify
4. **Testable**: Components can be tested in isolation
5. **Responsive**: Each component handles its own responsive behavior
6. **No CSS Conflicts**: Shadow DOM prevents style leakage

### 7. Migration Path

Phase 1: Extract leaf components
- Start with `<quick-actions>`
- Then `<chat-input>`
- Test thoroughly

Phase 2: Extract container components
- `<chat-messages>`
- `<document-viewer>`

Phase 3: Main app component
- `<chat-app>` orchestration
- Remove all global CSS except tokens

### 8. Immediate Fixes Without Full Refactor

If a full refactor isn't feasible immediately:

1. **Consolidate z-index values**:
   ```css
   --z-sidebar: 10;
   --z-chat: 20;
   --z-quickactions: 30;
   --z-modal: 100;
   --z-overlay: 90;
   ```

2. **Single visibility method**:
   ```javascript
   function setComponentVisibility(component, visible) {
     component.dataset.visible = visible;
     // All visibility logic in one place
   }
   ```

3. **Remove width constraints on mobile**:
   ```css
   @media (max-width: 768px) {
     .chat-container,
     .quick-actions {
       width: 100% !important;
       max-width: 100% !important;
       min-width: 100% !important;
     }
   }
   ```

4. **Centralize responsive checks**:
   ```javascript
   const MediaQuery = {
     isMobile: () => window.innerWidth <= 768,
     listen: (callback) => {
       window.addEventListener('resize', callback);
     }
   };
   ```

## Recommendation

The Web Components approach would solve the current architectural issues and provide a solid foundation for future development. The encapsulation and clear interfaces would prevent the kind of tangled dependencies that have emerged in the current implementation.