#!/usr/bin/env python3
"""Extract the exact DSPy prompt format for use in JavaScript."""

import os
import json
import dspy
from train_labeler import LabelGenerator

# Configure DSPy
lm = dspy.LM(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    temperature=0.7,
)
dspy.configure(lm=lm)

def extract_exact_prompt():
    """Extract the exact prompt format used by DSPy."""
    
    # Load the optimized model
    model = LabelGenerator()
    model.load('output/optimized_label_generator.json')
    
    # Run a test to capture the exact prompt
    test_heading = "Sample Section Heading"
    _ = model(heading=test_heading)
    
    # Get the last history item
    if hasattr(lm, 'history') and lm.history:
        last_item = lm.history[-1]
        
        # Extract the exact messages
        messages = last_item.get('messages', [])
        
        # Build the exact prompt structure
        system_prompt = None
        examples = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user' and 'This is an example' in msg.get('content', ''):
                # Extract example heading
                content = msg['content']
                heading_start = content.find('[[ ## heading ## ]]')
                if heading_start >= 0:
                    heading_text = content[heading_start:].split('\n')[1].strip()
                    examples.append({'type': 'user', 'heading': heading_text})
            elif msg['role'] == 'assistant' and '[[ ## label ## ]]' in msg.get('content', ''):
                # Extract example label
                content = msg['content']
                label_start = content.find('[[ ## label ## ]]')
                if label_start >= 0:
                    label_text = content[label_start:].split('\n')[1].strip()
                    if examples and examples[-1]['type'] == 'user':
                        examples[-1]['label'] = label_text
                        examples[-1]['type'] = 'complete'
        
        # Create JavaScript-friendly version
        js_code = """/**
 * Exact DSPy prompt format for generating quick action labels
 * This uses the structured format that DSPy optimized for best results
 */

// System prompt that defines the task structure
const DSPY_SYSTEM_PROMPT = `Your input fields are:
1. \`heading\` (str): The full section heading text
Your output fields are:
1. \`reasoning\` (str): 
2. \`label\` (str): A short 1-3 word label suitable for a navigation button
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## heading ## ]]
{heading}

[[ ## reasoning ## ]]
{reasoning}

[[ ## label ## ]]
{label}

[[ ## completed ## ]]
In adhering to this structure, your objective is: 
        Generate a short, concise label (1-3 words) for a section heading that will be used as a quick action button.`;

// Examples in the exact DSPy format
const DSPY_EXAMPLES = [
"""
        
        # Add examples in exact format
        for i, ex in enumerate(examples):
            if ex.get('type') == 'complete':
                js_code += f"""    {{
        user: `This is an example of the task, though some input or output fields are not supplied.

[[ ## heading ## ]]
{ex['heading']}`,
        assistant: `[[ ## reasoning ## ]]
Not supplied for this particular example. 

[[ ## label ## ]]
{ex['label']}`
    }}"""
                if i < len(examples) - 1:
                    js_code += ",\n"
                else:
                    js_code += "\n"
        
        js_code += """];

/**
 * Generate a quick action label using the exact DSPy format
 * @param {string} heading - The section heading
 * @param {Object} llmClient - Your LLM client
 * @returns {Promise<string>} The generated label
 */
export async function generateQuickActionLabelDSPy(heading, llmClient) {
    // Build messages array in exact DSPy format
    const messages = [
        { role: 'system', content: DSPY_SYSTEM_PROMPT }
    ];
    
    // Add all examples
    DSPY_EXAMPLES.forEach(example => {
        messages.push({ role: 'user', content: example.user });
        messages.push({ role: 'assistant', content: example.assistant });
    });
    
    // Add the actual request
    messages.push({
        role: 'user',
        content: `[[ ## heading ## ]]
${heading}

Respond with the corresponding output fields, starting with the field \`[[ ## reasoning ## ]]\`, then \`[[ ## label ## ]]\`, and then ending with the marker for \`[[ ## completed ## ]]\`.`
    });
    
    try {
        // Call the LLM with the exact format
        const response = await llmClient.chat.completions.create({
            model: 'gpt-4o-mini', // or your preferred model
            messages: messages,
            temperature: 0.7
        });
        
        // Extract the label from the structured response
        const content = response.choices[0].message.content;
        const labelMatch = content.match(/\\[\\[ ## label ## \\]\\]\\n(.+?)\\n/);
        
        if (labelMatch) {
            return labelMatch[1].trim();
        }
        
        // Fallback
        return heading.split(' ').slice(0, 2).join(' ');
    } catch (error) {
        console.error('Error generating label:', error);
        return heading.split(' ').slice(0, 2).join(' ');
    }
}

// Example usage
/*
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const label = await generateQuickActionLabelDSPy(
    "Introduction to Machine Learning",
    openai
);
console.log(label); // "Introduction"
*/
"""
        
        return js_code
    
    return None

def main():
    js_code = extract_exact_prompt()
    
    if js_code:
        # Save to file
        output_path = 'output/generateQuickActionLabelDSPy.js'
        with open(output_path, 'w') as f:
            f.write(js_code)
        
        print(f"Exact DSPy prompt format saved to: {output_path}")
        print("\nThis file contains:")
        print("- The exact system prompt DSPy uses")
        print("- All examples in the exact format")
        print("- A function that replicates DSPy's prompt structure")
    else:
        print("Error: Could not extract prompt format")

if __name__ == "__main__":
    main()