/**
 * Generate a short label for a section heading using the pattern learned from DSPy.
 * This replaces the manual metadata hack of using parentheses in headings.
 */
export function generateQuickActionLabel(heading) {
    // Examples learned from the training data
    const examples = [
    {
        "heading": "Tech Writer Agent in 7 different frameworks",
        "label": "Overview"
    },
    {
        "heading": "But first, how many agent maker frameworks are there?",
        "label": "Agent Landscape"
    },
    {
        "heading": "Why did you pick the tech writer agent for evaluation?",
        "label": "Tech Writer Choice"
    },
    {
        "heading": "What did I learn?",
        "label": "Insights"
    },
    {
        "heading": "What did I standardise on?",
        "label": "Shared Code"
    },
    {
        "heading": "How did I rank them?",
        "label": "Leaderboard"
    },
    {
        "heading": "Google Agent Developer Kit",
        "label": "adk-python"
    },
    {
        "heading": "Other python agent maker frameworks",
        "label": "Other Packages"
    },
    {
        "heading": "Other python agent makers",
        "label": "Python Servers"
    },
    {
        "heading": "TypeScript agent makers",
        "label": "TypeScript Agents"
    }
];
    
    // Simple pattern matching based on examples
    const headingLower = heading.toLowerCase();
    
    // Check for direct matches
    for (const example of examples) {
        if (example.heading.toLowerCase() === headingLower) {
            return example.label;
        }
    }
    
    // Apply learned patterns
    if (headingLower.includes('introduction')) return 'Introduction';
    if (headingLower.includes('getting started')) return 'Getting Started';
    if (headingLower.includes('overview')) return 'Overview';
    if (headingLower.includes('configuration') || headingLower.includes('config')) return 'Configuration';
    if (headingLower.includes('installation') || headingLower.includes('install')) return 'Installation';
    if (headingLower.includes('api')) return 'API Reference';
    if (headingLower.includes('authentication') || headingLower.includes('auth')) return 'Authentication';
    if (headingLower.includes('examples')) return 'Examples';
    if (headingLower.includes('troubleshoot')) return 'Troubleshooting';
    if (headingLower.includes('faq') || headingLower.includes('questions')) return 'FAQ';
    if (headingLower.includes('guide')) return 'Guide';
    if (headingLower.includes('reference')) return 'Reference';
    
    // Framework-specific patterns
    if (headingLower.includes('typescript')) return 'TypeScript';
    if (headingLower.includes('python')) return 'Python';
    if (headingLower.includes('javascript') || headingLower.includes('js')) return 'JavaScript';
    
    // Question patterns
    if (headingLower.startsWith('what')) return heading.split(' ').slice(0, 2).join(' ');
    if (headingLower.startsWith('how')) return heading.split(' ').slice(0, 2).join(' ');
    if (headingLower.startsWith('why')) return heading.split(' ').slice(0, 2).join(' ');
    
    // Fallback: Take first 2-3 significant words
    const words = heading.split(' ')
        .filter(w => w.length > 2 && !['the', 'and', 'for', 'with', 'from'].includes(w.toLowerCase()));
    
    if (words.length <= 2) {
        return words.join(' ');
    } else if (words.length === 3) {
        return words.join(' ');
    } else {
        return words.slice(0, 2).join(' ');
    }
}

/**
 * Alternative: Use with an LLM API for more sophisticated generation
 */
export async function generateQuickActionLabelWithLLM(heading, apiClient) {
    const prompt = `Generate a short 1-3 word label for this section heading that will be used as a quick action button.

Examples:
- "Tech Writer Agent in 7 different frameworks" -> "Overview"
- "But first, how many agent maker frameworks are there?" -> "Agent Landscape"
- "Why did you pick the tech writer agent for evaluation?" -> "Tech Writer Choice"
- "What did I learn?" -> "Insights"

Heading: "${heading}"
Label:`;
    
    const response = await apiClient.complete(prompt);
    return response.trim();
}
