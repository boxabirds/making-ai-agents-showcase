"""
Tree-sitter integration for semantic code analysis.

Provides:
- Language detection and parser selection
- Symbol extraction (functions, classes, methods)
- Import extraction
- AST queries
"""

from pathlib import Path
from typing import Optional

from tree_sitter_languages import get_parser, get_language


# Language detection by file extension
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}

# Languages with tree-sitter support
SUPPORTED_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "tsx",
    "go",
    "rust",
    "java",
    "c",
    "cpp",
    "ruby",
    "php",
    "json",
    "yaml",
    "html",
    "css",
}


def detect_language(path: str) -> Optional[str]:
    """
    Detect programming language from file extension.

    Args:
        path: File path

    Returns:
        Language name or None if unknown
    """
    ext = Path(path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


def is_supported(lang: str) -> bool:
    """Check if language has tree-sitter support."""
    return lang in SUPPORTED_LANGUAGES


class ParserManager:
    """Manages tree-sitter parsers for multiple languages."""

    def __init__(self):
        """Initialize parser manager."""
        self._parsers: dict = {}

    def get_parser(self, language: str):
        """
        Get or create parser for a language.

        Args:
            language: Language name

        Returns:
            tree-sitter Parser or None if unsupported
        """
        if language not in SUPPORTED_LANGUAGES:
            return None

        if language not in self._parsers:
            try:
                self._parsers[language] = get_parser(language)
            except Exception:
                return None

        return self._parsers[language]

    def parse(self, content: str, language: str):
        """
        Parse source code and return AST.

        Args:
            content: Source code
            language: Language name

        Returns:
            tree-sitter Tree or None if unsupported
        """
        parser = self.get_parser(language)
        if parser is None:
            return None

        try:
            return parser.parse(content.encode("utf-8"))
        except Exception:
            return None

    def extract_symbols(self, content: str, language: str) -> list[dict]:
        """
        Extract all symbols from source code.

        Args:
            content: Source code
            language: Language name

        Returns:
            List of symbol dicts with keys:
            name, kind, line, end_line, signature, doc, parent
        """
        tree = self.parse(content, language)
        if tree is None:
            return []

        symbols = []

        if language == "python":
            symbols = self._extract_python_symbols(tree.root_node, content)
        elif language in ("javascript", "typescript", "tsx"):
            symbols = self._extract_js_symbols(tree.root_node, content)
        elif language == "go":
            symbols = self._extract_go_symbols(tree.root_node, content)
        elif language == "java":
            symbols = self._extract_java_symbols(tree.root_node, content)

        return symbols

    def _extract_python_symbols(self, root, content: str) -> list[dict]:
        """Extract symbols from Python AST."""
        symbols = []

        def visit(node, parent_class=None):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)

                    # Get signature (first line)
                    sig = content.splitlines()[start_line - 1].strip() if start_line <= len(content.splitlines()) else None

                    # Get docstring
                    doc = self._get_python_docstring(node, content)

                    kind = "method" if parent_class else "function"
                    symbols.append({
                        "name": name,
                        "kind": kind,
                        "line": start_line,
                        "end_line": end_line,
                        "signature": sig,
                        "doc": doc,
                        "parent": parent_class,
                    })

            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)
                    doc = self._get_python_docstring(node, content)

                    symbols.append({
                        "name": name,
                        "kind": "class",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": f"class {name}",
                        "doc": doc,
                        "parent": None,
                    })

                    # Visit children with this class as parent
                    for child in node.children:
                        visit(child, parent_class=name)
                    return  # Don't revisit children

            for child in node.children:
                visit(child, parent_class)

        visit(root)
        return symbols

    def _get_python_docstring(self, node, content: str) -> Optional[str]:
        """Extract docstring from Python function/class node."""
        body = node.child_by_field_name("body")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                expr = first_stmt.children[0] if first_stmt.children else None
                if expr and expr.type == "string":
                    doc = get_node_text(expr, content)
                    # Strip quotes
                    if doc.startswith('"""') or doc.startswith("'''"):
                        return doc[3:-3].strip()
                    elif doc.startswith('"') or doc.startswith("'"):
                        return doc[1:-1].strip()
        return None

    def _extract_js_symbols(self, root, content: str) -> list[dict]:
        """Extract symbols from JavaScript/TypeScript AST."""
        symbols = []

        def visit(node, parent_class=None):
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)
                    sig = self._get_js_function_signature(node, content)

                    symbols.append({
                        "name": name,
                        "kind": "function",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": sig,
                        "doc": None,
                        "parent": None,
                    })

            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)

                    symbols.append({
                        "name": name,
                        "kind": "class",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": f"class {name}",
                        "doc": None,
                        "parent": None,
                    })

                    # Visit children with class as parent
                    for child in node.children:
                        visit(child, parent_class=name)
                    return

            elif node.type == "method_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)
                    sig = self._get_js_method_signature(node, content)

                    symbols.append({
                        "name": name,
                        "kind": "method",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": sig,
                        "doc": None,
                        "parent": parent_class,
                    })

            # Also handle variable declarations with arrow functions
            elif node.type == "lexical_declaration" or node.type == "variable_declaration":
                for child in node.children:
                    if child.type == "variable_declarator":
                        name_node = child.child_by_field_name("name")
                        value_node = child.child_by_field_name("value")
                        if name_node and value_node and value_node.type == "arrow_function":
                            name = get_node_text(name_node, content)
                            start_line, end_line = get_node_line_range(node)

                            symbols.append({
                                "name": name,
                                "kind": "function",
                                "line": start_line,
                                "end_line": end_line,
                                "signature": f"const {name} = (...) => ...",
                                "doc": None,
                                "parent": None,
                            })

            for child in node.children:
                visit(child, parent_class)

        visit(root)
        return symbols

    def _get_js_function_signature(self, node, content: str) -> str:
        """Get signature for JS function."""
        # Get first line up to opening brace
        start_line = node.start_point[0]
        lines = content.splitlines()
        if start_line < len(lines):
            line = lines[start_line]
            # Find opening brace and take everything before
            brace_idx = line.find('{')
            if brace_idx > 0:
                return line[:brace_idx].strip()
            return line.strip()
        return ""

    def _get_js_method_signature(self, node, content: str) -> str:
        """Get signature for JS method."""
        start_line = node.start_point[0]
        lines = content.splitlines()
        if start_line < len(lines):
            line = lines[start_line].strip()
            brace_idx = line.find('{')
            if brace_idx > 0:
                return line[:brace_idx].strip()
            return line
        return ""

    def _extract_go_symbols(self, root, content: str) -> list[dict]:
        """Extract symbols from Go AST."""
        symbols = []

        def visit(node):
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)

                    symbols.append({
                        "name": name,
                        "kind": "function",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": None,
                        "doc": None,
                        "parent": None,
                    })

            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)
                    # Try to get receiver type
                    receiver = node.child_by_field_name("receiver")
                    parent = None
                    if receiver:
                        for child in receiver.children:
                            if child.type == "type_identifier":
                                parent = get_node_text(child, content)
                                break

                    symbols.append({
                        "name": name,
                        "kind": "method",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": None,
                        "doc": None,
                        "parent": parent,
                    })

            elif node.type == "type_declaration":
                for child in node.children:
                    if child.type == "type_spec":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            name = get_node_text(name_node, content)
                            start_line, end_line = get_node_line_range(node)

                            symbols.append({
                                "name": name,
                                "kind": "type",
                                "line": start_line,
                                "end_line": end_line,
                                "signature": f"type {name}",
                                "doc": None,
                                "parent": None,
                            })

            for child in node.children:
                visit(child)

        visit(root)
        return symbols

    def _extract_java_symbols(self, root, content: str) -> list[dict]:
        """Extract symbols from Java AST."""
        symbols = []

        def visit(node, parent_class=None):
            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)

                    symbols.append({
                        "name": name,
                        "kind": "class",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": f"class {name}",
                        "doc": None,
                        "parent": None,
                    })

                    for child in node.children:
                        visit(child, parent_class=name)
                    return

            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node, content)
                    start_line, end_line = get_node_line_range(node)

                    symbols.append({
                        "name": name,
                        "kind": "method",
                        "line": start_line,
                        "end_line": end_line,
                        "signature": None,
                        "doc": None,
                        "parent": parent_class,
                    })

            for child in node.children:
                visit(child, parent_class)

        visit(root)
        return symbols

    def extract_imports(self, content: str, language: str) -> list[dict]:
        """
        Extract all imports from source code.

        Args:
            content: Source code
            language: Language name

        Returns:
            List of import dicts with keys:
            module, names, line, is_relative
        """
        tree = self.parse(content, language)
        if tree is None:
            return []

        imports = []

        if language == "python":
            imports = self._extract_python_imports(tree.root_node, content)
        elif language in ("javascript", "typescript", "tsx"):
            imports = self._extract_js_imports(tree.root_node, content)
        elif language == "go":
            imports = self._extract_go_imports(tree.root_node, content)
        elif language == "java":
            imports = self._extract_java_imports(tree.root_node, content)

        return imports

    def _extract_python_imports(self, root, content: str) -> list[dict]:
        """Extract imports from Python AST."""
        imports = []

        def visit(node):
            if node.type == "import_statement":
                # import X, Y, Z
                line = node.start_point[0] + 1
                for child in node.children:
                    if child.type == "dotted_name":
                        module = get_node_text(child, content)
                        imports.append({
                            "module": module,
                            "names": [],
                            "line": line,
                            "is_relative": False,
                        })
                    elif child.type == "aliased_import":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            module = get_node_text(name_node, content)
                            imports.append({
                                "module": module,
                                "names": [],
                                "line": line,
                                "is_relative": False,
                            })

            elif node.type == "import_from_statement":
                # from X import Y, Z
                line = node.start_point[0] + 1
                module_name = None
                is_relative = False
                names = []

                # First pass: get module name
                found_from = False
                found_import = False
                for child in node.children:
                    text = get_node_text(child, content)
                    if text == "from":
                        found_from = True
                    elif text == "import":
                        found_import = True
                    elif child.type == "dotted_name" and found_from and not found_import:
                        module_name = get_node_text(child, content)
                    elif child.type == "relative_import":
                        is_relative = True
                        # Get the dots and module name
                        parts = []
                        for sub in child.children:
                            if sub.type == "import_prefix":
                                parts.append(get_node_text(sub, content))
                            elif sub.type == "dotted_name":
                                parts.append(get_node_text(sub, content))
                        module_name = "".join(parts) if parts else "."

                # Second pass: get imported names (after 'import' keyword)
                found_import = False
                for child in node.children:
                    text = get_node_text(child, content)
                    if text == "import":
                        found_import = True
                        continue
                    if not found_import:
                        continue
                    if child.type == "dotted_name":
                        names.append(get_node_text(child, content))
                    elif child.type == "aliased_import":
                        name_node = child.child_by_field_name("name")
                        if name_node:
                            names.append(get_node_text(name_node, content))
                    elif child.type == "wildcard_import":
                        names.append("*")

                # Handle "from . import X" where module is just dots
                if module_name is None and is_relative:
                    module_name = "."

                if module_name:
                    imports.append({
                        "module": module_name,
                        "names": names,
                        "line": line,
                        "is_relative": is_relative,
                    })

            for child in node.children:
                visit(child)

        visit(root)
        return imports

    def _extract_js_imports(self, root, content: str) -> list[dict]:
        """Extract imports from JavaScript/TypeScript AST."""
        imports = []

        def visit(node):
            if node.type == "import_statement":
                line = node.start_point[0] + 1
                source = None
                names = []

                for child in node.children:
                    if child.type == "string":
                        source = get_node_text(child, content).strip("'\"")
                    elif child.type == "import_clause":
                        for sub in child.children:
                            if sub.type == "identifier":
                                names.append(get_node_text(sub, content))
                            elif sub.type == "named_imports":
                                for imp in sub.children:
                                    if imp.type == "import_specifier":
                                        name_node = imp.child_by_field_name("name")
                                        if name_node:
                                            names.append(get_node_text(name_node, content))
                            elif sub.type == "namespace_import":
                                names.append("*")

                if source:
                    imports.append({
                        "module": source,
                        "names": names,
                        "line": line,
                        "is_relative": source.startswith("."),
                    })

            # Handle CommonJS require()
            elif node.type == "lexical_declaration" or node.type == "variable_declaration":
                line = node.start_point[0] + 1
                for child in node.children:
                    if child.type == "variable_declarator":
                        name_node = child.child_by_field_name("name")
                        value_node = child.child_by_field_name("value")
                        if name_node and value_node and value_node.type == "call_expression":
                            func_node = value_node.child_by_field_name("function")
                            if func_node and get_node_text(func_node, content) == "require":
                                args = value_node.child_by_field_name("arguments")
                                if args:
                                    for arg in args.children:
                                        if arg.type == "string":
                                            source = get_node_text(arg, content).strip("'\"")
                                            imports.append({
                                                "module": source,
                                                "names": [get_node_text(name_node, content)],
                                                "line": line,
                                                "is_relative": source.startswith("."),
                                            })

            for child in node.children:
                visit(child)

        visit(root)
        return imports

    def _extract_go_imports(self, root, content: str) -> list[dict]:
        """Extract imports from Go AST."""
        imports = []

        def visit(node):
            if node.type == "import_declaration":
                line = node.start_point[0] + 1
                for child in node.children:
                    if child.type == "import_spec":
                        path_node = child.child_by_field_name("path")
                        if path_node:
                            path = get_node_text(path_node, content).strip('"')
                            imports.append({
                                "module": path,
                                "names": [],
                                "line": line,
                                "is_relative": False,
                            })
                    elif child.type == "import_spec_list":
                        for spec in child.children:
                            if spec.type == "import_spec":
                                path_node = spec.child_by_field_name("path")
                                if path_node:
                                    path = get_node_text(path_node, content).strip('"')
                                    imports.append({
                                        "module": path,
                                        "names": [],
                                        "line": spec.start_point[0] + 1,
                                        "is_relative": False,
                                    })

            for child in node.children:
                visit(child)

        visit(root)
        return imports

    def _extract_java_imports(self, root, content: str) -> list[dict]:
        """Extract imports from Java AST."""
        imports = []

        def visit(node):
            if node.type == "import_declaration":
                line = node.start_point[0] + 1
                # Get the full import path
                for child in node.children:
                    if child.type == "scoped_identifier":
                        module = get_node_text(child, content)
                        imports.append({
                            "module": module,
                            "names": [],
                            "line": line,
                            "is_relative": False,
                        })

            for child in node.children:
                visit(child)

        visit(root)
        return imports


def parse_file(content: str, lang: str):
    """
    Parse file content into AST.

    Args:
        content: Source code
        lang: Language name

    Returns:
        tree-sitter Tree or None if unsupported
    """
    manager = ParserManager()
    return manager.parse(content, lang)


def get_node_text(node, content: str) -> str:
    """
    Extract text for an AST node.

    Args:
        node: tree-sitter Node
        content: Full source code

    Returns:
        Text content of the node
    """
    return content[node.start_byte:node.end_byte]


def get_node_line_range(node) -> tuple[int, int]:
    """
    Get line range for a node (1-indexed).

    Args:
        node: tree-sitter Node

    Returns:
        Tuple of (start_line, end_line) both 1-indexed
    """
    # tree-sitter uses 0-indexed lines
    return (node.start_point[0] + 1, node.end_point[0] + 1)
