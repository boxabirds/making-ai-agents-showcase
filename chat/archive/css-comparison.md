# CSS Architecture Comparison

## Current Tangled CSS Issues

### 1. Quick Actions CSS Spread Across Multiple Locations

```css
/* Line 213 - Base styles */
.quick-actions {
    padding: 0.75rem 1rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    max-height: 100px;
    overflow-y: auto;
    scrollbar-width: none;
    align-content: flex-start;
    width: 100%;
    box-sizing: border-box;
}

/* Line 966 - Conflicting mobile rule (deleted) */
body:has(.detail-panel.active) .quick-actions {
    display: none;
}

/* Line 993 - Mobile overrides */
.quick-actions {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    max-height: 80px;
}
```

### 2. Z-Index Chaos

```css
/* Multiple competing z-index values */
.sidebar { z-index: 100; }
.mobile-header { z-index: 1000; }
.detail-panel { z-index: 95; }
.mobile-overlay { z-index: 90; }
.tray-input-container { z-index: 95; }
/* And many conditional z-index changes */
```

### 3. Complex Visibility Rules

```css
/* Multiple ways to hide/show elements */
body:has(.detail-panel.active) .chat-container .input-container {
    opacity: 0;
    pointer-events: none;
}

.detail-panel {
    opacity: 0;
    pointer-events: none;
}

.detail-panel.active {
    opacity: 1;
    pointer-events: auto;
}

/* Transform-based visibility */
.detail-panel {
    transform: translateY(100%);
}
```

### 4. Responsive Design Duplication

```css
/* Desktop chat container */
.chat-container {
    width: var(--chat-width);
    flex: 0 0 var(--chat-width);
    min-width: 375px;
    max-width: var(--chat-width);
}

/* Mobile override */
@media (max-width: 768px) {
    .chat-container {
        width: 100%;
        flex: 1 1 auto;
        max-width: 100%;
        min-width: 100%;
    }
}
```

## Proposed Clean Architecture

### 1. Component-Scoped Styles (Web Components)

```javascript
// Each component manages its own styles
class QuickActions extends HTMLElement {
  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
        }
        
        .container {
          /* All styles self-contained */
          /* No external dependencies */
          /* No specificity battles */
        }
      </style>
    `;
  }
}
```

### 2. Clear Z-Index Hierarchy

```css
/* Global z-index scale */
:root {
  --z-base: 1;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-fixed: 30;
  --z-overlay: 40;
  --z-modal: 50;
  --z-notification: 60;
}
```

### 3. Single Visibility Pattern

```javascript
// State-driven visibility
class Component {
  set visible(value) {
    this.style.display = value ? 'block' : 'none';
    this.setAttribute('aria-hidden', !value);
  }
}
```

### 4. Container Queries Instead of Media Queries

```css
/* Component responds to its container, not viewport */
.quick-actions {
  container-type: inline-size;
}

@container (max-width: 400px) {
  .action-btn {
    font-size: 0.875rem;
  }
}
```

## Benefits of Clean Architecture

1. **No Cascade Conflicts**: Shadow DOM isolates styles
2. **Predictable Behavior**: Components control their own layout
3. **Easy to Debug**: Styles are colocated with components
4. **True Responsive**: Components adapt to their container
5. **No Specificity Wars**: No need for `!important` or complex selectors

## Migration Strategy

### Phase 1: Immediate Fixes
```css
/* Remove all body:has() selectors */
/* Consolidate z-index values */
/* Remove duplicate responsive rules */
```

### Phase 2: Component Extraction
```javascript
// Start with leaf components
import './quick-actions-component.js';
// Replace <div class="quick-actions"> with <quick-actions>
```

### Phase 3: Full Architecture
```javascript
// Complete component tree
<chat-app>
  <chat-layout>
    <chat-sidebar slot="sidebar"></chat-sidebar>
    <chat-main slot="main">
      <chat-messages></chat-messages>
      <quick-actions></quick-actions>
      <chat-input></chat-input>
    </chat-main>
    <document-viewer slot="viewer"></document-viewer>
  </chat-layout>
</chat-app>
```

## Conclusion

The current CSS architecture has grown organically with patches and fixes, leading to:
- Unpredictable cascade effects
- Layout conflicts between mobile and desktop
- Visibility state confusion
- Width/positioning issues

A component-based architecture would provide:
- Clear boundaries and interfaces
- Predictable, isolated behavior
- Easier maintenance and debugging
- True responsive design without conflicts