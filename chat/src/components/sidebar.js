/**
 * Sidebar Component
 * Table of contents with collapsible sections and navigation
 */
import { BaseComponent, bem } from './base-component.js';
import { state } from '../state-manager.js';
import { escapeHtml } from '../utils/dom-helpers.js';

export class Sidebar extends BaseComponent {
  initialize() {
    this.state = {
      sections: [],
      currentSection: null,
      expandedSections: new Set(),
      isOpen: true,
      searchQuery: ''
    };
    
    super.initialize();
  }
  
  render() {
    const sidebarClass = this.state.isOpen ? 'sidebar sidebar--open' : 'sidebar sidebar--closed';
    
    this.element.innerHTML = `
      <aside class="${sidebarClass}" role="navigation" aria-label="Document navigation">
        <div class="${bem('sidebar', 'header')}">
          <h2 class="${bem('sidebar', 'title')}">Contents</h2>
          <button 
            class="${bem('sidebar', 'toggle')}"
            aria-label="${this.state.isOpen ? 'Close sidebar' : 'Open sidebar'}"
            title="${this.state.isOpen ? 'Close sidebar' : 'Open sidebar'}"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="${this.state.isOpen 
                ? 'M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z'
                : 'M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z'}"/>
            </svg>
          </button>
        </div>
        
        ${this.renderSearch()}
        
        <nav class="${bem('sidebar', 'nav')}" role="tree">
          ${this.renderSections()}
        </nav>
        
        ${this.renderFooter()}
      </aside>
    `;
  }
  
  renderSearch() {
    return `
      <div class="${bem('sidebar', 'search')}">
        <input 
          type="search"
          class="${bem('sidebar', 'search-input')}"
          placeholder="Search sections..."
          value="${escapeHtml(this.state.searchQuery)}"
          aria-label="Search sections"
        >
        <svg class="${bem('sidebar', 'search-icon')}" viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
      </div>
    `;
  }
  
  renderSections() {
    if (this.state.sections.length === 0) {
      return `
        <div class="${bem('sidebar', 'empty')}">
          <p>No sections available</p>
        </div>
      `;
    }
    
    const filteredSections = this.filterSections(this.state.sections, this.state.searchQuery);
    
    if (filteredSections.length === 0) {
      return `
        <div class="${bem('sidebar', 'empty')}">
          <p>No sections match your search</p>
        </div>
      `;
    }
    
    return `
      <ul class="${bem('sidebar', 'list')}" role="tree">
        ${filteredSections.map(section => this.renderSection(section)).join('')}
      </ul>
    `;
  }
  
