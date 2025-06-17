// Configuration
const CONFIG = {
    WORKER_URL: 'https://tech-writer-ai-proxy.julian-harris.workers.dev',
    MODEL: 'gemini-2.0-flash',
    MAX_TOKENS: 1024,
    TEMPERATURE: 0.0
};

// Tone profile constant
const TONE_PROFILE = `TONE OF VOICE PROFILE

Skeptical Optimism (Core Dimension):
Description: A foundational tone that approaches claims with healthy skepticism but maintains an underlying optimism about the potential of Vibe Coding and AI agents. It questions hype while looking for genuine value and practical applications.
Example from User: "truthful skeptical but optimistic."
Application: Critically evaluate tools and success stories, acknowledge limitations and potential pitfalls, but ultimately highlight the empowering aspects and future possibilities in a positive light.

Upbeat & Engaging:
Description: The overall energy should be positive, enthusiastic, and engaging, drawing the reader in rather than presenting information dryly.
Example from User: "more upbeat."
Application: Use active voice, varied sentence structure, and a generally positive framing, even when discussing complex or challenging topics.

Truthful & Accurate (Evidence-Based):
Description: All information, especially claims and technical descriptions, must be grounded in verifiable facts and evidence. Avoid making unsubstantiated statements.
Example from User: "still very truthful."
Application: Prioritize accuracy in describing tools, technologies, and case studies. Clearly distinguish between established facts, reported claims (with sources), and speculative future trends.

Slightly Sarcastic / Witty Humor:
Description: Incorporate occasional, subtle sarcasm or witty observations to add personality and make the content more relatable and entertaining. The humor should be intelligent and not overly broad or offensive.
Example from User: "slightly sarcastic, funny occasionally."
Application: Use sparingly in appropriate contexts, perhaps when commenting on industry hype, common misconceptions, or the quirks of technology. It should lighten the tone without undermining credibility.

Analytical & Discerning:
Description: A critical thinking approach that dissects information, compares and contrasts, and doesn't take claims at face value. This aligns with the "skeptical" aspect.
Application: When discussing tools, provide balanced comparisons. When analyzing case studies, look for underlying factors of success or failure, and question the generalizability of results.

Clear & Accessible (Non-Technical Focus):
Description: While the author is knowledgeable, the language must remain accessible to the target audience of non-technical people with business ideas. Avoid jargon where possible, or explain it clearly.
Application: Break down complex concepts into simpler terms. Use analogies or relatable examples. Focus on the implications and value for the reader, not just the technical details.

Direct & Experiential:
Description: The Substack conveys a sense of sharing direct experience and personal insights. The book should echo this by feeling authentic and based on real understanding, even if it's synthesizing broader research.
Application: Frame advice and analysis in a way that feels like it's coming from someone who has navigated this space. Use phrases that suggest firsthand knowledge or deep consideration.

Pragmatic & Action-Oriented:
Description: While analytical, the tone should also be practical, offering readers actionable insights and takeaways they can apply to their own ideas and projects.
Application: Conclude sections or chapters with clear summaries of key lessons or actionable steps. Focus on what the reader can do with the information.

Confident but Humble:
Description: The author's expertise should come through confidently, but without arrogance. Acknowledge the rapidly evolving nature of the field and the possibility of different perspectives.
Application: Present information with conviction where it's well-supported, but be open about areas of uncertainty or ongoing debate.

Conversational & Relatable:
Description: Avoid overly academic or formal language. The tone should feel more like an engaging conversation with a knowledgeable guide.
Application: Use contractions where appropriate. Address the reader directly at times (e.g., "you might find that..."). Incorporate rhetorical questions to stimulate thought.`;

// State management
const state = {
    currentSection: null,
    currentSubsection: null,
    chatHistory: [],
    documentContent: null,
    conversationHistory: [],
    isProcessing: false
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
    
    // Clear conversation history when new document is loaded
    state.conversationHistory = [];
    
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
    if (!message || state.isProcessing) return;
    
    state.isProcessing = true;
    elements.sendButton.disabled = true;
    elements.traySendButton.disabled = true;
    
    // Clear inputs
    elements.chatInput.value = '';
    elements.trayChatInput.value = '';
    
    // Add user message
    addMessage(message, 'user');
    
    // Show typing indicator
    showTyping();
    
    // Process message with LLM
    try {
        const response = await processUserMessage(message);
        hideTyping();
        
        // Check if response contains tool calls
        if (response.toolCall) {
            handleToolCall(response.toolCall);
            // Add any additional text from the response
            if (response.text) {
                addMessage(response.text, 'assistant');
            }
        } else {
            addMessage(response.text, 'assistant');
        }
        
        // Update conversation history
        state.conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: response.text || `Navigated to section` }
        );
    } catch (error) {
        hideTyping();
        addMessage(`I apologize, but I encountered an error: ${error.message}`, 'assistant');
        console.error('Chat error:', error);
    } finally {
        state.isProcessing = false;
        elements.sendButton.disabled = false;
        elements.traySendButton.disabled = false;
        elements.chatInput.focus();
    }
}

