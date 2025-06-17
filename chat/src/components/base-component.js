/**
 * Base Component Class
 * Foundation for all UI components with common functionality
 */
import { state } from '../state-manager.js';
import { $, $$, classes, delegate } from '../utils/dom-helpers.js';

export class BaseComponent {
  constructor(element, options = {}) {
    this.element = typeof element === 'string' ? $(element) : element;
    this.options = options;
    this.state = {};
    this.subscriptions = [];
    this.eventCleanups = [];
    
    if (!this.element) {
      throw new Error(`Element not found: ${element}`);
    }
    
    this.initialize();
  }
  
  // Override in subclasses
  initialize() {
    this.render();
    this.attachEvents();
    this.subscribeToState();
  }
  
  // Override in subclasses
  render() {
    console.warn(`${this.constructor.name} should implement render()`);
  }
  
  // Override in subclasses
  attachEvents() {
    // Subclasses attach their event listeners here
  }
  
  // Override in subclasses
  subscribeToState() {
    // Subclasses subscribe to state changes here
  }
  
  // Helper to subscribe to state with automatic cleanup
  watchState(key, callback) {
    const unsubscribe = state.subscribe(key, callback.bind(this));
    this.subscriptions.push(unsubscribe);
    return unsubscribe;
  }
  
  // Helper to add event listener with automatic cleanup
  on(selector, event, handler) {
    if (typeof selector === 'string') {
      // Delegated event
      const cleanup = delegate(this.element, selector, event, handler.bind(this));
      this.eventCleanups.push(cleanup);
    } else {
      // Direct event
      handler = event;
      event = selector;
      const boundHandler = handler.bind(this);
      this.element.addEventListener(event, boundHandler);
      this.eventCleanups.push(() => {
        this.element.removeEventListener(event, boundHandler);
      });
    }
  }
  
  // Query within component
  $(selector) {
    return $(selector, this.element);
  }
  
  $$(selector) {
    return $$(selector, this.element);
  }
  
  // Update local state and re-render
  setState(updates) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...updates };
    this.onStateChange(updates, oldState);
  }
  
  // Called when local state changes
  onStateChange(updates, oldState) {
    this.render();
  }
  
  // Show/hide component
  show() {
    classes.remove(this.element, 'hidden');
    this.element.style.display = '';
  }
  
  hide() {
    classes.add(this.element, 'hidden');
    this.element.style.display = 'none';
  }
  
  // Enable/disable component
  enable() {
    classes.remove(this.element, 'disabled');
    this.element.removeAttribute('aria-disabled');
  }
  
  disable() {
    classes.add(this.element, 'disabled');
    this.element.setAttribute('aria-disabled', 'true');
  }
  
  // Cleanup when component is destroyed
  destroy() {
    // Unsubscribe from state
    this.subscriptions.forEach(unsubscribe => unsubscribe());
    this.subscriptions = [];
    
    // Remove event listeners
    this.eventCleanups.forEach(cleanup => cleanup());
    this.eventCleanups = [];
    
    // Clear element
    this.element.innerHTML = '';
  }
  
  // Alias for destroy to match subclass expectations
  cleanup() {
    this.destroy();
  }
}

// CSS class name generator with BEM convention
export function bem(block, element, modifier) {
  let className = block;
  
  if (element) {
    className += `__${element}`;
  }
  
  if (modifier) {
    if (typeof modifier === 'string') {
      className += `--${modifier}`;
    } else if (typeof modifier === 'object') {
      Object.entries(modifier).forEach(([key, value]) => {
        if (value) {
          className += ` ${block}${element ? `__${element}` : ''}--${key}`;
        }
      });
    }
  }
  
  return className;
}