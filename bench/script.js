// State management
const state = {
    currentView: 'overview',
    currentFramework: null,
    chatHistory: [],
    isTyping: false
};

// DOM elements
const elements = {
    sidebar: null,
    hamburgerBtn: null,
    closeSidebar: null,
    frameworkList: null,
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
    chatTitle: null,
    chatSubtitle: null,
    trayChatInput: null,
    traySendButton: null,
    separatorVertical: null,
    fullscreenBtn: null,
    chatContainer: null
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    renderFrameworkList();
    setupEventListeners();
    setupQuickActions();
    setupResizer();
    
    // Focus on chat input
    elements.chatInput.focus();
    
    // Show overview report in detail panel
    showOverviewReport();
});

function initializeElements() {
    // Cache DOM elements
    elements.sidebar = document.getElementById('sidebar');
    elements.hamburgerBtn = document.getElementById('hamburgerBtn');
    elements.closeSidebar = document.getElementById('closeSidebar');
    elements.frameworkList = document.getElementById('frameworkList');
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
    elements.chatTitle = document.getElementById('chatTitle');
    elements.chatSubtitle = document.getElementById('chatSubtitle');
    elements.trayChatInput = document.getElementById('trayChatInput');
    elements.traySendButton = document.getElementById('traySendButton');
    elements.separatorVertical = document.getElementById('separatorVertical');
    elements.fullscreenBtn = document.getElementById('fullscreenBtn');
    elements.chatContainer = document.querySelector('.chat-container');
}

function renderFrameworkList() {
    elements.frameworkList.innerHTML = frameworks.map(framework => `
        <button class="nav-item" data-framework="${framework}">
            <span class="nav-icon">${getFrameworkIcon(framework)}</span>
            ${framework}
        </button>
    `).join('');
}

function getFrameworkIcon(framework) {
    // Return appropriate icon based on framework
    const iconMap = {
        'No framework': '📝',
        'langgraph': '📊',
        'pydantic-ai': '🔒',
        'dspy': '🧪',
        'crewai': '👥',
        'autogen': '🤖',
        'langflow': '🌊',
        'flowise': '🌸'
    };
    return iconMap[framework] || '📦';
}

function setupEventListeners() {
    // Mobile menu toggles
    elements.hamburgerBtn.addEventListener('click', () => {
        elements.sidebar.classList.add('active');
        elements.mobileOverlay.classList.add('active');
    });

    elements.closeSidebar.addEventListener('click', closeMobileMenu);
    elements.mobileOverlay.addEventListener('click', closeMobileMenu);

    // Framework selection
    elements.frameworkList.addEventListener('click', (e) => {
        const navItem = e.target.closest('.nav-item');
        if (navItem) {
            selectFramework(navItem.dataset.framework);
            closeMobileMenu();
        }
    });

    // Overview selection
    document.querySelector('[data-framework="overview"]').addEventListener('click', () => {
        selectFramework('overview');
        closeMobileMenu();
    });

    // Chat functionality
    elements.sendButton.addEventListener('click', sendMessage);
    elements.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Tray chat functionality
    elements.traySendButton.addEventListener('click', sendMessage);
    elements.trayChatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Sync input values between main and tray
    elements.chatInput.addEventListener('input', (e) => {
        elements.trayChatInput.value = e.target.value;
    });

    elements.trayChatInput.addEventListener('input', (e) => {
        elements.chatInput.value = e.target.value;
    });

    // Detail panel
    elements.closePanelBtn.addEventListener('click', () => {
        // If in fullscreen, just exit fullscreen, otherwise close panel
        if (elements.detailPanel.classList.contains('fullscreen')) {
            toggleFullscreen();
        } else {
            closeDetailPanel();
        }
    });
    elements.fullscreenBtn.addEventListener('click', toggleFullscreen);

    // Close panel on mobile overlay click
    elements.mobileOverlay.addEventListener('click', closeDetailPanel);

    // Close panel when clicking outside on mobile only
    document.addEventListener('click', (e) => {
        // Only close on mobile when it's a tray
        if (window.innerWidth <= 768 &&
            elements.detailPanel.classList.contains('active') &&
            !elements.detailPanel.contains(e.target) &&
            !e.target.closest('.artifact-preview')) {
            closeDetailPanel();
        }
    });
    
    // Close panel on Escape key (mobile only)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && 
            window.innerWidth <= 768 && 
            elements.detailPanel.classList.contains('active')) {
            closeDetailPanel();
        }
    });
}

