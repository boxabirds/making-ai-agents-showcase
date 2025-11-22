from typing import List, Tuple

from tree_sitter_languages import get_parser


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
    "yaml": "yaml",
    "toml": "toml",
    "xml": "xml",
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
    "yaml": {"block_node", "flow_node", "block_mapping", "block_sequence"},
    "toml": {"table", "inline_table", "array_table", "key_value_pair"},
    "xml": {"element", "start_tag"},
}

IDENTIFIER_TYPES = {
    "python": {"identifier", "name"},
    "javascript": {"identifier"},
    "typescript": {"identifier"},
    "tsx": {"identifier"},
    "go": {"identifier"},
    "rust": {"identifier"},
    "java": {"identifier"},
    "cpp": {"identifier"},
    "c": {"identifier"},
    "c_sharp": {"identifier"},
    "ruby": {"identifier"},
    "php": {"name", "identifier"},
    "yaml": {"plain_scalar", "tag", "block_scalar", "flow_scalar"},
    "toml": {"bare_key", "quoted_key"},
    "xml": {"start_tag_name", "attribute_name"},
}

IMPORT_NODE_TYPES = {
    "python": {"import_statement", "import_from_statement"},
    "javascript": {"import_statement"},
    "typescript": {"import_statement"},
    "tsx": {"import_statement"},
    "go": {"import_spec"},
    "rust": {"use_declaration", "use_list"},
    "java": {"import_declaration"},
    "cpp": {"preproc_include"},
    "c": {"preproc_include"},
    "c_sharp": {"using_directive"},
    "ruby": {"method_call"},  # treat `require` calls via call edges, not imports
    "php": {"namespace_use_declaration"},
    "toml": {"key_value_pair"},
    "yaml": {"block_mapping_pair", "flow_pair"},
    "xml": {"attribute"},
}

CALL_NODE_TYPES = {
    "python": {"call"},
    "javascript": {"call_expression"},
    "typescript": {"call_expression"},
    "tsx": {"call_expression"},
    "go": {"call_expression"},
    "rust": {"call_expression"},
    "java": {"method_invocation"},
    "cpp": {"call_expression"},
    "c": {"call_expression"},
    "c_sharp": {"invocation_expression"},
    "ruby": {"method_call"},
    "php": {"function_call_expression", "method_call_expression"},
    "yaml": {"block_node", "flow_node"},
    "toml": {"inline_table", "table", "array_table"},
    "xml": {"element"},
}

