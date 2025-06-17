/**
 * Document Parser Component
 * Handles markdown parsing, structure extraction, and document navigation
 */
import { BaseComponent } from './base-component.js';
import { state } from '../state-manager.js';
import { escapeHtml } from '../utils/dom-helpers.js';

export class DocumentParser extends BaseComponent {
  initialize() {
    this.state = {
      sections: [],
      rawMarkdown: '',
      renderedHTML: ''
    };
    
    // Initialize without rendering since this is a non-visual component
    this.subscribeToState();
  }
  
  render() {
    // This is a non-visual component, no DOM rendering needed
  }
  
  /**
   * Parse markdown content and extract structure
   * Handles H1 sections with H2 subsections
   * Supports bracketed phrases in titles
   */
  parseMarkdown(markdownContent) {
    this.state.rawMarkdown = markdownContent;
    this.state.sections = [];
    
    const lines = markdownContent.split('\n');
    let currentSection = null;
    let currentSubsection = null;
    let contentBuffer = [];
    
    lines.forEach((line, index) => {
      const h1Match = line.match(/^#\s+(.+)$/);
      const h2Match = line.match(/^##\s+(.+)$/);
      
      if (h1Match) {
        // Save previous section if exists
        if (currentSection) {
          if (currentSubsection) {
            currentSubsection.content = contentBuffer.join('\n').trim();
            currentSubsection = null;
          } else {
            currentSection.content = contentBuffer.join('\n').trim();
          }
          this.state.sections.push(currentSection);
        }
        
        // Parse title for bracketed phrase
        const titleInfo = this.parseTitleWithBrackets(h1Match[1]);
        
        // Start new section
        currentSection = {
          id: this.slugify(titleInfo.displayTitle),
          title: titleInfo.displayTitle,
          fullTitle: h1Match[1],
          bracketedPhrase: titleInfo.bracketedPhrase,
          level: 1,
          content: '',
          subsections: [],
          startLine: index
        };
        contentBuffer = [line];
      } else if (h2Match && currentSection) {
        // Save previous subsection if exists
        if (currentSubsection) {
          currentSubsection.content = contentBuffer.join('\n').trim();
        } else {
          // Save section content before first subsection
          currentSection.content = contentBuffer.join('\n').trim();
        }
        
        // Parse subsection title
        const titleInfo = this.parseTitleWithBrackets(h2Match[1]);
        
        // Create new subsection
        currentSubsection = {
          id: this.slugify(titleInfo.displayTitle),
          title: titleInfo.displayTitle,
          fullTitle: h2Match[1],
          bracketedPhrase: titleInfo.bracketedPhrase,
          text: titleInfo.displayTitle, // For quick actions
          level: 2,
          content: '',
          parentId: currentSection.id,
          startLine: index
        };
        
        currentSection.subsections.push(currentSubsection);
        contentBuffer = [line];
      } else {
        contentBuffer.push(line);
      }
    });
    
    // Save final section
    if (currentSection) {
      if (currentSubsection) {
        currentSubsection.content = contentBuffer.join('\n').trim();
      } else {
        currentSection.content = contentBuffer.join('\n').trim();
      }
      this.state.sections.push(currentSection);
    }
    
    // Update global state
    state.set({
      sections: this.state.sections,
      documentContent: markdownContent
    });
    
    // Render full HTML
    this.renderFullHTML();
    
    return this.state.sections;
  }
  
  /**
   * Parse title with bracketed phrases
   * Example: "Introduction [Getting Started]" -> 
   * { displayTitle: "Introduction", bracketedPhrase: "Getting Started" }
   */
  parseTitleWithBrackets(title) {
    const match = title.match(/^(.+?)\s*\[(.+)\]\s*$/);
    
    if (match) {
      return {
        displayTitle: match[1].trim(),
        bracketedPhrase: match[2].trim()
      };
    }
    
    return {
      displayTitle: title.trim(),
      bracketedPhrase: null
    };
  }
  
  /**
   * Convert title to URL-friendly slug
   */
  slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-')     // Replace spaces with hyphens
      .replace(/-+/g, '-')      // Replace multiple hyphens with single
      .trim();
  }
  
  /**
   * Get section by ID
   */
  getSection(sectionId) {
    for (const section of this.state.sections) {
      if (section.id === sectionId) {
        return section;
      }
      
      // Check subsections
      const subsection = section.subsections.find(sub => sub.id === sectionId);
      if (subsection) {
        return subsection;
      }
    }
    return null;
  }
  
  /**
   * Get HTML for a specific section
   */
  getSectionHTML(sectionId) {
    const section = this.getSection(sectionId);
    if (!section) return '';
    
    // Include subsections if it's a main section
    let markdown = section.content;
    if (section.level === 1 && section.subsections.length > 0) {
      section.subsections.forEach(sub => {
        markdown += '\n\n' + sub.content;
      });
    }
    
    return this.renderMarkdown(markdown);
  }
  
  /**
   * Get quick actions for current section (subsections)
   */
  getQuickActions(sectionId) {
    const section = this.getSection(sectionId);
    if (!section || section.level !== 1) return [];
    
    return section.subsections.map(sub => ({
      id: sub.id,
      text: sub.title,
      fullTitle: `${section.title} > ${sub.title}`
    }));
  }
  
  /**
   * Get main sections only (H1)
   */
  getMainSections() {
    return this.state.sections;
  }
  
  /**
   * Render markdown to HTML using marked.js
   */
  renderMarkdown(markdown) {
    if (typeof marked === 'undefined') {
      console.warn('marked.js not loaded');
      return escapeHtml(markdown);
    }
    
    try {
      // Configure marked options
      marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: true,
        mangle: false
      });
      
      // Render markdown
      let html = marked.parse(markdown);
      
      // Add IDs to headers for navigation
      html = html.replace(/<h(\d)>(.*?)<\/h\d>/g, (match, level, content) => {
        const id = this.slugify(content.replace(/<[^>]*>/g, ''));
        return `<h${level} id="${id}">${content}</h${level}>`;
      });
      
      return html;
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return escapeHtml(markdown);
    }
  }
  
  /**
   * Render full document HTML
   */
  renderFullHTML() {
    this.state.renderedHTML = this.renderMarkdown(this.state.rawMarkdown);
    return this.state.renderedHTML;
  }
  
  /**
   * Find section by search query
   */
  searchSections(query) {
    const lowerQuery = query.toLowerCase();
    const results = [];
    
    this.state.sections.forEach(section => {
      // Check section title
      if (section.title.toLowerCase().includes(lowerQuery)) {
        results.push({
          type: 'section',
          item: section,
          score: section.title.toLowerCase().startsWith(lowerQuery) ? 2 : 1
        });
      }
      
      // Check subsections
      section.subsections.forEach(sub => {
        if (sub.title.toLowerCase().includes(lowerQuery)) {
          results.push({
            type: 'subsection',
            item: sub,
            parent: section,
            score: sub.title.toLowerCase().startsWith(lowerQuery) ? 2 : 1
          });
        }
      });
    });
    
    // Sort by score
    return results.sort((a, b) => b.score - a.score);
  }
  
  /**
   * Get table of contents
   */
  getTableOfContents() {
    const toc = [];
    
    this.state.sections.forEach(section => {
      toc.push({
        id: section.id,
        title: section.title,
        level: 1,
        children: section.subsections.map(sub => ({
          id: sub.id,
          title: sub.title,
          level: 2
        }))
      });
    });
    
    return toc;
  }
  
  /**
   * Get navigation context (prev/next sections)
   */
  getNavigationContext(currentSectionId) {
    const sections = this.state.sections;
    const currentIndex = sections.findIndex(s => s.id === currentSectionId);
    
    if (currentIndex === -1) {
      // Check if it's a subsection
      for (let i = 0; i < sections.length; i++) {
        const subIndex = sections[i].subsections.findIndex(sub => sub.id === currentSectionId);
        if (subIndex !== -1) {
          return {
            current: sections[i].subsections[subIndex],
            parent: sections[i],
            prev: subIndex > 0 ? sections[i].subsections[subIndex - 1] : sections[i],
            next: subIndex < sections[i].subsections.length - 1 
              ? sections[i].subsections[subIndex + 1]
              : (i < sections.length - 1 ? sections[i + 1] : null)
          };
        }
      }
      return null;
    }
    
    return {
      current: sections[currentIndex],
      parent: null,
      prev: currentIndex > 0 ? sections[currentIndex - 1] : null,
      next: currentIndex < sections.length - 1 ? sections[currentIndex + 1] : null
    };
  }
}

// Export singleton instance
export const documentParser = new DocumentParser(document.createElement('div'));