function setupQuickActions() {
    elements.quickActions.addEventListener('click', (e) => {
        const btn = e.target.closest('.quick-action-btn');
        if (btn) {
            handleQuickAction(btn.dataset.action);
        }
    });
}

function closeMobileMenu() {
    elements.sidebar.classList.remove('active');
    elements.mobileOverlay.classList.remove('active');
}

function closeDetailPanel() {
    elements.detailPanel.classList.remove('active');
    elements.mobileOverlay.classList.remove('active');
    elements.separatorVertical.classList.remove('active');
    
    // Restore focus to main input on mobile
    if (window.innerWidth <= 768) {
        setTimeout(() => {
            elements.chatInput.focus();
        }, 300); // Wait for animation to complete
    }
}

function selectFramework(framework) {
    // Update state
    state.currentFramework = framework === 'overview' ? null : framework;
    state.currentView = framework;

    // Update UI
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.framework === framework);
    });

    // Update chat header
    if (framework === 'overview') {
        elements.chatTitle.textContent = 'Tech Writer Benchmark Overview';
        elements.chatSubtitle.textContent = 'Explore implementations across frameworks';
    } else {
        elements.chatTitle.textContent = `${framework} Implementation`;
        elements.chatSubtitle.textContent = 'Explore this framework\'s approach';
    }

    // Update quick actions
    updateQuickActions(framework);

    // Clear welcome message if needed
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add system message about selection
    addMessage(`Now viewing: **${framework}**`, 'assistant');

    // Show appropriate content in detail panel
    if (framework === 'overview') {
        showOverviewReport();
    } else {
        showFrameworkCode(framework);
    }
}

function updateQuickActions(framework) {
    let actions, labels;
    
    if (framework === 'overview') {
        actions = ['summary', 'leaderboard', 'method', 'future'];
        labels = {
            'summary': 'Summary',
            'leaderboard': 'Leaderboard',
            'method': 'Method',
            'future': 'Future'
        };
    } else {
        actions = ['summary', 'llms', 'tools', 'memory', 'other'];
        labels = {
            'summary': 'Summary',
            'llms': 'LLMs',
            'tools': 'Tools',
            'memory': 'Memory',
            'other': 'Other'
        };
    }

    elements.quickActions.innerHTML = actions.map(action => `
        <button class="quick-action-btn" data-action="${action}">
            ${labels[action]}
        </button>
    `).join('');
}

