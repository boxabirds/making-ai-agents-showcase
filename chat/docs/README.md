# Documentation

This directory contains documentation for the chat application's tool calling implementation.

## Files

### [tool-calling.md](./tool-calling.md)
Comprehensive guide covering:
- Implementation details
- Architecture decisions
- Testing strategy
- Common issues and solutions
- Best practices

### [quick-reference.md](./quick-reference.md)
Quick reference for developers:
- Critical success factors
- Minimal working examples
- Common pitfalls
- Testing checklist

## Key Takeaways

1. **Prompt Engineering**: The word "instead" is critical for tool calling
2. **API Version**: Must use v1beta endpoint for tool support (v1 doesn't support tools)
3. **Proxy Configuration**: Ensure any proxy (including Cloudflare) uses v1beta endpoint
4. **Navigation Design**: Separate section/subsection parameters with enum validation

## Related Files

- `/chat/test-*.sh` - Test suite for tool calling
- `/chat/script.js` - Main implementation
- `/matrix/backend/worker.js` - Cloudflare Worker proxy
- `/chat/navigation-protocol-evolution.md` - Design evolution