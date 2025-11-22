from infinite_scalability.llm import REPORT_SYSTEM_PROMPT


def test_report_system_prompt_mentions_citations():
    assert "path:start-end" in REPORT_SYSTEM_PROMPT
    assert "must include" in REPORT_SYSTEM_PROMPT