function handleQuickAction(action) {
    // Clear welcome message if present
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Get appropriate response
    let response;
    let userMessage;
    
    if (state.currentView === 'overview') {
        response = overviewResponses[action];
        // Overview-specific messages
        const overviewMessages = {
            'summary': 'Show me a summary of the Tech Writer benchmark results',
            'leaderboard': 'Show the framework leaderboard and performance comparison',
            'method': 'Explain the benchmark methodology and evaluation criteria',
            'future': 'What are the future directions for this benchmark?'
        };
        userMessage = overviewMessages[action] || `Show ${action}`;
    } else {
        const frameworkInfo = frameworkData[state.currentView];
        response = frameworkInfo ? frameworkInfo[action] : 'Information not available yet.';
        
        // Framework-specific messages
        const frameworkMessages = {
            'summary': `Tell me about ${state.currentView}'s approach to building AI agents`,
            'llms': `Show how ${state.currentView} handles LLM integration and management`,
            'tools': `Explain ${state.currentView}'s tool and function calling capabilities`,
            'memory': `Show how ${state.currentView} manages agent memory and state`,
            'other': `What are the unique features and characteristics of ${state.currentView}?`
        };
        userMessage = frameworkMessages[action] || `Show ${action} for ${state.currentView}`;
    }

    // Add user message
    addMessage(userMessage, 'user');

    // Simulate typing
    showTyping();
    setTimeout(() => {
        hideTyping();
        
        // Check if this should be an artifact
        // For overview: summary and leaderboard are artifacts
        // For frameworks: all actions create artifacts
        const shouldBeArtifact = (state.currentView === 'overview' && (action === 'summary' || action === 'leaderboard')) ||
                                (state.currentView !== 'overview');
        
        if (shouldBeArtifact) {
            // Determine the artifact title based on context
            let artifactTitle;
            if (state.currentView === 'overview') {
                artifactTitle = `${action.charAt(0).toUpperCase() + action.slice(1)} Report`;
            } else {
                const titleMap = {
                    'summary': `${state.currentView} Overview`,
                    'llms': `${state.currentView} LLM Integration`,
                    'tools': `${state.currentView} Tool System`,
                    'memory': `${state.currentView} Memory Management`,
                    'other': `${state.currentView} Unique Features`
                };
                artifactTitle = titleMap[action] || `${state.currentView} ${action.charAt(0).toUpperCase() + action.slice(1)}`;
            }
            
            addArtifact({
                title: artifactTitle,
                summary: response.split('\n')[0].replace(/^#+\s*/, ''),
                fullContent: response
            });
        } else {
            addMessage(response, 'assistant');
        }
    }, 1000);
}

function showOverviewReport() {
    // Combine all overview sections into a comprehensive report
    const fullReport = `
        <div class="overview-report">
            <h2>Tech Writer Benchmark Report</h2>
            
            <section class="report-section">
                ${formatMessage(overviewResponses.summary)}
            </section>
            
            <section class="report-section">
                ${formatMessage(overviewResponses.leaderboard)}
            </section>
            
            <section class="report-section">
                ${formatMessage(overviewResponses.method)}
            </section>
            
            <section class="report-section">
                ${formatMessage(overviewResponses.future)}
            </section>
        </div>
    `;
    
    elements.panelContent.innerHTML = fullReport;
    elements.panelTitle.textContent = 'Full Benchmark Report';
    
    // Show panel
    elements.detailPanel.classList.add('active');
    
    // Show separator on desktop
    if (window.innerWidth > 768) {
        elements.separatorVertical.classList.add('active');
    }
    
    // On mobile, show overlay and focus tray input
    if (window.innerWidth <= 768) {
        elements.mobileOverlay.classList.add('active');
        // Small delay to ensure animation has started
        setTimeout(() => {
            elements.trayChatInput.focus();
        }, 100);
    }
}

function showFrameworkCode(framework) {
    const frameworkInfo = frameworkData[framework];
    if (!frameworkInfo) return;

    const codeContent = `
        <div class="code-container">
            <div class="code-header">${framework} - tech_writer.py</div>
            <div class="code-content">
                <pre><code class="language-python">${escapeHtml(frameworkInfo.code)}</code></pre>
            </div>
        </div>
    `;

    elements.panelContent.innerHTML = codeContent;
    elements.panelTitle.textContent = `${framework} Code`;
    
    // Apply syntax highlighting
    elements.panelContent.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
        hljs.lineNumbersBlock(block);
    });

    // Show panel
    elements.detailPanel.classList.add('active');
    
    // Show separator on desktop
    if (window.innerWidth > 768) {
        elements.separatorVertical.classList.add('active');
    }
    
    // On mobile, show overlay and focus tray input
    if (window.innerWidth <= 768) {
        elements.mobileOverlay.classList.add('active');
        // Small delay to ensure animation has started
        setTimeout(() => {
            elements.trayChatInput.focus();
        }, 100);
    }
}

function sendMessage() {
    // Get message from whichever input is active
    const message = (document.activeElement === elements.trayChatInput 
        ? elements.trayChatInput.value 
        : elements.chatInput.value).trim();
    
    if (!message || state.isTyping) return;

    // Clear welcome message
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message
    addMessage(message, 'user');
    
    // Clear both inputs
    elements.chatInput.value = '';
    elements.trayChatInput.value = '';

    // Process message
    processUserMessage(message);
}

