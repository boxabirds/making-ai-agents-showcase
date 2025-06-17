// State management
const state = {
    currentSection: null,
    currentSubsection: null,
    chatHistory: [],
    isTyping: false,
    documentContent: null
};

// DOM elements
const elements = {
    sidebar: null,
    hamburgerBtn: null,
    closeSidebar: null,
    sectionsList: null,
    quickActions: null,
    messagesContainer: null,
    chatInput: null,
    sendButton: null,
    typingIndicator: null,
    detailPanel: null,
    closePanelBtn: null,
    panelContent: null,
    panelTitle: null,
    mobileOverlay: null,
    documentTitle: null,
    trayChatInput: null,
    traySendButton: null,
    separatorVertical: null,
    fullscreenBtn: null,
    chatContainer: null
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
    setupResizer();
    
    // Load sample document or from URL parameter
    loadDocument();
    
    // Focus on chat input
    elements.chatInput.focus();
});

function initializeElements() {
    // Cache DOM elements
    elements.sidebar = document.getElementById('sidebar');
    elements.hamburgerBtn = document.getElementById('hamburgerBtn');
    elements.closeSidebar = document.getElementById('closeSidebar');
    elements.sectionsList = document.getElementById('sectionsList');
    elements.quickActions = document.getElementById('quickActions');
    elements.messagesContainer = document.getElementById('messagesContainer');
    elements.chatInput = document.getElementById('chatInput');
    elements.sendButton = document.getElementById('sendButton');
    elements.typingIndicator = document.getElementById('typingIndicator');
    elements.detailPanel = document.getElementById('detailPanel');
    elements.closePanelBtn = document.getElementById('closePanelBtn');
    elements.panelContent = document.getElementById('panelContent');
    elements.panelTitle = document.getElementById('panelTitle');
    elements.mobileOverlay = document.getElementById('mobileOverlay');
    elements.documentTitle = document.getElementById('documentTitle');
    elements.trayChatInput = document.getElementById('trayChatInput');
    elements.traySendButton = document.getElementById('traySendButton');
    elements.separatorVertical = document.getElementById('separatorVertical');
    elements.chatContainer = document.querySelector('.chat-container');
}

// Load document content
async function loadDocument() {
    // Check for document URL in query params
    const urlParams = new URLSearchParams(window.location.search);
    const docUrl = urlParams.get('doc');
    
    if (docUrl) {
        try {
            const response = await fetch(docUrl);
            const markdown = await response.text();
            processDocument(markdown);
        } catch (error) {
            console.error('Failed to load document:', error);
            loadSampleDocument();
        }
    } else {
        loadSampleDocument();
    }
}

function loadSampleDocument() {
    // Load a sample markdown document
    const sampleMarkdown = `# Introduction

Welcome to this interactive document viewer. This system allows you to chat with any markdown document.

## Getting Started

To begin, you can click on any section in the sidebar or use the quick action buttons below.

## Features

The document chat interface provides several key features:
- Natural language questions about the content
- Quick navigation between sections
- Intelligent section recommendations

# Usage Guide

This section covers how to use the document chat interface effectively.

## Navigation

You can navigate through the document in several ways:
- Click sections in the sidebar
- Use quick action buttons
- Ask to go to specific sections

## Asking Questions

Feel free to ask any questions about the document content. The AI will help you understand and find information.

# Technical Details

Here's how the system works under the hood.

## Architecture

The system uses a markdown parser to extract document structure and enable intelligent navigation.

## Implementation

Built with vanilla JavaScript and modern web standards for maximum compatibility.`;

    processDocument(sampleMarkdown);
}

function processDocument(markdown) {
    // Parse the markdown document
    const sections = window.documentParser.parseMarkdown(markdown);
    state.documentContent = markdown;
    
    // Render sections in sidebar
    renderSections(sections);
    
    // Show first section by default
    if (sections.length > 0) {
        navigateToSection(sections[0].id);
    }
}

function renderSections(sections) {
    elements.sectionsList.innerHTML = sections.map(section => `
        <button class="nav-item" data-section="${section.id}">
            <span class="nav-icon">${section.hasSubsections ? '📑' : '📄'}</span>
            ${section.title}
        </button>
    `).join('');
    
    // Add click handlers
    elements.sectionsList.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const sectionId = btn.dataset.section;
            navigateToSection(sectionId);
        });
    });
}