async function processUserMessage(message) {
    // Build conversation contents for LLM
    const contents = buildContents(message);
    
    try {
        // Call LLM API
        const responseData = await callGeminiAPI(contents);
        
        // Parse response for tool calls
        const parsedResponse = parseAssistantResponse(responseData);
        
        return parsedResponse;
    } catch (error) {
        throw error;
    }
}

function buildCompactHierarchy() {
    if (!window.documentParser || !window.documentParser.sections) {
        return "No sections available";
    }
    
    let hierarchy = "";
    window.documentParser.sections.forEach((section, index) => {
        if (index > 0) hierarchy += "; ";
        hierarchy += section.title;
        if (section.subsections.length > 0) {
            hierarchy += ` (${section.subsections.map(sub => sub.title).join(', ')})`;
        }
    });
    
    return hierarchy;
}

function buildToolDefinitions() {
    if (!window.documentParser || !window.documentParser.sections) {
        return [];
    }
    
    // Build structured hierarchy
    const sections = window.documentParser.sections.map(s => ({
        name: s.title,
        subsections: s.subsections.map(sub => sub.title)
    }));
    
    // Generate clear description listing all sections and their subsections
    const sectionDescriptions = sections.map(s => {
        if (s.subsections.length > 0) {
            return `${s.name} (subsections: ${s.subsections.join(', ')})`;
        }
        return s.name;
    }).join('; ');
    
    // Extract just the section names for the enum
    const sectionNames = sections.map(s => s.name);
    
    // Extract all unique subsection names for the enum
    const allSubsections = sections.flatMap(s => s.subsections);
    const uniqueSubsections = [...new Set(allSubsections)];
    
    return [{
        function_declarations: [{
            name: "navigate_to_section",
            description: `When user asks about content related to these sections, navigate there instead of describing it. Available sections: ${sectionDescriptions}`,
            parameters: {
                type: "object",
                properties: {
                    section: {
                        type: "string",
                        description: "The main section name",
                        enum: sectionNames
                    },
                    subsection: {
                        type: "string",
                        description: "The subsection name within the main section (optional). Only provide if user asks about specific subsection content. Must be a valid subsection under the chosen section.",
                        enum: uniqueSubsections.length > 0 ? uniqueSubsections : undefined
                    }
                },
                required: ["section"]
            }
        }]
    }];
}

function buildContents(currentMessage) {
    const contents = [];
    
    // Build system prompt
    const systemPrompt = buildSystemPrompt();
    
    // Always include system prompt at the beginning
    contents.push({
        role: "user",
        parts: [{ text: systemPrompt }]
    });
    contents.push({
        role: "model", 
        parts: [{ text: "I understand. I'm ready to help you navigate and understand this document. I can answer questions about its content and help you find specific sections." }]
    });
    
    // Add conversation history
    state.conversationHistory.forEach(msg => {
        contents.push({
            role: msg.role === 'user' ? 'user' : 'model',
            parts: [{ text: msg.content }]
        });
    });
    
    // Add current message
    contents.push({
        role: "user",
        parts: [{ text: currentMessage }]
    });
    
    return contents;
}

function buildSystemPrompt() {
    let prompt = `You are a helpful AI assistant that helps users navigate and understand the report.
    You respond in a tone of voice profile as defined below. Your answers should be accurate, concise, and helpful.

<report>
${state.documentContent || 'No document loaded yet.'}
</report>

<available-sections>
`;
    
    // Add available sections for navigation
    if (window.documentParser) {
        const sections = window.documentParser.sections;
        sections.forEach(section => {
            prompt += `- ${section.title} (id: ${section.id})`;
            if (section.subsections.length > 0) {
                prompt += '\n  Subsections:';
                section.subsections.forEach(sub => {
                    prompt += `\n    - ${sub.title} (id: ${sub.id})`;
                });
            }
            prompt += '\n';
        });
    }
    
    prompt += `</available-sections>

<tone-profile>
${TONE_PROFILE}
</tone-profile>

Remember: 
- Base your answers on the document content provided above
- Be helpful in navigating the document
- Keep responses concise and relevant
- When users ask about specific topics that are covered in the sections, jump to that section instead of responding with a message`;
    
    return prompt;
}

