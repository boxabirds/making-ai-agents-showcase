/**
 * State Manager
 * Central state management with event-based updates
 * Simple pub/sub pattern for reactive updates
 */
export class StateManager {
  constructor() {
    this.state = {
      // Document state
      currentSection: null,
      currentSubsection: null,
      documentContent: null,
      sections: [],
      
      // Chat state
      messages: [],
      conversationHistory: [],
      isProcessing: false,
      
      // UI state
      sidebarOpen: false,
      documentViewerOpen: false,
      isMobile: window.innerWidth <= 768,
      
      // Config
      apiEndpoint: 'https://tech-writer-ai-proxy.julian-harris.workers.dev',
      model: 'gemini-2.0-flash',
      maxTokens: 1024,
      temperature: 0.0
    };
    
    this.listeners = new Map();
    this.debug = true;
  }
  
  // Get current state or specific path
  get(path) {
    if (!path) return { ...this.state };
    
    const keys = path.split('.');
    let value = this.state;
    
    for (const key of keys) {
      value = value[key];
      if (value === undefined) return undefined;
    }
    
    return value;
  }
  
  // Update state and notify listeners
  set(updates) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...updates };
    
    if (this.debug) {
      console.log('State updated:', updates);
    }
    
    // Notify all listeners
    this.notify(updates, oldState);
  }
  
  // Subscribe to state changes
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    
    this.listeners.get(key).add(callback);
    
    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(key);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(key);
        }
      }
    };
  }
  
  // Notify listeners of changes
  notify(updates, oldState) {
    // Notify global listeners
    const globalListeners = this.listeners.get('*');
    if (globalListeners) {
      globalListeners.forEach(callback => {
        callback(this.state, updates, oldState);
      });
    }
    
    // Notify specific listeners
    Object.keys(updates).forEach(key => {
      const listeners = this.listeners.get(key);
      if (listeners) {
        listeners.forEach(callback => {
          callback(updates[key], key, oldState[key]);
        });
      }
    });
  }
  
  // Helper methods for common state updates
  addMessage(message) {
    this.set({
      messages: [...this.state.messages, message]
    });
  }
  
  updateConversationHistory(entries) {
    this.set({
      conversationHistory: [...this.state.conversationHistory, ...entries]
    });
  }
  
  setProcessing(isProcessing) {
    this.set({ isProcessing });
  }
  
  navigateToSection(sectionId, subsectionId = null) {
    this.set({
      currentSection: sectionId,
      currentSubsection: subsectionId
    });
  }
  
  toggleSidebar() {
    this.set({ sidebarOpen: !this.state.sidebarOpen });
  }
  
  toggleDocumentViewer() {
    this.set({ documentViewerOpen: !this.state.documentViewerOpen });
  }
  
  updateMobileState() {
    const isMobile = window.innerWidth <= 768;
    if (isMobile !== this.state.isMobile) {
      this.set({ isMobile });
    }
  }
}

// Export singleton instance
export const state = new StateManager();