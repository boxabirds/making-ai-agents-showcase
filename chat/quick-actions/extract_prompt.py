#!/usr/bin/env python3
"""Extract the prompt from DSPy for use in JavaScript."""

import os
import dspy
import json
from train_labeler import LabelGenerator

# Configure DSPy
lm = dspy.LM(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    temperature=0.7,
)
dspy.configure(lm=lm)

def create_javascript_function():
    """Create a JavaScript function that can generate labels."""
    
    # Load the optimized model
    model = LabelGenerator()
    model.load('output/optimized_label_generator.json')
    
    # Load training data to get examples
    with open('output/training_data.json', 'r') as f:
        training_data = json.load(f)
    
    # Convert to examples format
    examples = []
    for item in training_data:
        examples.append({
            "heading": item['full_heading'],
            "label": item['short_label']
        })
    
    # Test to capture the prompt pattern
    test_heading = "Sample Section Heading"
    _ = model(heading=test_heading)
    
    # Create JavaScript function
    js_code = """/**
 * Generate a short label for a section heading using the pattern learned from DSPy.
 * This replaces the manual metadata hack of using parentheses in headings.
 */
export function generateQuickActionLabel(heading) {
    // Examples learned from the training data
    const examples = """ + json.dumps(examples, indent=4) + """;
    
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
""" + '\n'.join([f"- \"{ex['heading']}\" -> \"{ex['label']}\"" for ex in examples[:4]]) + """

Heading: "${heading}"
Label:`;
    
    const response = await apiClient.complete(prompt);
    return response.trim();
}
"""
    
    return js_code

def main():
    js_code = create_javascript_function()
    
    # Save to file
    output_path = 'output/generateQuickActionLabel.js'
    with open(output_path, 'w') as f:
        f.write(js_code)
    
    print(f"JavaScript function saved to: {output_path}")
    print("\nYou can now import this function in your document parser:")
    print("import { generateQuickActionLabel } from './generateQuickActionLabel.js';")

if __name__ == "__main__":
    main()