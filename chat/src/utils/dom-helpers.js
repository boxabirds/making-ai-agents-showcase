/**
 * DOM Helper Utilities
 * Common DOM manipulation and event handling utilities
 */

// Create element with classes and attributes
export function createElement(tag, options = {}) {
  const element = document.createElement(tag);
  
  if (options.className) {
    element.className = options.className;
  }
  
  if (options.attributes) {
    Object.entries(options.attributes).forEach(([key, value]) => {
      element.setAttribute(key, value);
    });
  }
  
  if (options.innerHTML) {
    element.innerHTML = options.innerHTML;
  }
  
  if (options.textContent) {
    element.textContent = options.textContent;
  }
  
  return element;
}

// Escape HTML to prevent XSS
export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Add event listener with automatic cleanup
export function addEventHandler(element, event, handler, options) {
  element.addEventListener(event, handler, options);
  
  // Return cleanup function
  return () => {
    element.removeEventListener(event, handler, options);
  };
}

// Delegate event handling for dynamic content
export function delegate(container, selector, event, handler) {
  const delegatedHandler = (e) => {
    const target = e.target.closest(selector);
    if (target && container.contains(target)) {
      handler.call(target, e);
    }
  };
  
  return addEventHandler(container, event, delegatedHandler);
}

// Debounce function for performance
export function debounce(func, wait) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Smooth scroll to element
export function scrollToElement(element, options = {}) {
  const defaults = {
    behavior: 'smooth',
    block: 'start',
    inline: 'nearest'
  };
  
  element.scrollIntoView({ ...defaults, ...options });
}

// Check if element is in viewport
export function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

// Class manipulation helpers
export const classes = {
  add: (element, ...classNames) => {
    element.classList.add(...classNames);
  },
  
  remove: (element, ...classNames) => {
    element.classList.remove(...classNames);
  },
  
  toggle: (element, className, force) => {
    return element.classList.toggle(className, force);
  },
  
  has: (element, className) => {
    return element.classList.contains(className);
  }
};

// Query selector shortcuts
export const $ = (selector, context = document) => context.querySelector(selector);
export const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

// Template literal tag for safe HTML
export function html(strings, ...values) {
  return strings.reduce((result, string, i) => {
    const value = values[i - 1];
    if (value === undefined) return result + string;
    
    // Escape if not marked as safe
    const escaped = value.__safe ? value : escapeHtml(String(value));
    return result + escaped + string;
  });
}

// Mark HTML as safe (use with caution)
export function safeHtml(htmlString) {
  return { __safe: true, toString: () => htmlString };
}