INHERIT_NODE_TYPES = {
    "python": {"class_definition"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration"},
    "tsx": {"class_declaration"},
    "java": {"class_declaration"},
    "cpp": {"class_specifier", "struct_specifier"},
    "c_sharp": {"class_declaration"},
    "php": {"class_declaration"},
    "yaml": set(),
    "toml": set(),
    "xml": set(),
}

MEMBER_NODE_TYPES = {
    "javascript": {"method_definition"},
    "typescript": {"method_definition"},
    "tsx": {"method_definition"},
    "java": {"method_declaration"},
    "c_sharp": {"method_declaration"},
    "php": {"method_declaration"},
    "yaml": {"block_mapping_pair", "flow_pair"},
    "toml": {"key_value_pair"},
    "xml": {"attribute"},
}

IMPLEMENTS_NODE_TYPES = {
    "java": {"class_declaration"},
    "typescript": {"class_declaration"},
    "tsx": {"class_declaration"},
    "c_sharp": {"class_declaration"},
    "php": {"class_declaration"},
}

EXPORT_NODE_TYPES = {
    "javascript": {"export_statement", "export_clause"},
    "typescript": {"export_statement", "export_clause"},
    "tsx": {"export_statement", "export_clause"},
}

def supports_lang(lang: str) -> bool:
    return lang in TS_LANGS


def _collect_nodes(node, wanted: set, results: list):
    if node.type in wanted:
        results.append(node)
    for child in node.children:
        _collect_nodes(child, wanted, results)


def _find_identifier(node, text: str, lang: str) -> str:
    wanted = IDENTIFIER_TYPES.get(lang, {"identifier", "name"})
    for child in node.children:
        if child.type in wanted:
            return text[child.start_byte : child.end_byte]
    return ""


def extract_code_chunks(text: str, lang: str) -> List[Tuple[int, int, str, str]]:
    """
    Extract code chunks using tree-sitter. Returns list of (start_line, end_line, text, kind).
    """
    if not supports_lang(lang):
        raise ValueError(f"Language not supported for tree-sitter parsing: {lang}")
    parser = get_parser(TS_LANGS[lang])
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
    parser = get_parser(TS_LANGS[lang])
    tree = parser.parse(text.encode("utf-8"))
    wanted = NODE_TYPES.get(lang, set())
    nodes: list = []
    _collect_nodes(tree.root_node, wanted, nodes)
    lines = text.splitlines()
    symbols: List[Tuple[str, str, int, int]] = []
    for node in nodes:
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        name = _find_identifier(node, text, lang)
        if not name and lines:
            name = lines[start_line - 1].strip()
        kind = node.type.replace("_definition", "").replace("_declaration", "")
        symbols.append((name or "unknown", kind, start_line, end_line))
    return symbols


def extract_imports(text: str, lang: str) -> List[Tuple[str, int]]:
    """
    Extract import targets (module names) with line numbers via tree-sitter.
    """
    if not supports_lang(lang):
        return []
    parser = get_parser(TS_LANGS[lang])
    tree = parser.parse(text.encode("utf-8"))
    imports: List[Tuple[str, int]] = []
    node_types = IMPORT_NODE_TYPES.get(lang, set())

    def walk(node):
        if node.type in node_types:
            segment = text[node.start_byte : node.end_byte]
            line_no = node.start_point[0] + 1
            names: List[str] = []

            def collect_ident(child):
                if child.type in IDENTIFIER_TYPES.get(lang, {"identifier", "name"}):
                    names.append(text[child.start_byte : child.end_byte])
                for gc in child.children:
                    collect_ident(gc)

            collect_ident(node)
            for n in names:
                cleaned = n.split(".")[0]
                if cleaned:
                    imports.append((cleaned, line_no))
            if not names and node.type in {"attribute"} and lang == "xml":
                # treat attribute names as potential imports/refs
                imports.append((text[node.start_byte : node.end_byte], line_no))
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return imports


def extract_edges(text: str, lang: str, symbols: List[Tuple[str, str, int, int]]) -> List[Tuple[str, str, str]]:
    """
    Extract edges between symbols using tree-sitter. Supports call edges and inheritance/member-of edges; import edges are handled separately.
    Returns list of (src_symbol_name, dst_symbol_name, edge_type).
    """
    if not supports_lang(lang):
        return []
    parser = get_parser(TS_LANGS[lang])
    tree = parser.parse(text.encode("utf-8"))
    call_types = CALL_NODE_TYPES.get(lang, set())
    inherit_types = INHERIT_NODE_TYPES.get(lang, set())
    member_types = MEMBER_NODE_TYPES.get(lang, set())
    implements_types = IMPLEMENTS_NODE_TYPES.get(lang, set())
    export_types = EXPORT_NODE_TYPES.get(lang, set())
    symbol_ranges = []
    for name, kind, start, end in symbols:
        symbol_ranges.append((start, end, name))
    edges: List[Tuple[str, str, str]] = []

    def symbol_for_line(line_no: int) -> str | None:
        for start, end, name in symbol_ranges:
            if start <= line_no <= end:
                return name
        return None

    def walk(node, current_symbol: str | None):
        if node.type in call_types:
            caller = current_symbol
            callee = _find_identifier(node, text, lang)
            if caller and callee:
                edges.append((caller, callee, "calls"))
        if node.type in inherit_types and current_symbol:
            base = ""
            for child in node.children:
                if child.type in IDENTIFIER_TYPES.get(lang, {"identifier", "name"}):
                    base = text[child.start_byte : child.end_byte]
                    break
            if base:
                edges.append((current_symbol, base, "inherits"))
        if node.type in member_types:
            parent = current_symbol
            member = _find_identifier(node, text, lang)
            if parent and member:
                edges.append((parent, member, "member-of"))
        if node.type in implements_types and current_symbol:
            for child in node.children:
                if child.type in {"interface_type_list", "type_identifier", "identifier"}:
                    impl = text[child.start_byte : child.end_byte]
                    if impl:
                        edges.append((current_symbol, impl, "implements"))
        if node.type in export_types and current_symbol:
            target = _find_identifier(node, text, lang)
            if target:
                edges.append((current_symbol, target, "exports"))
        for child in node.children:
            child_symbol = current_symbol
            line_no = child.start_point[0] + 1
            sym = symbol_for_line(line_no)
            if sym:
                child_symbol = sym
            walk(child, child_symbol)

    walk(tree.root_node, None)
    return edges