function navigateToSection(sectionId, subsectionId = null) {
    // Update active state
    elements.sectionsList.querySelectorAll('.nav-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.section === sectionId);
    });
    
    // Update current section
    state.currentSection = sectionId;
    state.currentSubsection = subsectionId;
    
    // Get section data
    const section = window.documentParser.getSection(sectionId);
    if (!section) return;
    
    // Update panel title
    elements.panelTitle.textContent = section.title;
    
    // Render section content
    const html = window.documentParser.getSectionHTML(sectionId);
    elements.panelContent.innerHTML = html;
    
    // Update quick actions
    updateQuickActions(sectionId);
    
    // Scroll to subsection if specified
    if (subsectionId) {
        // Scroll after next paint to ensure content is rendered
        requestAnimationFrame(() => {
            scrollToSubsection(subsectionId);
        });
    }
    
    // Highlight code blocks
    elements.panelContent.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
        hljs.lineNumbersBlock(block);
    });
    
    // Show panel on mobile
    if (window.innerWidth <= 768) {
        showDetailPanel();
    } else {
        // On desktop, ensure panel is visible
        if (!elements.detailPanel.classList.contains('active')) {
            elements.detailPanel.classList.add('active');
            elements.separatorVertical.classList.add('active');
        }
        
        // Scroll to subsection if specified
        if (subsectionId) {
            // Use requestAnimationFrame to ensure DOM is ready
            requestAnimationFrame(() => {
                scrollToSubsection(subsectionId);
            });
        }
    }
    
    // Focus panel content for keyboard navigation
    elements.panelContent.focus();
}

function updateQuickActions(sectionId) {
    const actions = window.documentParser.getQuickActions(sectionId);
    
    if (actions.length === 0) {
        elements.quickActions.style.display = 'none';
        return;
    }
    
    elements.quickActions.style.display = 'flex';
    elements.quickActions.innerHTML = actions.map(action => `
        <button class="quick-action-btn" data-action="${action.id}" title="${action.fullTitle}">
            ${action.text}
        </button>
    `).join('');
    
    // Add click handlers
    elements.quickActions.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const actionId = btn.dataset.action;
            const action = actions.find(a => a.id === actionId);
            if (action) {
                navigateToSection(state.currentSection, actionId);
                addArtifactToChat(action.fullTitle, 'subsection', actionId);
            }
        });
    });
}

function setupEventListeners() {
    // Mobile menu toggles
    elements.hamburgerBtn.addEventListener('click', () => {
        elements.sidebar.classList.add('active');
        elements.mobileOverlay.classList.add('active');
    });
    
    elements.closeSidebar.addEventListener('click', closeSidebar);
    elements.mobileOverlay.addEventListener('click', () => {
        // Close sidebar if it's open
        if (elements.sidebar.classList.contains('active')) {
            closeSidebar();
        }
        // Close detail panel if it's open
        if (elements.detailPanel.classList.contains('active')) {
            hideDetailPanel();
        }
    });
    
    // Panel controls
    elements.closePanelBtn.addEventListener('click', handleClosePanelClick);
    
    // Chat input
    elements.chatInput.addEventListener('keypress', handleChatInput);
    elements.sendButton.addEventListener('click', sendMessage);
    
    // Tray chat input
    elements.trayChatInput.addEventListener('keypress', handleChatInput);
    elements.traySendButton.addEventListener('click', sendMessage);
    
    // Sync chat inputs
    elements.chatInput.addEventListener('input', (e) => {
        elements.trayChatInput.value = e.target.value;
    });
    
    elements.trayChatInput.addEventListener('input', (e) => {
        elements.chatInput.value = e.target.value;
    });
    
    // Escape key handling
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (window.innerWidth <= 768) {
                // Mobile: hide panel if active
                if (elements.detailPanel.classList.contains('active')) {
                    hideDetailPanel();
                }
            } else {
                // Desktop: exit fullscreen if active
                if (document.body.classList.contains('panel-fullscreen')) {
                    document.body.classList.remove('panel-fullscreen');
                }
            }
        }
    });
    
    // Panel content scroll detection for spacebar navigation
    elements.panelContent.addEventListener('scroll', () => {
        checkScrollEnd();
    });
    
    // Spacebar navigation when panel content has focus
    elements.panelContent.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Spacebar') {
            handleSpacebarNavigation(e);
        }
    });
    
    // Remove unreliable transition handling - scrolling happens in navigateToSection
}

function handleChatInput(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;
    
    // Clear inputs
    elements.chatInput.value = '';
    elements.trayChatInput.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Show typing indicator
    showTyping();
    
    // Process message (simulate for now)
    setTimeout(() => {
        processUserMessage(message);
    }, 1000);
}

