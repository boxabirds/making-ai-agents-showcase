// Document parser module for handling markdown documents
class DocumentParser {
    constructor() {
        this.sections = [];
        this.rawMarkdown = '';
        this.renderedHTML = '';
    }

    // Parse markdown content and extract structure
    parseMarkdown(markdownContent) {
        this.rawMarkdown = markdownContent;
        this.sections = [];
        
        // Split by H1 sections
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
                        currentSubsection.content = contentBuffer.join('\n');
                        currentSubsection = null;
                    } else {
                        currentSection.content = contentBuffer.join('\n');
                    }
                    this.sections.push(currentSection);
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
                    currentSubsection.content = contentBuffer.join('\n');
                }
                
                // Parse title for bracketed phrase
                const titleInfo = this.parseTitleWithBrackets(h2Match[1]);
                
                // Start new subsection
                currentSubsection = {
                    id: this.slugify(titleInfo.displayTitle),
                    title: titleInfo.displayTitle,
                    fullTitle: h2Match[1],
                    bracketedPhrase: titleInfo.bracketedPhrase,
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
        
        // Save last section
        if (currentSection) {
            if (currentSubsection) {
                currentSubsection.content = contentBuffer.join('\n');
            } else {
                currentSection.content = contentBuffer.join('\n');
            }
            this.sections.push(currentSection);
        }
        
        // Render full HTML
        this.renderedHTML = marked.parse(markdownContent);
        
        return this.sections;
    }

    // Get a specific section by ID
    getSection(sectionId) {
        for (const section of this.sections) {
            if (section.id === sectionId) {
                return section;
            }
            for (const subsection of section.subsections) {
                if (subsection.id === sectionId) {
                    return subsection;
                }
            }
        }
        return null;
    }

    // Get rendered HTML for a section
    getSectionHTML(sectionId) {
        const section = this.getSection(sectionId);
        if (!section) return '';
        
        if (section.level === 1) {
            // Include all subsections for H1
            let fullContent = section.content;
            section.subsections.forEach(sub => {
                fullContent += '\n' + sub.content;
            });
            // Add IDs to headings for navigation
            const html = marked.parse(fullContent);
            return this.addHeadingIds(html);
        } else {
            // Just the subsection content for H2
            return marked.parse(section.content);
        }
    }
    
    // Add IDs to H2 headings for in-page navigation
    addHeadingIds(html) {
        return html.replace(/<h2>(.*?)<\/h2>/g, (match, title) => {
            // Parse for bracketed phrase and use display title
            const titleInfo = this.parseTitleWithBrackets(title);
            const id = this.slugify(titleInfo.displayTitle);
            return `<h2 id="${id}">${titleInfo.displayTitle}</h2>`;
        });
    }

    // Get quick actions (first 2 words of H2 titles) for a section
    getQuickActions(sectionId) {
        const section = this.sections.find(s => s.id === sectionId);
        if (!section) return [];
        
        return section.subsections.map(sub => {
            // Use bracketed phrase if available, otherwise use first 2 words
            let displayText;
            if (sub.bracketedPhrase) {
                displayText = sub.bracketedPhrase;
            } else {
                const words = sub.title.split(' ');
                displayText = words.length > 2 
                    ? words.slice(0, 2).join(' ') + '...'
                    : sub.title;
            }
            
            return {
                id: sub.id,
                text: displayText,
                fullTitle: sub.title
            };
        });
    }

    // Parse title with bracketed phrase at end
    parseTitleWithBrackets(title) {
        const bracketMatch = title.match(/^(.+?)\s*\(([^)]+)\)\s*$/);
        if (bracketMatch) {
            return {
                displayTitle: bracketMatch[1].trim(),
                bracketedPhrase: bracketMatch[2].trim()
            };
        }
        return {
            displayTitle: title,
            bracketedPhrase: null
        };
    }
    
    // Create slug from title
    slugify(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-')
            .trim();
    }

    // Get all H1 sections for navigation
    getMainSections() {
        return this.sections.map(section => ({
            id: section.id,
            title: section.title,
            hasSubsections: section.subsections.length > 0
        }));
    }

    // Search through document content
    searchContent(query) {
        const lowerQuery = query.toLowerCase();
        const results = [];
        
        this.sections.forEach(section => {
            if (section.title.toLowerCase().includes(lowerQuery) ||
                section.content.toLowerCase().includes(lowerQuery)) {
                results.push({
                    sectionId: section.id,
                    title: section.title,
                    type: 'section',
                    preview: this.getPreview(section.content, lowerQuery)
                });
            }
            
            section.subsections.forEach(sub => {
                if (sub.title.toLowerCase().includes(lowerQuery) ||
                    sub.content.toLowerCase().includes(lowerQuery)) {
                    results.push({
                        sectionId: sub.id,
                        title: sub.title,
                        parentTitle: section.title,
                        type: 'subsection',
                        preview: this.getPreview(sub.content, lowerQuery)
                    });
                }
            });
        });
        
        return results;
    }

    // Get preview text around search term
    getPreview(content, searchTerm) {
        const index = content.toLowerCase().indexOf(searchTerm.toLowerCase());
        if (index === -1) return '';
        
        const start = Math.max(0, index - 50);
        const end = Math.min(content.length, index + searchTerm.length + 50);
        
        let preview = content.substring(start, end);
        if (start > 0) preview = '...' + preview;
        if (end < content.length) preview = preview + '...';
        
        return preview;
    }
}

// Create global instance
window.documentParser = new DocumentParser();