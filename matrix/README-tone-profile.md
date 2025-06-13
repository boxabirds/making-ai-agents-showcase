# Tone of Voice Profile System

This directory uses a centralized tone of voice profile to ensure consistency across all generated content.

## Files

- `tone-profile.txt` - The master tone of voice profile
- `matrix.prompt.txt` - References the tone profile for matrix generation
- `matrix-viewer-template-with-chat.html` - Uses the tone profile for chatbot responses

## How it Works

### 1. Matrix Generation (`--data` flag)

When running `./generate-matrix.sh --data`, the script:
1. Reads `matrix.prompt.txt` 
2. Reads `tone-profile.txt`
3. Combines them with the implementation files
4. Sends to the LLM to generate comparisons using the specified tone

### 2. Viewer Generation (`--viewer` flag)

When running `./generate-matrix.sh --viewer` or just `./generate-matrix.sh`, the script:
1. Reads the template file
2. Reads `tone-profile.txt`
3. Injects the tone profile into the chatbot's system prompt
4. Ensures chatbot responses match the tone of the generated content

## Modifying the Tone

To change the tone of voice:
1. Edit `tone-profile.txt`
2. Regenerate the matrix data: `./generate-matrix.sh --data`
3. Regenerate the viewer: `./generate-matrix.sh`

This ensures all content (comparisons, assessments, and chatbot responses) uses the same tone.

## Tone Profile Components

The current tone profile includes:
- **Skeptical Optimism** - Questions hype while highlighting genuine value
- **Upbeat & Engaging** - Positive energy and active voice
- **Truthful & Accurate** - Evidence-based claims
- **Slightly Sarcastic** - Occasional witty observations
- **Analytical & Discerning** - Critical thinking approach
- **Clear & Accessible** - Non-technical language
- **Direct & Experiential** - Authentic insights
- **Pragmatic & Action-Oriented** - Actionable takeaways
- **Confident but Humble** - Expertise without arrogance
- **Conversational & Relatable** - Engaging dialogue style