function processUserMessage(message) {
    hideTyping();
    
    // Simple navigation intent detection for demo
    const lowerMessage = message.toLowerCase();
    
    // Check for navigation requests
    if (lowerMessage.includes('go to') || lowerMessage.includes('show') || lowerMessage.includes('navigate')) {
        // Search for matching sections
        const results = window.documentParser.searchContent(message);
        
        if (results.length > 0) {
            const result = results[0];
            if (result.type === 'section') {
                navigateToSection(result.sectionId);
            } else {
                // Find parent section for subsection
                const subsection = window.documentParser.getSection(result.sectionId);
                if (subsection && subsection.parentId) {
                    navigateToSection(subsection.parentId, result.sectionId);
                }
            }
            
            addMessage(`I've navigated to "${result.title}". This section covers ${result.preview}`, 'assistant');
            addArtifactToChat(result.title, result.type, result.sectionId);
        } else {
            addMessage("I couldn't find a section matching your request. Try being more specific or check the sidebar for available sections.", 'assistant');
        }
    } else {
        // General question - would integrate with LLM here
        addMessage("I understand you're asking about the document. In a full implementation, I would use the document content to provide a detailed answer. For now, try asking me to navigate to specific sections!", 'assistant');
    }
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = sender === 'user' ? 'You' : 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (sender === 'assistant') {
        // Parse markdown in assistant messages
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    // Remove welcome message if exists
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    elements.messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addArtifactToChat(title, type, sectionId) {
    const artifactDiv = document.createElement('div');
    artifactDiv.className = 'artifact-reference';
    artifactDiv.innerHTML = `
        <div class="artifact-icon">${type === 'section' ? '📑' : '📄'}</div>
        <div class="artifact-info">
            <div class="artifact-title">${title}</div>
            <div class="artifact-type">${type === 'section' ? 'Section' : 'Subsection'}</div>
        </div>
    `;
    
    artifactDiv.addEventListener('click', () => {
        if (type === 'section') {
            navigateToSection(sectionId);
        } else {
            // For subsections, find parent section
            const subsection = window.documentParser.getSection(sectionId);
            if (subsection && subsection.parentId) {
                navigateToSection(subsection.parentId, sectionId);
            }
        }
    });
    
    elements.messagesContainer.appendChild(artifactDiv);
    scrollToBottom();
}

function showTyping() {
    state.isTyping = true;
    elements.typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTyping() {
    state.isTyping = false;
    elements.typingIndicator.style.display = 'none';
}

function scrollToBottom() {
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function showDetailPanel() {
    elements.detailPanel.classList.add('active');
    if (window.innerWidth <= 768) {
        elements.mobileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function scrollToSubsection(subsectionId) {
    console.log('scrollToSubsection called with:', subsectionId);
    console.log('Panel content exists:', !!elements.panelContent);
    console.log('Panel content HTML length:', elements.panelContent.innerHTML.length);
    
    // Log all elements with IDs
    const allWithIds = elements.panelContent.querySelectorAll('[id]');
    console.log('All elements with IDs:', Array.from(allWithIds).map(el => ({
        tag: el.tagName,
        id: el.id,
        text: el.textContent.substring(0, 50)
    })));
    
    const element = elements.panelContent.querySelector(`#${subsectionId}`);
    if (element) {
        console.log('Found element:', element);
        console.log('Element position:', element.getBoundingClientRect());
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        console.log('Scroll command sent');
    } else {
        console.warn(`Could not find element with ID: ${subsectionId}`);
    }
}

function hideDetailPanel() {
    elements.detailPanel.classList.remove('active');
    elements.mobileOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

function closeSidebar() {
    elements.sidebar.classList.remove('active');
    elements.mobileOverlay.classList.remove('active');
}

function handleClosePanelClick() {
    if (window.innerWidth <= 768) {
        // Mobile: hide the panel
        hideDetailPanel();
    } else {
        // Desktop: toggle fullscreen
        const isFullscreen = document.body.classList.contains('panel-fullscreen');
        if (isFullscreen) {
            // Exit fullscreen
            document.body.classList.remove('panel-fullscreen');
        } else {
            // Enter fullscreen
            document.body.classList.add('panel-fullscreen');
        }
    }
}

// Check if at end of panel content
function checkScrollEnd() {
    const panel = elements.panelContent;
    const isAtEnd = panel.scrollHeight - panel.scrollTop <= panel.clientHeight + 10;
    elements.detailPanel.dataset.atEnd = isAtEnd;
}

// Handle spacebar navigation
function handleSpacebarNavigation(e) {
    const panel = elements.panelContent;
    const isAtEnd = panel.scrollHeight - panel.scrollTop <= panel.clientHeight + 10;
    
    if (isAtEnd) {
        // Move to next section
        e.preventDefault();
        const sections = window.documentParser.getMainSections();
        const currentIndex = sections.findIndex(s => s.id === state.currentSection);
        
        if (currentIndex >= 0 && currentIndex < sections.length - 1) {
            // Navigate to next section
            const nextSection = sections[currentIndex + 1];
            navigateToSection(nextSection.id);
            
            // Scroll to top of new section
            setTimeout(() => {
                elements.panelContent.scrollTop = 0;
            }, 50);
        }
    } else {
        // Let default spacebar scrolling work
        // No need to prevent default
    }
}

// Resizer functionality
function setupResizer() {
    if (window.innerWidth <= 768) return; // Skip on mobile
    
    // Set initial flex value for chat container
    elements.chatContainer.style.flex = '0 0 400px';
    
    let isResizing = false;
    let startX = 0;
    let startWidthChat = 0;
    let startWidthPanel = 0;
    
    elements.separatorVertical.addEventListener('mousedown', (e) => {
        if (window.innerWidth <= 768) return;
        
        isResizing = true;
        startX = e.clientX;
        startWidthChat = elements.chatContainer.offsetWidth;
        startWidthPanel = elements.detailPanel.offsetWidth;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const newChatWidth = startWidthChat + deltaX;
        const newPanelWidth = startWidthPanel - deltaX;
        
        // Enforce minimum width for chat (375px) and panel (300px)
        if (newChatWidth >= 375 && newPanelWidth >= 300) {
            elements.chatContainer.style.flex = `0 0 ${newChatWidth}px`;
            elements.detailPanel.style.width = `${newPanelWidth}px`;
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}