# Navigation Protocol Evolution

## Version 1: Single ID Parameter (Original)

```javascript
{
  name: "jump_to_section",
  description: "User mentions a section so we return a request to jump to that section id",
  parameters: {
    type: "object",
    properties: {
      section_id: {
        type: "string"
      }
    },
    required: ["section_id"]
  }
}
```

**Problems:**
- Ambiguous whether navigating to section or subsection
- Required complex ID mapping
- LLM had to guess the correct ID format

## Version 2: Hierarchical Navigation (Current)

```javascript
{
  name: "navigate_to_section",
  description: "When user asks about content related to these sections, navigate there instead of describing it. Available sections: Agno (subsections: Architecture, Tools, Performance); Autogen (subsections: Getting Started, Advanced Features, Examples)",
  parameters: {
    type: "object",
    properties: {
      section: {
        type: "string",
        description: "The main section name",
        enum: ["Agno", "Autogen", "Deployment Guide"]
      },
      subsection: {
        type: "string",
        description: "The subsection name within the main section (optional). Only provide if user asks about specific subsection content. Must be a valid subsection under the chosen section.",
        enum: ["Architecture", "Tools", "Performance", "Getting Started", "Advanced Features", "Examples", "Cloud Deployment", "Security"]
      }
    },
    required: ["section"]
  }
}
```

**Improvements:**
- Clear separation of section and subsection
- Natural language values instead of IDs
- Enum validation prevents typos
- Hierarchical structure preserved in description
- Optional subsection parameter

## Key Design Decisions

### 1. Natural Language Over IDs
- **Before**: `section_id: "agno-architecture"`
- **After**: `section: "Agno", subsection: "Architecture"`

### 2. Enum Validation
- Sections have strict enum (prevents invalid sections)
- Subsections have combined enum (all possible values)
- Description guides proper pairing

### 3. Prompt Engineering
- "jump to that section **instead**" triggers tool use
- Clear hierarchy in description prevents mismatches
- Tool description lists valid combinations

## Test Coverage

1. **test-1**: Basic single-section navigation (legacy)
2. **test-2**: Complex prompt compatibility (legacy)
3. **test-3**: Hierarchical navigation with enum validation
4. **test-4**: Cloudflare worker proxy support
5. **test-5**: Full production prompt
6. **test-6**: New protocol with all features
7. **test-7**: Subsection validation edge cases

## Results

All tests pass, demonstrating:
- LLM correctly identifies section/subsection from queries
- Enum constraints are respected
- Invalid combinations are avoided
- Fallback behavior works when subsection not found
- v1beta endpoint is required for tool support (not a Cloudflare limitation)

## Future Considerations

1. **Deeper Nesting**: For H3+ support, could use array path: `["Agno", "Tools", "Debugging"]`
2. **Dynamic Enums**: Generate enums based on actual document structure
3. **Fuzzy Matching**: Handle slight variations in subsection names
4. **Context Awareness**: Consider current section when interpreting ambiguous requests