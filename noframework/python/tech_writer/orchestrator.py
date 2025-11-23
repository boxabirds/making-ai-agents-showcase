"""
Orchestration for agentic exploration and report generation.

Phases:
1. Exploration: LLM explores codebase via tool calls
2. Outline: LLM generates report outline from understanding
3. Sections: LLM generates each section with citations
4. Assembly: Combine sections into final report
"""

import json
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Optional

from tech_writer.citations import verify_all_citations
from tech_writer.llm import LLMClient, get_tool_definitions
from tech_writer.store import CacheStore
from tech_writer.tools.filesystem import list_files, read_file
from tech_writer.tools.semantic import (
    get_definition,
    get_imports,
    get_references,
    get_structure,
    get_symbols,
    search_text,
)

# Constants
DEFAULT_MAX_EXPLORATION_STEPS = 50
DEFAULT_MAX_SECTIONS = 20
MAX_CITATION_FIX_ATTEMPTS = 2


@dataclass
class Section:
    """A section of the report outline."""
    title: str
    focus: str
    relevant_files: list[str]


EXPLORATION_SYSTEM_PROMPT = """You are a technical documentation expert exploring a codebase.

Your goal is to understand the codebase well enough to write comprehensive documentation based on the user's prompt.

You have access to these tools:
- list_files(pattern, path): List files matching a glob pattern
- read_file(path, start_line, end_line): Read file content
- get_symbols(path, kind): Get functions/classes/methods in a file
- get_imports(path): Get imports in a file
- get_definition(name): Find where a symbol is defined
- get_references(name): Find all usages of a symbol
- get_structure(path): Get complete structural overview of a file
- search_text(query): Search for text across files you've read
- finish_exploration(understanding): Signal you're done exploring

Explore strategically:
1. Start with entry points (README, main files, package.json)
2. Follow imports to understand dependencies
3. Use get_structure for file overviews before reading full content
4. Focus on understanding architecture, not every line of code

When you have enough understanding to write documentation matching the prompt, call finish_exploration with a summary of what you've learned.
"""

OUTLINE_SYSTEM_PROMPT = """You are a technical documentation expert creating an outline.

Based on your understanding of the codebase, create a JSON outline for the documentation.

Return a JSON array of sections, each with:
- title: Section title
- focus: What this section should cover
- relevant_files: Files to cite in this section

Example:
[
  {"title": "Overview", "focus": "High-level architecture", "relevant_files": ["README.md"]},
  {"title": "Core Components", "focus": "Main classes and their responsibilities", "relevant_files": ["src/core.js"]}
]

Return ONLY the JSON array, no other text.
"""

SECTION_SYSTEM_PROMPT = """You are a technical documentation expert writing a section.

Write the content for this section based on the provided context.

You have tools available if you need more information:
- read_file(path): Read a file's contents
- get_symbols(path, kind): Get functions/classes in a file
- get_structure(path): Get structural overview of a file
- get_imports(path): Get imports in a file
- search_text(query): Search for text in cached files

Follow these rules:

1. CITE YOUR SOURCES: Every claim about the code must include a citation in the format [path:start_line-end_line]
   Example: "The Axios class handles HTTP requests [lib/core/Axios.js:10-25]."

2. Be specific and accurate - only describe what you can see in the code

3. Use markdown formatting with appropriate headers

4. Don't repeat information from previous sections

5. Focus on the section's specific topic as described in the outline

6. If pre-gathered context is insufficient, use tools to read more files

7. When you have enough information, output the section content and stop calling tools
"""

CITATION_FIX_PROMPT_ADDITION = """
IMPORTANT: Your previous attempt had invalid citations. These citations were wrong:
{invalid_citations_list}

Common citation errors:
- Citing files that weren't read (use read_file first)
- Wrong line numbers (check the actual content)
- Citing non-existent lines (file may be shorter than you think)

Before making any claim, verify you have read the file and know the correct line numbers.
Use get_structure(path) to see available functions/classes and their line ranges.
"""

