# Quick Action Label Generation

## Overview

The chat interface now automatically generates concise quick action labels for document sections using the integrated Gemini LLM. This eliminates the need for manual metadata annotations using parentheses in markdown headings.

## How It Works

### 1. Document Parsing
When a markdown document is loaded, the `DocumentParser` extracts all H1 and H2 headings.

### 2. Label Generation
After parsing, all headings are sent in a single API call to generate labels:
- Uses a DSPy-optimized prompt with examples
- Returns a JSON array of labels matching the input array
- Falls back to simple word extraction if API fails

### 3. Label Application
Generated labels are applied to:
- Section objects (`quickActionLabel` property)
- Quick action buttons (displayed text)
- Tooltips show the full heading for context

## Implementation Details

### Prompt Structure
The system uses examples from DSPy training to generate consistent labels:

```javascript
Input: ["Introduction to Machine Learning", "Getting Started with Python"]
Output: ["ML Introduction", "Python Setup"]
```

### API Configuration
- Temperature: 0.3 (balanced between creativity and consistency)
- Max tokens: 256 (sufficient for many labels)
- Model: Gemini 2.0 Flash

### Fallback Strategy
If the API fails or returns invalid JSON:
1. Extract first 2-3 significant words from heading
2. Filter out common words (the, and, for, with, from)
3. Use first 20 characters if no significant words found

## Usage

### Automatic Generation
Simply load any markdown document. Labels are generated automatically during parsing.

### Manual Testing
```javascript
// Test label generation directly
const headings = ["Introduction to AI", "Getting Started"];
const labels = await window.generateQuickActionLabels(headings);
console.log(labels); // ["AI Introduction", "Getting Started"]
```

### Accessing Generated Labels
```javascript
// After document is parsed
documentParser.getMainSections().forEach(section => {
    console.log(`${section.title} → ${section.quickActionLabel}`);
    section.subsections.forEach(sub => {
        console.log(`  ${sub.title} → ${sub.quickActionLabel}`);
    });
});
```

## Benefits

1. **No Manual Annotation**: No need for `# Title (Label)` format
2. **Consistency**: DSPy-trained examples ensure consistent labeling
3. **Efficiency**: Single API call for all headings
4. **Graceful Degradation**: Falls back to title if generation fails
5. **Context Preservation**: Full titles shown in tooltips

## Testing

Use `test-quick-action-labels.html` to test the feature:
1. Open the file in a browser
2. Click "Load Test Document"
3. Check console for generated labels
4. Verify quick action buttons display correctly

## Future Improvements

1. **Caching**: Store generated labels in localStorage
2. **Batch Processing**: Handle very large documents in chunks
3. **Custom Examples**: Allow project-specific training examples
4. **Pre-generation**: Generate labels server-side for production