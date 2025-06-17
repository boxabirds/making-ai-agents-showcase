/**
 * Document Viewer Component
 * Displays markdown content with section navigation
 */
import { BaseComponent, bem } from './base-component.js';
import { state } from '../state-manager.js';
import { documentParser } from './document-parser.js';

export class DocumentViewer extends BaseComponent {
  initialize() {
    this.state = {
      content: '',
      currentSection: null,
      isOpen: false,
      scrollPosition: 0,
      headingOffsets: new Map()
    };
    
    this.intersectionObserver = null;
    this.scrollTimeout = null;
    
    super.initialize();
  }
  
  render() {
    const viewerClass = bem('document-viewer', null, {
      'open': this.state.isOpen
    });
    
    this.element.innerHTML = `
      <div class="${viewerClass}">
        <div class="${bem('document-viewer', 'header')}">
          <div class="${bem('document-viewer', 'nav')}">
            <button 
              class="${bem('document-viewer', 'nav-btn', 'prev')}"
              aria-label="Previous section"
              title="Previous section (Shift+Space)"
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
              </svg>
              <span>Previous</span>
            </button>
            
            <div class="${bem('document-viewer', 'breadcrumb')}">
              <span class="${bem('document-viewer', 'section-title')}"></span>
            </div>
            
            <button 
              class="${bem('document-viewer', 'nav-btn', 'next')}"
              aria-label="Next section"
              title="Next section (Space)"
            >
              <span>Next</span>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"/>
              </svg>
            </button>
          </div>
          
          <button 
            class="${bem('document-viewer', 'close')}"
            aria-label="Close document viewer"
            title="Close (Escape)"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div class="${bem('document-viewer', 'content')}" role="document">
          <div class="${bem('document-viewer', 'inner')}">
            ${this.state.content || '<p class="document-viewer__empty">No content to display</p>'}
          </div>
        </div>
        
        <div class="${bem('document-viewer', 'footer')}">
          <div class="${bem('document-viewer', 'progress')}">
            <div class="${bem('document-viewer', 'progress-bar')}"></div>
          </div>
          <div class="${bem('document-viewer', 'stats')}">
            <span class="${bem('document-viewer', 'read-time')}"></span>
          </div>
        </div>
      </div>
    `;
    
    // Setup intersection observer after render
    setTimeout(() => this.setupIntersectionObserver(), 0);
    
    // Update UI elements
    this.updateNavigation();
    this.updateProgress();
  }
  