# Tools available during section generation (subset of exploration tools)
SECTION_TOOLS = {"read_file", "get_symbols", "get_structure", "get_imports", "search_text"}


def run_pipeline(
    prompt: str,
    repo: str,
    cache_dir: Optional[str] = None,
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_exploration: int = DEFAULT_MAX_EXPLORATION_STEPS,
    max_sections: int = DEFAULT_MAX_SECTIONS,
    db_path: Optional[str] = None,
) -> tuple[str, CacheStore]:
    """
    Run the full documentation pipeline.

    Args:
        prompt: The documentation prompt
        repo: Repository path or URL
        cache_dir: Directory for caching cloned repos
        model: LLM model to use
        api_key: API key
        base_url: Base URL for API
        max_exploration: Maximum exploration steps in Phase 1
        max_sections: Maximum sections in the outline
        db_path: Path for persistent cache (None for in-memory)

    Returns:
        Tuple of (report_markdown, cache_store)
    """
    # Handle remote repos
    repo_path = Path(repo)
    if not repo_path.exists():
        from tech_writer.repo import resolve_repo
        repo_path, _ = resolve_repo(repo, cache_dir)

    # Initialize store with optional persistence
    store = CacheStore(db_path=db_path)
    llm = LLMClient(model=model, api_key=api_key, base_url=base_url)

    # Phase 1: Exploration
    understanding = explore_codebase(prompt, repo_path, store, llm, max_steps=max_exploration)

    # Phase 2: Outline
    cached_files = store.list_cached_files()
    outline = generate_outline(prompt, understanding, cached_files, llm)

    # Enforce max_sections limit
    if len(outline) > max_sections:
        outline = outline[:max_sections]

    # Phase 3: Sections
    generator = SectionGenerator(
        store=store,
        repo_root=repo_path,
        llm_client=llm,
    )

    sections_content = []
    for section in outline:
        content = generator.generate(
            section=section,
            prompt=prompt,
            previous_sections=sections_content,
        )
        sections_content.append(content)

    # Phase 3.5: Citation verification and re-generation
    sections_content = verify_and_fix_citations(
        outline=outline,
        sections_content=sections_content,
        store=store,
        generator=generator,
        prompt=prompt,
    )

    # Phase 4: Assembly
    report = assemble_report(prompt, outline, sections_content)

    return report, store


def verify_and_fix_citations(
    outline: list[Section],
    sections_content: list[str],
    store: CacheStore,
    generator: 'SectionGenerator',
    prompt: str,
) -> list[str]:
    """
    Verify citations and re-generate sections with invalid citations.

    Args:
        outline: Report outline
        sections_content: Generated section content
        store: Cache store for verification
        generator: Section generator for re-generation
        prompt: Original prompt

    Returns:
        Fixed sections content (same length as input)
    """
    fixed_content = list(sections_content)

    for _ in range(MAX_CITATION_FIX_ATTEMPTS):
        # Find sections with invalid citations
        sections_to_fix = []

        for i, (section, content) in enumerate(zip(outline, fixed_content)):
            results, valid, invalid = verify_all_citations(content, store)
            if invalid > 0:
                invalid_citations = [r for r in results if not r.valid]
                sections_to_fix.append((i, section, invalid_citations))

        if not sections_to_fix:
            break  # All citations valid

        # Re-generate affected sections with stricter prompt
        for idx, section, invalid_cits in sections_to_fix:
            previous = fixed_content[:idx]
            fixed_content[idx] = generator.generate_with_citation_fix(
                section=section,
                prompt=prompt,
                previous_sections=previous,
                invalid_citations=invalid_cits,
            )

    return fixed_content