async function callGeminiAPI(contents) {
    const tools = buildToolDefinitions();
    
    console.log('Calling Gemini API with tools:', JSON.stringify(tools, null, 2));
    
    const response = await fetch(CONFIG.WORKER_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: CONFIG.MODEL,
            contents: contents,
            tools: tools,
            generationConfig: {
                temperature: CONFIG.TEMPERATURE,
                maxOutputTokens: CONFIG.MAX_TOKENS
            }
        })
    });

    const data = await response.json();
    
    console.log('Gemini API response:', JSON.stringify(data, null, 2));
    
    // Check if the response contains an error
    if (data.error) {
        if (data.error.code === 503 || data.error.status === 'UNAVAILABLE') {
            throw new Error('The AI model is currently overloaded. Please try again in a few moments.');
        } else if (data.error.code === 429) {
            throw new Error('Too many requests. Please wait a moment before trying again.');
        } else if (data.error.message) {
            throw new Error(data.error.message);
        } else {
            throw new Error('An unexpected error occurred. Please try again.');
        }
    }
    
    // Return the full response data for parsing
    return data;
}

function parseAssistantResponse(responseData) {
    console.log('Parsing assistant response...');
    
    // Check if the response has the expected structure
    if (!responseData.candidates || !responseData.candidates[0] || !responseData.candidates[0].content) {
        console.error('Invalid response structure:', responseData);
        throw new Error('Invalid response format from AI model');
    }
    
    const content = responseData.candidates[0].content;
    console.log('Response content:', JSON.stringify(content, null, 2));
    
    // Check if it's a function call response
    if (content.parts && content.parts[0] && content.parts[0].functionCall) {
        const functionCall = content.parts[0].functionCall;
        console.log('Function call detected:', functionCall);
        return {
            toolCall: {
                tool: functionCall.name,
                section: functionCall.args.section,
                subsection: functionCall.args.subsection
            },
            text: "" // Gemini doesn't return text with function calls
        };
    }
    
    // Regular text response
    if (content.parts && content.parts[0] && content.parts[0].text) {
        console.log('Text response detected');
        return { text: content.parts[0].text };
    }
    
    console.error('No valid content found in response');
    throw new Error('No valid content in response');
}

function handleToolCall(toolCall) {
    console.log('Handling tool call:', toolCall);
    
    if (toolCall.tool === 'navigate_to_section') {
        const { section: sectionName, subsection: subsectionName } = toolCall;
        console.log(`Looking for section: "${sectionName}", subsection: "${subsectionName}"`);
        
        // Find matching section by name (case-insensitive)
        const sectionObj = window.documentParser.sections.find(
            s => s.title.toLowerCase() === sectionName.toLowerCase()
        );
        
        if (!sectionObj) {
            console.error('Section not found:', sectionName);
            addMessage(`I couldn't find the section "${sectionName}". Please check the section name and try again.`, 'assistant');
            return;
        }
        
        if (subsectionName) {
            // User wants to navigate to a subsection
            const subsectionObj = sectionObj.subsections.find(
                sub => sub.title.toLowerCase() === subsectionName.toLowerCase()
            );
            
            if (subsectionObj) {
                console.log('Navigating to subsection:', subsectionObj.id, 'in section:', sectionObj.id);
                navigateToSection(sectionObj.id, subsectionObj.id);
                addArtifactToChat(`${sectionObj.title} > ${subsectionObj.title}`, 'subsection', subsectionObj.id);
            } else {
                // Subsection not found, fallback to main section
                console.log('Subsection not found, falling back to main section');
                navigateToSection(sectionObj.id);
                addArtifactToChat(sectionObj.title, 'section', sectionObj.id);
                addMessage(`I couldn't find the subsection "${subsectionName}" in ${sectionName}, so I'm showing the main section.`, 'assistant');
            }
        } else {
            // Navigate to main section only
            console.log('Navigating to main section:', sectionObj.id);
            navigateToSection(sectionObj.id);
            addArtifactToChat(sectionObj.title, 'section', sectionObj.id);
        }
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
    elements.typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTyping() {
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
    const element = elements.panelContent.querySelector(`#${subsectionId}`);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
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