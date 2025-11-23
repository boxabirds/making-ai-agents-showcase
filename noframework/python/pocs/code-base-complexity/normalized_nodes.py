"""
Normalized AST node mappings for language-agnostic complexity analysis.

Maps language-specific tree-sitter node types to universal concepts.
"""

# Universal node categories
UN_FUNCTION = "UN_Function"
UN_IF = "UN_If"
UN_LOOP = "UN_Loop"
UN_SWITCH = "UN_Switch"
UN_TRY = "UN_Try"
UN_BOOLEAN_OP = "UN_BooleanOp"
UN_TERNARY = "UN_Ternary"

# Language-specific node mappings
NODE_MAPPINGS = {
    "python": {
        UN_FUNCTION: ["function_definition"],
        UN_IF: ["if_statement", "elif_clause"],
        UN_LOOP: ["for_statement", "while_statement"],
        UN_SWITCH: ["match_statement"],  # Python 3.10+
        UN_TRY: ["except_clause"],  # Count except handlers, not try itself
        UN_BOOLEAN_OP: [],  # Handled specially - check for "and"/"or" operators
        UN_TERNARY: ["conditional_expression"],
    },
    "javascript": {
        UN_FUNCTION: ["function_declaration", "method_definition", "arrow_function", "function_expression"],
        UN_IF: ["if_statement"],
        UN_LOOP: ["for_statement", "for_in_statement", "while_statement", "do_statement"],
        UN_SWITCH: ["switch_case"],  # Count cases, not switch itself
        UN_TRY: ["catch_clause"],
        UN_BOOLEAN_OP: [],  # Handled specially - check for &&/|| operators
        UN_TERNARY: ["ternary_expression"],
    },
    "typescript": {
        UN_FUNCTION: ["function_declaration", "method_definition", "arrow_function", "function_expression"],
        UN_IF: ["if_statement"],
        UN_LOOP: ["for_statement", "for_in_statement", "while_statement", "do_statement"],
        UN_SWITCH: ["switch_case"],
        UN_TRY: ["catch_clause"],
        UN_BOOLEAN_OP: [],
        UN_TERNARY: ["ternary_expression"],
    },
    "go": {
        UN_FUNCTION: ["function_declaration", "method_declaration"],
        UN_IF: ["if_statement"],
        UN_LOOP: ["for_statement"],  # Go only has for
        UN_SWITCH: ["expression_case", "type_case"],
        UN_TRY: [],  # Go uses error returns
        UN_BOOLEAN_OP: [],
        UN_TERNARY: [],  # Go has no ternary
    },
    "rust": {
        UN_FUNCTION: ["function_item"],
        UN_IF: ["if_expression", "if_let_expression"],
        UN_LOOP: ["for_expression", "while_expression", "loop_expression"],
        UN_SWITCH: ["match_arm"],
        UN_TRY: [],  # Rust uses Result/Option
        UN_BOOLEAN_OP: [],
        UN_TERNARY: [],  # Rust uses if expressions
    },
    "java": {
        UN_FUNCTION: ["method_declaration", "constructor_declaration"],
        UN_IF: ["if_statement"],
        UN_LOOP: ["for_statement", "while_statement", "do_statement", "enhanced_for_statement"],
        UN_SWITCH: ["switch_label"],  # Count case labels
        UN_TRY: ["catch_clause"],
        UN_BOOLEAN_OP: [],
        UN_TERNARY: ["ternary_expression"],
    },
}

# Boolean operators by language
BOOLEAN_OPERATORS = {
    "python": {"and", "or"},
    "javascript": {"&&", "||"},
    "typescript": {"&&", "||"},
    "go": {"&&", "||"},
    "rust": {"&&", "||"},
    "java": {"&&", "||"},
}

# Extension to language mapping
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
}


def get_language(file_path: str) -> str | None:
    """Get language from file extension."""
    from pathlib import Path
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


def is_function_node(node_type: str, language: str) -> bool:
    """Check if node type represents a function definition."""
    if language not in NODE_MAPPINGS:
        return False
    return node_type in NODE_MAPPINGS[language].get(UN_FUNCTION, [])


def is_decision_point(node_type: str, language: str) -> bool:
    """Check if node type represents a decision point for cyclomatic complexity."""
    if language not in NODE_MAPPINGS:
        return False

    mapping = NODE_MAPPINGS[language]
    decision_categories = [UN_IF, UN_LOOP, UN_SWITCH, UN_TRY, UN_TERNARY]

    for category in decision_categories:
        if node_type in mapping.get(category, []):
            return True

    return False


def is_nesting_node(node_type: str, language: str) -> bool:
    """Check if node type increases nesting depth for cognitive complexity."""
    if language not in NODE_MAPPINGS:
        return False

    mapping = NODE_MAPPINGS[language]
    nesting_categories = [UN_IF, UN_LOOP, UN_SWITCH, UN_TRY]

    for category in nesting_categories:
        if node_type in mapping.get(category, []):
            return True

    return False


def get_boolean_operators(language: str) -> set:
    """Get boolean operators for a language."""
    return BOOLEAN_OPERATORS.get(language, set())


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return list(NODE_MAPPINGS.keys())
