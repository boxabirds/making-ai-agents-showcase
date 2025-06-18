/**
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
    {
        user: `This is an example of the task, though some input or output fields are not supplied.

[[ ## heading ## ]]
Other python agent maker frameworks`,
        assistant: `[[ ## reasoning ## ]]
Not supplied for this particular example. 

[[ ## label ## ]]
Other Packages`
    },
    {
        user: `This is an example of the task, though some input or output fields are not supplied.

[[ ## heading ## ]]
Google Agent Developer Kit`,
        assistant: `[[ ## reasoning ## ]]
Not supplied for this particular example. 

[[ ## label ## ]]
adk-python`
    },
    {
        user: `This is an example of the task, though some input or output fields are not supplied.

[[ ## heading ## ]]
Why did you pick the tech writer agent for evaluation?`,
        assistant: `[[ ## reasoning ## ]]
Not supplied for this particular example. 

[[ ## label ## ]]
Tech Writer Choice`
    },
    {
        user: `This is an example of the task, though some input or output fields are not supplied.

[[ ## heading ## ]]
What did I standardise on?`,
        assistant: `[[ ## reasoning ## ]]
Not supplied for this particular example. 

[[ ## label ## ]]
Shared Code`
    }
];

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
        const labelMatch = content.match(/\[\[ ## label ## \]\]\n(.+?)\n/);
        
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