  renderSection(section) {
    const isExpanded = this.state.expandedSections.has(section.id);
    const hasSubsections = section.subsections && section.subsections.length > 0;
    const isActive = section.id === this.state.currentSection;
    const isParentOfActive = this.isParentOfActiveSection(section);
    
    let itemClass = 'sidebar__item';
    if (isActive) itemClass += ' sidebar__item--active';
    if (isParentOfActive) itemClass += ' sidebar__item--parent-active';
    if (hasSubsections) itemClass += ' sidebar__item--has-children';
    if (isExpanded) itemClass += ' sidebar__item--expanded';
    
    return `
      <li class="${itemClass}" role="treeitem" aria-expanded="${isExpanded}">
        <div class="${bem('sidebar', 'item-content')}">
          ${hasSubsections ? `
            <button 
              class="${bem('sidebar', 'expand-btn')}"
              data-section-id="${section.id}"
              aria-label="${isExpanded ? 'Collapse' : 'Expand'} ${escapeHtml(section.title)}"
            >
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="${isExpanded 
                  ? 'M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z'
                  : 'M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z'}"/>
              </svg>
            </button>
          ` : `
            <span class="${bem('sidebar', 'indent')}"></span>
          `}
          
          <a 
            href="#${section.id}"
            class="${bem('sidebar', 'link')}"
            data-section-id="${section.id}"
            ${isActive ? 'aria-current="page"' : ''}
          >
            <span class="${bem('sidebar', 'link-text')}">${escapeHtml(section.title)}</span>
            ${section.bracketedPhrase ? `
              <span class="${bem('sidebar', 'badge')}">${escapeHtml(section.bracketedPhrase)}</span>
            ` : ''}
          </a>
        </div>
        
        ${hasSubsections && isExpanded ? `
          <ul class="${bem('sidebar', 'sublist')}" role="group">
            ${section.subsections.map(sub => this.renderSubsection(sub)).join('')}
          </ul>
        ` : ''}
      </li>
    `;
  }
  
  renderSubsection(subsection) {
    const isActive = subsection.id === this.state.currentSection;
    
    const itemClass = isActive ? 'sidebar__subitem sidebar__subitem--active' : 'sidebar__subitem';
    
    return `
      <li class="${itemClass}" role="treeitem">
        <a 
          href="#${subsection.id}"
          class="${bem('sidebar', 'sublink')}"
          data-section-id="${subsection.id}"
          ${isActive ? 'aria-current="page"' : ''}
        >
          <span class="${bem('sidebar', 'sublink-text')}">${escapeHtml(subsection.title)}</span>
        </a>
      </li>
    `;
  }
  
  renderFooter() {
    return `
      <div class="${bem('sidebar', 'footer')}">
        <button class="${bem('sidebar', 'collapse-all')}" title="Collapse all sections">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12 8l-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z"/>
          </svg>
          Collapse All
        </button>
      </div>
    `;
  }
  
  attachEvents() {
    // Toggle sidebar
    this.on('.sidebar__toggle', 'click', this.handleToggle);
    
    // Expand/collapse sections
    this.on('.sidebar__expand-btn', 'click', this.handleExpandToggle);
    
    // Section navigation
    this.on('.sidebar__link, .sidebar__sublink', 'click', this.handleNavigation);
    
    // Search
    this.on('.sidebar__search-input', 'input', this.handleSearch);
    
    // Collapse all
    this.on('.sidebar__collapse-all', 'click', this.handleCollapseAll);
    
    // Keyboard navigation
    this.on('.sidebar__nav', 'keydown', this.handleKeyboardNav);
  }
  
  subscribeToState() {
    // Watch for sections updates
    this.watchState('sections', (sections) => {
      this.setState({ sections });
      // Auto-expand parent of current section
      this.autoExpandCurrentSection();
    });
    
    // Watch for current section changes
    this.watchState('currentSection', (currentSection) => {
      this.setState({ currentSection });
      this.autoExpandCurrentSection();
    });
  }
  
  handleToggle(e) {
    e.preventDefault();
    this.setState({ isOpen: !this.state.isOpen });
    
    // Emit event for other components
    this.element.dispatchEvent(new CustomEvent('sidebar-toggle', {
      detail: { isOpen: this.state.isOpen },
      bubbles: true
    }));
  }
  
  handleExpandToggle(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const sectionId = e.currentTarget.dataset.sectionId;
    const expanded = new Set(this.state.expandedSections);
    
    if (expanded.has(sectionId)) {
      expanded.delete(sectionId);
    } else {
      expanded.add(sectionId);
    }
    
    this.setState({ expandedSections: expanded });
  }
  
  handleNavigation(e) {
    e.preventDefault();
    
    const sectionId = e.currentTarget.dataset.sectionId;
    
    // Update state
    state.set({ currentSection: sectionId });
    
    // Emit navigation event
    this.element.dispatchEvent(new CustomEvent('section-navigate', {
      detail: { sectionId },
      bubbles: true
    }));
  }
  
  handleSearch(e) {
    const query = e.target.value;
    this.setState({ searchQuery: query });
    
    // Expand all sections when searching
    if (query) {
      const expanded = new Set(this.state.sections.map(s => s.id));
      this.setState({ expandedSections: expanded });
    }
  }
  
  handleCollapseAll(e) {
    e.preventDefault();
    this.setState({ expandedSections: new Set() });
  }
  
  handleKeyboardNav(e) {
    const current = e.target;
    if (!current.matches('.sidebar__link, .sidebar__sublink')) return;
    
    let next;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        next = this.findNextLink(current);
        if (next) next.focus();
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        next = this.findPrevLink(current);
        if (next) next.focus();
        break;
        
      case 'ArrowRight':
        // Expand if has children
        const expandBtn = current.parentElement.querySelector('.sidebar__expand-btn');
        if (expandBtn && !this.state.expandedSections.has(current.dataset.sectionId)) {
          expandBtn.click();
        }
        break;
        
      case 'ArrowLeft':
        // Collapse if expanded, or focus parent
        const parentExpandBtn = current.parentElement.querySelector('.sidebar__expand-btn');
        if (parentExpandBtn && this.state.expandedSections.has(current.dataset.sectionId)) {
          parentExpandBtn.click();
        } else {
          // Focus parent section
          const parentItem = current.closest('.sidebar__sublist')?.closest('.sidebar__item');
          if (parentItem) {
            parentItem.querySelector('.sidebar__link')?.focus();
          }
        }
        break;
    }
  }
  
  // Helper methods
  filterSections(sections, query) {
    if (!query) return sections;
    
    const lowerQuery = query.toLowerCase();
    
    return sections.filter(section => {
      // Check section title
      if (section.title.toLowerCase().includes(lowerQuery)) return true;
      
      // Check subsections
      if (section.subsections) {
        return section.subsections.some(sub => 
          sub.title.toLowerCase().includes(lowerQuery)
        );
      }
      
      return false;
    });
  }
  
  isParentOfActiveSection(section) {
    if (!section.subsections || !this.state.currentSection) return false;
    
    return section.subsections.some(sub => sub.id === this.state.currentSection);
  }
  
  autoExpandCurrentSection() {
    if (!this.state.currentSection) return;
    
    // Find parent section if current is a subsection
    for (const section of this.state.sections) {
      if (section.subsections) {
        const hasActiveChild = section.subsections.some(
          sub => sub.id === this.state.currentSection
        );
        
        if (hasActiveChild) {
          const expanded = new Set(this.state.expandedSections);
          expanded.add(section.id);
          this.setState({ expandedSections: expanded });
          break;
        }
      }
    }
  }
  
  findNextLink(current) {
    const links = Array.from(this.element.querySelectorAll('.sidebar__link, .sidebar__sublink'));
    const currentIndex = links.indexOf(current);
    return links[currentIndex + 1] || null;
  }
  
  findPrevLink(current) {
    const links = Array.from(this.element.querySelectorAll('.sidebar__link, .sidebar__sublink'));
    const currentIndex = links.indexOf(current);
    return links[currentIndex - 1] || null;
  }
  
  // Public API
  expandSection(sectionId) {
    const expanded = new Set(this.state.expandedSections);
    expanded.add(sectionId);
    this.setState({ expandedSections: expanded });
  }
  
  collapseSection(sectionId) {
    const expanded = new Set(this.state.expandedSections);
    expanded.delete(sectionId);
    this.setState({ expandedSections: expanded });
  }
  
  expandAll() {
    const expanded = new Set(this.state.sections.map(s => s.id));
    this.setState({ expandedSections: expanded });
  }
  
  collapseAll() {
    this.setState({ expandedSections: new Set() });
  }
  
  setOpen(isOpen) {
    this.setState({ isOpen });
  }
  
  toggle() {
    this.setState({ isOpen: !this.state.isOpen });
  }
}