function processUserMessage(message) {
    showTyping();

    setTimeout(() => {
        hideTyping();

        // Check for predefined responses
        let response = chatResponses[message];

        if (!response) {
            // Generate contextual response
            response = generateResponse(message);
        }

        // Determine if this should be an artifact
        const lowerMessage = message.toLowerCase();
        let shouldBeArtifact = false;
        let artifactTitle = '';
        
        // Comparisons become artifacts
        if (lowerMessage.includes('compare') && message.includes(' vs ')) {
            shouldBeArtifact = true;
            artifactTitle = 'Framework Comparison';
        }
        // Framework-specific detailed questions become artifacts
        else if (state.currentView !== 'overview' && 
                (lowerMessage.includes('how') || lowerMessage.includes('explain') || 
                 lowerMessage.includes('show') || lowerMessage.includes('detail'))) {
            shouldBeArtifact = true;
            artifactTitle = `${state.currentView} Details`;
        }
        // Overview reports
        else if (state.currentView === 'overview' && 
                (lowerMessage.includes('report') || lowerMessage.includes('summary') || 
                 lowerMessage.includes('leaderboard'))) {
            shouldBeArtifact = true;
            artifactTitle = 'Benchmark Report';
        }
        
        if (shouldBeArtifact) {
            addArtifact({
                title: artifactTitle,
                summary: response.split('\n')[0].replace(/^#+\s*/, ''),
                fullContent: response
            });
        } else {
            addMessage(response, 'assistant');
        }
    }, 1500);
}

function generateResponse(message) {
    const lowerMessage = message.toLowerCase();

    // Context-aware responses
    if (state.currentView !== 'overview') {
        const framework = state.currentView;
        
        if (lowerMessage.includes('example') || lowerMessage.includes('code')) {
            return `Here's a code example for ${framework}. Click the code panel on the right (or bottom on mobile) to see the full implementation.`;
        }
        
        if (lowerMessage.includes('pros') || lowerMessage.includes('cons')) {
            const data = frameworkData[framework];
            return data ? data.summary : `${framework} provides a comprehensive solution for building AI agents.`;
        }
    }

    // General responses
    if (lowerMessage.includes('best')) {
        return 'The "best" framework depends on your specific needs. LangGraph excels at complex workflows, Pydantic-AI offers great type safety, and "No framework" provides maximum control with minimal dependencies.';
    }

    if (lowerMessage.includes('how many')) {
        return 'The benchmark includes 51 implementations: 50 open-source frameworks plus a "No framework" baseline implementation.';
    }

    return 'I can help you explore the Tech Writer benchmark results. Try asking about specific frameworks, comparisons, or use the quick action buttons above!';
}

function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(content);
    
    messageDiv.appendChild(contentDiv);
    elements.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    
    // Add to history
    state.chatHistory.push({ content, role, timestamp: new Date() });
}

function addArtifact(artifact) {
    const artifactDiv = document.createElement('div');
    artifactDiv.className = 'message assistant';
    
    const preview = document.createElement('div');
    preview.className = 'artifact-preview';
    preview.innerHTML = `
        <h4>${artifact.title}</h4>
        <p>${artifact.summary}</p>
        <div class="artifact-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            Click to view full content
        </div>
    `;
    
    preview.addEventListener('click', () => {
        showArtifactContent(artifact);
    });
    
    artifactDiv.appendChild(preview);
    elements.messagesContainer.appendChild(artifactDiv);
    
    // Scroll to bottom
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    
    // Automatically open the artifact with a small delay for smooth animation
    setTimeout(() => {
        showArtifactContent(artifact);
    }, 100);
}

function showArtifactContent(artifact) {
    elements.panelContent.innerHTML = `
        <div class="artifact-full">
            <h2>${artifact.title}</h2>
            <div class="artifact-body">${formatMessage(artifact.fullContent)}</div>
        </div>
    `;
    
    elements.detailPanel.classList.add('active');
    
    // Show separator on desktop
    if (window.innerWidth > 768) {
        elements.separatorVertical.classList.add('active');
    }
    
    // On mobile, show overlay
    if (window.innerWidth <= 768) {
        elements.mobileOverlay.classList.add('active');
    }
}

function showTyping() {
    state.isTyping = true;
    elements.typingIndicator.classList.add('active');
    elements.sendButton.disabled = true;
}

function hideTyping() {
    state.isTyping = false;
    elements.typingIndicator.classList.remove('active');
    elements.sendButton.disabled = false;
    elements.chatInput.focus();
}

