from typing import List, Tuple

from tree_sitter import Parser
from tree_sitter_languages import get_language


# Map our language labels to tree-sitter names (expand as needed)
TS_LANGS = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "json": "json",
    "markdown": "markdown",
    "go": "go",
    "rust": "rust",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "c_sharp": "c_sharp",
    "ruby": "ruby",
    "php": "php",
}

# Node types we care about for chunking per language
NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "method_definition", "class_declaration"},
    "typescript": {"function_declaration", "method_definition", "class_declaration"},
    "tsx": {"function_declaration", "method_definition", "class_declaration"},
    "go": {"function_declaration", "method_declaration", "type_declaration"},
    "rust": {"function_item", "impl_item", "struct_item", "enum_item"},
    "java": {"method_declaration", "class_declaration", "interface_declaration"},
    "cpp": {"function_definition", "class_specifier", "struct_specifier"},
    "c": {"function_definition"},
    "c_sharp": {"method_declaration", "class_declaration"},
    "ruby": {"method", "class"},
    "php": {"function_definition", "method_declaration", "class_declaration"},
    "markdown": {"section"},
    "json": {"object"},
}


def supports_lang(lang: str) -> bool:
    return lang in TS_LANGS


def _collect_nodes(node, wanted: set, results: list):
    if node.type in wanted:
        results.append(node)
    for child in node.children:
        _collect_nodes(child, wanted, results)


def extract_code_chunks(text: str, lang: str) -> List[Tuple[int, int, str, str]]:
    """
    Extract code chunks using tree-sitter. Returns list of (start_line, end_line, text, kind).
    """
    if not supports_lang(lang):
        raise ValueError(f"Language not supported for tree-sitter parsing: {lang}")
    language = get_language(TS_LANGS[lang])
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(text.encode("utf-8"))
    wanted = NODE_TYPES.get(lang, set())
    nodes: list = []
    _collect_nodes(tree.root_node, wanted, nodes)
    lines = text.splitlines()
    chunks: List[Tuple[int, int, str, str]] = []
    for node in nodes:
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        chunk_text = "\n".join(lines[start_line - 1 : end_line])
        kind = node.type.replace("_definition", "")
        chunks.append((start_line, end_line, chunk_text, kind))
    return chunks


def extract_symbols(text: str, lang: str) -> List[Tuple[str, str, int, int]]:
    """
    Extract symbol definitions (name, kind, start_line, end_line) via tree-sitter.
    """
    if not supports_lang(lang):
        return []
    language = get_language(TS_LANGS[lang])
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(text.encode("utf-8"))
    wanted = NODE_TYPES.get(lang, set())
    nodes: list = []
    _collect_nodes(tree.root_node, wanted, nodes)
    lines = text.splitlines()
    symbols: List[Tuple[str, str, int, int]] = []
    for node in nodes:
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        name = ""
        for child in node.children:
            if child.type in {"identifier", "name"}:
                name = text[child.start_byte : child.end_byte]
                break
        if not name and lines:
            name = lines[start_line - 1].strip().split("(")[0].replace("def ", "").replace("class ", "")
        kind = node.type.replace("_definition", "").replace("_declaration", "")
        symbols.append((name or "unknown", kind, start_line, end_line))
    return symbols