  attachEvents() {
    // Navigation buttons
    this.on('.document-viewer__nav-btn--prev', 'click', () => this.navigatePrevious());
    this.on('.document-viewer__nav-btn--next', 'click', () => this.navigateNext());
    
    // Close button
    this.on('.document-viewer__close', 'click', () => this.close());
    
    // Scroll tracking
    const content = this.$('.document-viewer__content');
    if (content) {
      content.addEventListener('scroll', this.handleScroll.bind(this));
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', this.handleKeydown.bind(this));
    
    // Handle clicks on internal links
    this.on('.document-viewer__inner a[href^="#"]', 'click', this.handleInternalLink);
  }
  
  subscribeToState() {
    // Watch for current section changes
    this.watchState('currentSection', (sectionId) => {
      if (sectionId && sectionId !== this.state.currentSection) {
        this.navigateToSection(sectionId);
      }
    });
    
    // Watch for document content changes
    this.watchState('documentContent', (content) => {
      if (content && !this._isLoadingDocument) {
        // Only render the already parsed content, don't re-parse
        const html = documentParser.renderFullHTML();
        this.setState({ content: html });
      }
    });
  }
  
  setupIntersectionObserver() {
    // Disconnect existing observer
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    // Create new observer to track visible headings
    this.intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            if (id) {
              // Update current section based on visible heading
              this.updateCurrentSection(id);
            }
          }
        });
      },
      {
        root: this.$('.document-viewer__content'),
        rootMargin: '-20% 0px -70% 0px',
        threshold: 0
      }
    );
    
    // Observe all headings
    const headings = this.element.querySelectorAll('h1[id], h2[id]');
    headings.forEach(heading => {
      this.intersectionObserver.observe(heading);
    });
  }
  
  handleScroll(e) {
    // Debounce scroll events
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    
    this.scrollTimeout = setTimeout(() => {
      this.state.scrollPosition = e.target.scrollTop;
      this.updateProgress();
    }, 100);
  }
  
  handleKeydown(e) {
    if (!this.state.isOpen) return;
    
    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        this.close();
        break;
        
      case ' ':
        if (e.shiftKey) {
          e.preventDefault();
          this.navigatePrevious();
        } else if (!e.target.matches('input, textarea')) {
          e.preventDefault();
          this.navigateNext();
        }
        break;
        
      case 'ArrowUp':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          this.navigatePrevious();
        }
        break;
        
      case 'ArrowDown':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          this.navigateNext();
        }
        break;
    }
  }
  
  handleInternalLink(e) {
    e.preventDefault();
    const href = e.currentTarget.getAttribute('href');
    const targetId = href.substring(1); // Remove #
    
    if (targetId) {
      this.navigateToSection(targetId);
    }
  }
  
  updateCurrentSection(sectionId) {
    if (sectionId !== this.state.currentSection) {
      this.state.currentSection = sectionId;
      state.set({ currentSection: sectionId });
      this.updateNavigation();
    }
  }
  
  updateNavigation() {
    const navContext = documentParser.getNavigationContext(this.state.currentSection);
    if (!navContext) return;
    
    // Update breadcrumb
    const titleEl = this.$('.document-viewer__section-title');
    if (titleEl) {
      if (navContext.parent) {
        titleEl.textContent = `${navContext.parent.title} › ${navContext.current.title}`;
      } else {
        titleEl.textContent = navContext.current.title;
      }
    }
    
    // Update nav buttons
    const prevBtn = this.$('.document-viewer__nav-btn--prev');
    const nextBtn = this.$('.document-viewer__nav-btn--next');
    
    if (prevBtn) {
      prevBtn.disabled = !navContext.prev;
      if (navContext.prev) {
        prevBtn.title = `Previous: ${navContext.prev.title} (Shift+Space)`;
      }
    }
    
    if (nextBtn) {
      nextBtn.disabled = !navContext.next;
      if (navContext.next) {
        nextBtn.title = `Next: ${navContext.next.title} (Space)`;
      }
    }
  }
  
  updateProgress() {
    const content = this.$('.document-viewer__content');
    const progressBar = this.$('.document-viewer__progress-bar');
    
    if (content && progressBar) {
      const scrollPercentage = (content.scrollTop / (content.scrollHeight - content.clientHeight)) * 100;
      progressBar.style.width = `${Math.min(100, Math.max(0, scrollPercentage))}%`;
    }
    
    // Update read time
    this.updateReadTime();
  }
  
  updateReadTime() {
    const readTimeEl = this.$('.document-viewer__read-time');
    if (!readTimeEl) return;
    
    // Calculate words in current section
    const section = documentParser.getSection(this.state.currentSection);
    if (!section) return;
    
    const text = section.content || '';
    const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
    const readTime = Math.ceil(wordCount / 200); // Average reading speed: 200 words/min
    
    readTimeEl.textContent = `${readTime} min read`;
  }
  
  // Public API
  open() {
    this.setState({ isOpen: true });
    document.body.classList.add('document-viewer-open');
    
    this.element.dispatchEvent(new CustomEvent('viewer-open', {
      bubbles: true
    }));
  }
  
  close() {
    this.setState({ isOpen: false });
    document.body.classList.remove('document-viewer-open');
    
    this.element.dispatchEvent(new CustomEvent('viewer-close', {
      bubbles: true
    }));
  }
  
  toggle() {
    if (this.state.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  loadDocument(markdownContent) {
    // Prevent infinite loop
    if (this._isLoadingDocument) return;
    this._isLoadingDocument = true;
    
    try {
      // Parse the document
      const sections = documentParser.parseMarkdown(markdownContent);
      
      // Render the full HTML
      const html = documentParser.renderFullHTML();
      this.setState({ content: html });
      
      // Navigate to first section if none selected
      if (!this.state.currentSection && sections.length > 0) {
        this.navigateToSection(sections[0].id);
      }
      
      // Open the viewer
      this.open();
    } finally {
      this._isLoadingDocument = false;
    }
  }
  
  navigateToSection(sectionId, smooth = true) {
    const targetEl = this.element.querySelector(`#${sectionId}`);
    if (!targetEl) return;
    
    const content = this.$('.document-viewer__content');
    if (!content) return;
    
    // Calculate scroll position
    const contentRect = content.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    const scrollTop = content.scrollTop + targetRect.top - contentRect.top - 20;
    
    // Scroll to section
    if (smooth) {
      content.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      });
    } else {
      content.scrollTop = scrollTop;
    }
    
    // Update state
    this.updateCurrentSection(sectionId);
    
    // Focus for accessibility
    targetEl.setAttribute('tabindex', '-1');
    targetEl.focus({ preventScroll: true });
  }
  
  navigateNext() {
    const navContext = documentParser.getNavigationContext(this.state.currentSection);
    if (navContext && navContext.next) {
      this.navigateToSection(navContext.next.id);
    }
  }
  
  navigatePrevious() {
    const navContext = documentParser.getNavigationContext(this.state.currentSection);
    if (navContext && navContext.prev) {
      this.navigateToSection(navContext.prev.id);
    }
  }
  
  scrollToTop() {
    const content = this.$('.document-viewer__content');
    if (content) {
      content.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }
  
  cleanup() {
    // Disconnect intersection observer
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    // Clear timeout
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    
    // Remove global event listener
    document.removeEventListener('keydown', this.handleKeydown.bind(this));
    
    super.destroy();
  }
}