function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^###\s+(.*)$/gm, '<h4>$1</h4>')
        .replace(/^##\s+(.*)$/gm, '<h3>$1</h3>')
        .replace(/^#\s+(.*)$/gm, '<h2>$1</h2>')
        .replace(/^-\s+(.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/```python\n([\s\S]*?)```/g, '<pre><code class="language-python">$1</code></pre>')
        .replace(/```\n([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Additional styles for artifacts
const style = document.createElement('style');
style.textContent = `
.artifact-full {
    padding: 0;
}

.artifact-full h2 {
    margin-bottom: 1.5rem;
    color: var(--accent-color);
}

.artifact-body {
    line-height: 1.8;
}

.artifact-body h3 {
    margin: 1.5rem 0 1rem 0;
    color: var(--accent-color);
}

.artifact-body h4 {
    margin: 1rem 0 0.5rem 0;
}

.artifact-body ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.artifact-body li {
    margin: 0.25rem 0;
}

.artifact-body code {
    background: var(--bg-tertiary);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.875rem;
}

.artifact-body pre {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1rem 0;
}

.artifact-body pre code {
    background: none;
    padding: 0;
}

/* Overview report styles */
.overview-report {
    padding: 0;
}

.overview-report h2 {
    margin-bottom: 2rem;
    color: var(--accent-color);
    font-size: 1.75rem;
}

.report-section {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid var(--border-color);
}

.report-section:last-child {
    border-bottom: none;
}

.report-section h3 {
    color: var(--accent-color);
    margin: 1.5rem 0 1rem 0;
}

.report-section h4 {
    margin: 1rem 0 0.5rem 0;
}

.report-section ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.report-section li {
    margin: 0.5rem 0;
    line-height: 1.6;
}

.report-section strong {
    color: var(--text-primary);
}

.report-section code {
    background: var(--bg-tertiary);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.875rem;
}
`;
document.head.appendChild(style);

// Setup resizer for desktop
function setupResizer() {
    if (window.innerWidth <= 768) return; // Skip on mobile
    
    // Mark as setup to avoid duplicate event listeners
    if (elements.separatorVertical.hasAttribute('data-resizer-setup')) return;
    elements.separatorVertical.setAttribute('data-resizer-setup', 'true');
    
    let isResizing = false;
    let startX = 0;
    let startWidthChat = 0;
    let startWidthPanel = 0;
    
    elements.separatorVertical.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidthChat = elements.chatContainer.offsetWidth;
        startWidthPanel = elements.detailPanel.offsetWidth;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none'; // Prevent text selection during drag
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
            document.body.style.cursor = 'default';
            document.body.style.userSelect = ''; // Restore text selection
        }
    });
}

// Toggle fullscreen mode
function toggleFullscreen() {
    const isFullscreen = elements.detailPanel.classList.contains('fullscreen');
    
    if (isFullscreen) {
        // Exit fullscreen
        elements.detailPanel.classList.remove('fullscreen');
        document.body.classList.remove('fullscreen-active');
        
        // Restore separator visibility if it was active
        if (window.innerWidth > 768) {
            elements.separatorVertical.classList.add('active');
        }
    } else {
        // Enter fullscreen
        elements.detailPanel.classList.add('fullscreen');
        document.body.classList.add('fullscreen-active');
        
        // Hide separator in fullscreen
        elements.separatorVertical.classList.remove('active');
    }
}

// Update escape key handler to include fullscreen
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Check for fullscreen first
        if (elements.detailPanel.classList.contains('fullscreen')) {
            toggleFullscreen();
        } else if (window.innerWidth <= 768 && elements.detailPanel.classList.contains('active')) {
            // Then check for mobile tray
            closeDetailPanel();
        }
    }
});

// Update panel visibility on window resize
window.addEventListener('resize', () => {
    // Update separator visibility
    if (window.innerWidth > 768 && elements.detailPanel.classList.contains('active')) {
        elements.separatorVertical.classList.add('active');
    } else {
        elements.separatorVertical.classList.remove('active');
    }
    
    // Re-setup resizer if switching to desktop
    if (window.innerWidth > 768 && !elements.separatorVertical.hasAttribute('data-resizer-setup')) {
        setupResizer();
    }
});