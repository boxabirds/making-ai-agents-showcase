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

Write the content for this section based on the provided context. Follow these rules:

1. CITE YOUR SOURCES: Every claim about the code must include a citation in the format [path:start_line-end_line]
   Example: "The Axios class handles HTTP requests [lib/core/Axios.js:10-25]."

2. Be specific and accurate - only describe what you can see in the code

3. Use markdown formatting with appropriate headers

4. Don't repeat information from previous sections

5. Focus on the section's specific topic as described in the outline
"""


def run_pipeline(
    prompt: str,
    repo: str,
    cache_dir: Optional[str] = None,
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
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

    Returns:
        Tuple of (report_markdown, cache_store)
    """
    # Handle remote repos
    repo_path = Path(repo)
    if not repo_path.exists():
        from tech_writer.repo import resolve_repo
        repo_path, _ = resolve_repo(repo, cache_dir)

    # Initialize
    store = CacheStore()
    llm = LLMClient(model=model, api_key=api_key, base_url=base_url)

    # Phase 1: Exploration
    understanding = explore_codebase(prompt, repo_path, store, llm)

    # Phase 2: Outline
    cached_files = store.list_cached_files()
    outline = generate_outline(prompt, understanding, cached_files, llm)

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

    # Phase 4: Assembly
    report = assemble_report(prompt, outline, sections_content)

    return report, store


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
    """Generates individual report sections."""

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

    def generate(
        self,
        section: Section,
        prompt: str,
        previous_sections: list[str],
    ) -> str:
        """Generate content for a section."""
        # Gather context from relevant files
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

        context = "\n".join(context_parts)

        # Build previous sections summary
        prev_summary = ""
        if previous_sections:
            prev_summary = "\n\nPrevious sections covered:\n"
            for prev in previous_sections:
                # Extract just the header
                lines = prev.strip().splitlines()
                if lines:
                    prev_summary += f"- {lines[0]}\n"

        messages = [
            {"role": "system", "content": SECTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Documentation task: {prompt}

Section to write:
Title: {section.title}
Focus: {section.focus}

Context from relevant files:
{context}
{prev_summary}

Write this section with citations in [path:line-line] format."""},
        ]

        response = self.llm_client.chat(messages)
        return response["content"] or ""


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
