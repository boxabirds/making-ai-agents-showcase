# Interactive Document Chat Interface

A modern web interface for chatting with markdown documents. This system allows users to navigate and interact with any markdown document through a conversational interface.

## Features

- **Dynamic Document Parsing**: Automatically extracts H1 sections and H2 subsections from markdown
- **Smart Navigation**: Click sections in sidebar or use chat to navigate
- **Quick Actions**: H2 subsections appear as quick action buttons (first 2 words)
- **Artifact References**: Chat responses can include clickable section/subsection references
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Code Highlighting**: Automatic syntax highlighting for code blocks

## Usage

### Running Locally

```bash
python3 serve.py
# Visit http://localhost:8082
```

### Loading Documents

1. **Default**: Loads built-in sample document
2. **URL Parameter**: `?doc=path/to/document.md`
3. **Remote URLs**: `?doc=https://example.com/doc.md`

### Interface Components

1. **Left Sidebar**: Shows all H1 sections
2. **Chat Area**: Natural language interaction
3. **Quick Actions**: H2 subsections of current section
4. **Document Panel**: Rendered markdown content

### Navigation Methods

- Click sections in sidebar
- Use quick action buttons
- Ask in chat: "Show me the section about X"
- Click artifact references in chat

## Architecture

- `index.html`: Main interface structure
- `document-parser.js`: Markdown parsing and structure extraction
- `script.js`: UI logic and interactions
- `styles.css`: Modern, responsive styling

## Future Integration

The interface is designed to integrate with a language model that has a single tool:

```javascript
{
  name: "navigate_to_section",
  parameters: {
    sectionId: "string", // H1 or H2 section ID
    type: "section|subsection"
  }
}
```

The LLM would receive the full document in its system prompt and use this tool to navigate users to relevant sections based on their questions.