def explore_codebase(
    prompt: str,
    repo_root: Path,
    store: CacheStore,
    llm_client: LLMClient,
    max_steps: int = 50,
) -> str:
    """
    Agentic exploration phase.

    Args:
        prompt: The documentation prompt
        repo_root: Root of the repository
        store: Cache store
        llm_client: LLM client for tool calling
        max_steps: Maximum exploration steps

    Returns:
        Understanding summary from LLM
    """
    # Create tool handlers with bound parameters
    tool_handlers = {
        "list_files": partial(list_files, repo_root=repo_root),
        "read_file": partial(read_file, store=store, repo_root=repo_root),
        "get_symbols": partial(get_symbols, store=store, repo_root=repo_root),
        "get_imports": partial(get_imports, store=store, repo_root=repo_root),
        "get_definition": partial(get_definition, store=store),
        "get_references": partial(get_references, store=store),
        "get_structure": partial(get_structure, store=store, repo_root=repo_root),
        "search_text": partial(search_text, store=store),
    }

    messages = [
        {"role": "system", "content": EXPLORATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Documentation task:\n\n{prompt}\n\nPlease explore the codebase and call finish_exploration when ready."},
    ]

    understanding, _ = llm_client.run_tool_loop(
        messages=messages,
        tools=get_tool_definitions(),
        tool_handlers=tool_handlers,
        max_steps=max_steps,
    )

    return understanding


def generate_outline(
    prompt: str,
    understanding: str,
    cached_files: list[str],
    llm_client: LLMClient,
) -> list[Section]:
    """
    Generate report outline.

    Args:
        prompt: The documentation prompt
        understanding: Summary from exploration
        cached_files: List of explored files
        llm_client: LLM client

    Returns:
        List of sections for the report
    """
    files_list = "\n".join(f"- {f}" for f in cached_files)

    messages = [
        {"role": "system", "content": OUTLINE_SYSTEM_PROMPT},
        {"role": "user", "content": f"""Documentation task:
{prompt}

Understanding from exploration:
{understanding}

Files explored:
{files_list}

Create a JSON outline for this documentation."""},
    ]

    response = llm_client.chat(messages)
    content = response["content"] or "[]"

    # Parse JSON from response
    try:
        # Try to find JSON in the response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            outline_data = json.loads(json_str)
        else:
            outline_data = []
    except json.JSONDecodeError:
        outline_data = []

    # Convert to Section objects
    sections = []
    for item in outline_data:
        if isinstance(item, dict):
            sections.append(Section(
                title=item.get("title", "Untitled"),
                focus=item.get("focus", ""),
                relevant_files=item.get("relevant_files", []),
            ))

    return sections


class SectionGenerator:
    """Generates individual report sections with agentic exploration."""

    def __init__(
        self,
        store: CacheStore,
        repo_root: Path,
        llm_client: LLMClient,
        max_exploration_steps: int = 5,
    ):
        self.store = store
        self.repo_root = repo_root
        self.llm_client = llm_client
        self.max_exploration_steps = max_exploration_steps

    def _build_context(self, section: Section) -> str:
        """Build context string from relevant files."""
        context_parts = []
        for file_path in section.relevant_files:
            cached = self.store.get_file(file_path)
            if cached:
                # Include structure and key parts of content
                structure = get_structure(file_path, store=self.store)
                context_parts.append(f"## {file_path}\n")
                context_parts.append(f"Imports: {[i['module'] for i in structure['imports']]}\n")
                context_parts.append(f"Classes: {[c['name'] for c in structure['classes']]}\n")
                context_parts.append(f"Functions: {[f['name'] for f in structure['functions']]}\n")

                # Include truncated content
                lines = cached.content.splitlines()
                preview_lines = min(100, len(lines))
                context_parts.append(f"\nFirst {preview_lines} lines:\n```\n")
                context_parts.append("\n".join(lines[:preview_lines]))
                context_parts.append("\n```\n\n")

        return "\n".join(context_parts)

    def _build_previous_summary(self, previous_sections: list[str]) -> str:
        """Build summary of previous sections."""
        if not previous_sections:
            return ""

        prev_summary = "\n\nPrevious sections covered:\n"
        for prev in previous_sections:
            # Extract just the header
            lines = prev.strip().splitlines()
            if lines:
                prev_summary += f"- {lines[0]}\n"
        return prev_summary

    def _build_user_prompt(
        self,
        section: Section,
        prompt: str,
        context: str,
        prev_summary: str,
    ) -> str:
        """Build user prompt for section generation."""
        return f"""Documentation task: {prompt}

Section to write:
Title: {section.title}
Focus: {section.focus}

Context from relevant files:
{context}
{prev_summary}

Write this section with citations in [path:line-line] format."""

    def _get_tool_handlers(self) -> dict:
        """Get tool handlers for section generation."""
        return {
            "read_file": partial(read_file, store=self.store, repo_root=self.repo_root),
            "get_symbols": partial(get_symbols, store=self.store, repo_root=self.repo_root),
            "get_structure": partial(get_structure, store=self.store, repo_root=self.repo_root),
            "get_imports": partial(get_imports, store=self.store, repo_root=self.repo_root),
            "search_text": partial(search_text, store=self.store),
        }

    def _get_section_tools(self) -> list[dict]:
        """Get filtered tool definitions for section generation."""
        return [
            t for t in get_tool_definitions()
            if t["function"]["name"] in SECTION_TOOLS
        ]

    def generate(
        self,
        section: Section,
        prompt: str,
        previous_sections: list[str],
    ) -> str:
        """Generate content for a section using agentic exploration."""
        context = self._build_context(section)
        prev_summary = self._build_previous_summary(previous_sections)

        messages = [
            {"role": "system", "content": SECTION_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(section, prompt, context, prev_summary)},
        ]

        # Run agentic loop with limited steps
        content, _ = self.llm_client.run_tool_loop(
            messages=messages,
            tools=self._get_section_tools(),
            tool_handlers=self._get_tool_handlers(),
            max_steps=self.max_exploration_steps,
        )

        return content or ""

    def generate_with_citation_fix(
        self,
        section: Section,
        prompt: str,
        previous_sections: list[str],
        invalid_citations: list,
    ) -> str:
        """Generate section with explicit instructions to fix citation errors."""
        # Build list of invalid citations for the prompt
        invalid_list = "\n".join(
            f"- [{r.citation.path}:{r.citation.start_line}-{r.citation.end_line}]: {r.error}"
            for r in invalid_citations
        )

        # Add citation fix instructions to the system prompt
        enhanced_prompt = SECTION_SYSTEM_PROMPT + CITATION_FIX_PROMPT_ADDITION.format(
            invalid_citations_list=invalid_list
        )

        context = self._build_context(section)
        prev_summary = self._build_previous_summary(previous_sections)

        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": self._build_user_prompt(section, prompt, context, prev_summary)},
        ]

        # Run agentic generation with extra steps for verification
        content, _ = self.llm_client.run_tool_loop(
            messages=messages,
            tools=self._get_section_tools(),
            tool_handlers=self._get_tool_handlers(),
            max_steps=self.max_exploration_steps + 2,
        )

        return content or ""


def assemble_report(
    prompt: str,
    outline: list[Section],
    sections_content: list[str],
) -> str:
    """
    Assemble final report from sections.

    Args:
        prompt: Original prompt (for title extraction)
        outline: Report outline
        sections_content: Generated content for each section

    Returns:
        Complete markdown report
    """
    parts = []

    # Title from prompt (first line or truncated)
    prompt_lines = prompt.strip().splitlines()
    title = prompt_lines[0] if prompt_lines else "Documentation"
    if title.startswith("#"):
        title = title.lstrip("#").strip()
    parts.append(f"# {title}\n\n")

    # Add each section
    for section, content in zip(outline, sections_content):
        # Ensure section has proper header if not already
        if not content.strip().startswith("#"):
            parts.append(f"## {section.title}\n\n")
        parts.append(content.strip())
        parts.append("\n\n")

    return "".join(parts)
