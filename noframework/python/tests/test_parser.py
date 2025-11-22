from infinite_scalability.parser import extract_code_chunks, supports_lang


def test_supports_python():
    assert supports_lang("python")
    assert supports_lang("go")


def test_extract_python_chunks():
    code = """
def foo():
    return 1

class Bar:
    def baz(self):
        return 2
"""
    chunks = extract_code_chunks(code, "python")
    kinds = {c[3] for c in chunks}
    assert "function" in kinds
    assert "class" in kinds
    # ensure line ranges cover definitions
    assert any(start == 2 for start, _, _, _ in chunks)
