# Evaluation Design for tech_writer v2

## Overview

This document defines the evaluation strategy for the tech_writer documentation generation system. The goal is to measure whether generated reports are accurate, well-cited, and useful.

Evaluation operates at three levels:
1. **Automated checks** - Fast, cheap, run on every generation
2. **LLM-as-a-judge** - Scalable semantic evaluation
3. **Human-in-the-loop (HIL)** - Ground truth calibration

## Goals

1. Validate that citations actually support the claims they're attached to
2. Measure whether reports are faithful to the source code (no hallucinations)
3. Assess completeness relative to the user's prompt
4. Establish ground truth via human annotation
5. Calibrate LLM judges against human judgments
6. Enable regression testing as the system evolves

## Metrics

### Citation Metrics

These metrics evaluate whether the citation system is working correctly.

#### Citation Validity

**Definition:** The percentage of citations that resolve to actual cached content.

**Computation:** Already implemented in `citations.py:verify_all_citations()`. A citation is valid if:
- The file path exists in the cache
- The start_line and end_line are within the file's line count
- start_line <= end_line

**Formula:**
```
citation_validity = valid_citations / total_citations
```

**Target:** > 95% (citations that don't resolve indicate bugs in the system)

**Implementation status:** Complete.

#### Citation Coverage

**Definition:** The percentage of factual claims in the report that have at least one supporting citation.

**Computation:**
1. Extract all sentences/claims from the report
2. For each claim, check if it contains a citation pattern `[path:line-line]`
3. Count claims with vs without citations

**Formula:**
```
citation_coverage = claims_with_citations / total_claims
```

**Target:** > 80% (some claims like "This section covers X" don't need citations)

**Implementation status:** Not implemented.

#### Citation Precision

**Definition:** The percentage of citations where the cited code actually supports the claim being made.

**Computation:** Requires semantic judgment (LLM or human). For each citation:
1. Extract the claim text surrounding the citation
2. Extract the actual code from the cited lines
3. Judge: "Does this code support this claim?"

**Formula:**
```
citation_precision = supporting_citations / total_citations
```

**Target:** > 85%

**Implementation status:** Not implemented. Requires LLM-as-judge or HIL.

#### Citation Recall

**Definition:** For claims that should be cited, how many have correct citations (not just any citation)?

**Computation:** Requires ground truth annotation. Given a set of claims that experts have identified as needing citations:
1. Check if the claim has a citation
2. Check if the citation is correct (precision)

**Formula:**
```
citation_recall = correctly_cited_claims / claims_needing_citations
```

**Target:** > 75%

**Implementation status:** Not implemented. Requires HIL ground truth.

#### Line Range Accuracy

**Definition:** Whether the cited line range is appropriate - not too narrow (missing context) or too broad (citing entire files).

**Computation:** Human judgment or LLM judge with categories:
- `too_narrow`: Citation misses relevant context
- `correct`: Citation includes appropriate scope
- `too_broad`: Citation includes unrelated code

**Formula:**
```
line_range_accuracy = correct_ranges / total_citations
```

**Target:** > 70% correct

**Implementation status:** Not implemented.

### Content Quality Metrics

These metrics evaluate the quality of the generated documentation itself.

#### Faithfulness

**Definition:** Whether the report only contains statements that are supported by the source code. A report is unfaithful if it contains hallucinations - claims that aren't grounded in any code the system read.

**Computation:** LLM-as-judge evaluates each claim:
1. Extract claim from report
2. Gather all code the system read (from cache)
3. Judge: "Is this claim supported by any of the code?"

**Scoring:**
- 0 = Claim contradicts the code
- 1 = Claim is not supported by any code (hallucination)
- 2 = Claim is partially supported
- 3 = Claim is fully supported by code

**Formula:**
```
faithfulness = sum(claim_scores) / (3 * total_claims)
```

**Target:** > 0.85

**Implementation status:** Not implemented.

#### Completeness

**Definition:** Whether the report adequately addresses what the user asked for in their prompt.

**Computation:** LLM-as-judge compares prompt to outline and content:
1. Extract key topics/questions from the prompt
2. Check which topics are covered in the report
3. Assess depth of coverage for each topic

**Scoring per topic:**
- 0 = Not mentioned
- 1 = Mentioned briefly
- 2 = Covered adequately
- 3 = Covered thoroughly

**Formula:**
```
completeness = sum(topic_scores) / (3 * total_topics)
```

**Target:** > 0.75

**Implementation status:** Not implemented.

#### Coherence

**Definition:** Whether the report flows logically, with proper transitions between sections and consistent terminology.

**Computation:** LLM-as-judge evaluates structure:
1. Do sections follow a logical order?
2. Are transitions between sections smooth?
3. Is terminology consistent throughout?
4. Are there redundant sections?

**Scoring:**
- 0 = Incoherent, disorganized
- 1 = Some logical issues
- 2 = Generally coherent with minor issues
- 3 = Well-organized and flows naturally

**Target:** > 2.0 average

**Implementation status:** Not implemented.

#### Technical Accuracy

**Definition:** Whether technical statements in the report are correct.

**Computation:** Requires domain expertise. Evaluator checks:
1. Are function/class names correct?
2. Are described behaviors accurate?
3. Are relationships between components correct?

This is the hardest metric to automate and typically requires human expert review or code execution to verify.

**Target:** > 90% of technical statements correct

**Implementation status:** Not implemented.

### Operational Metrics

These metrics track system behavior, not output quality.

#### Exploration Efficiency

**Definition:** How many files were read relative to total files in the repo.

**Formula:**
```
exploration_efficiency = files_cached / total_repo_files
```

**Interpretation:** Lower is better (system focused on relevant files). Very low might indicate under-exploration.

**Target:** 5-30% depending on query scope

**Implementation status:** Partially implemented (can compute from store).

#### Token Usage

**Definition:** Total tokens consumed across all LLM calls.

**Breakdown:**
- Exploration phase tokens
- Outline phase tokens
- Section generation tokens (per section)
- Total tokens

**Implementation status:** Not implemented. Requires capturing OpenAI response `usage` field.

#### LLM Calls

**Definition:** Number of LLM API calls made during generation.

**Breakdown:**
- Exploration tool loop iterations
- Outline generation (always 1)
- Section generation calls
- Citation fix re-generation calls

**Implementation status:** Not implemented.

## Evaluation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         tech_writer generates report                         │
│                                                                             │
│  Input: prompt + repo                                                       │
│  Output: report.md + cache.db                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TIER 1: Automated                              │
│                           (runs on every generation)                         │
│                                                                             │
│  Checks:                                                                    │
│  ├── Citation validity (verify_all_citations)                               │
│  ├── Citation coverage (regex + sentence detection)                         │
│  ├── Section count vs max_sections                                          │
│  ├── Exploration efficiency (files_cached / repo_files)                     │
│  └── Report length sanity check                                             │
│                                                                             │
│  Output: metrics.json with pass/fail status                                 │
│  Cost: ~0 (no LLM calls)                                                    │
│  Latency: < 1 second                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TIER 2: LLM-as-Judge                             │
│                        (runs on CI or manual trigger)                        │
│                                                                             │
│  Evaluations:                                                               │
│  ├── Citation precision (per citation)                                      │
│  │   └── "Does this code support this claim?" → bool + reasoning            │
│  ├── Faithfulness (per section)                                             │
│  │   └── "Are all claims grounded in cited code?" → score 0-3              │
│  ├── Completeness (whole report)                                            │
│  │   └── "Does the report address the prompt?" → score 0-3                 │
│  └── Coherence (whole report)                                               │
│      └── "Is the report well-organized?" → score 0-3                       │
│                                                                             │
│  Output: eval_results.json with scores and reasoning                        │
│  Cost: ~$0.10-0.50 per report (depends on size)                            │
│  Latency: 30-120 seconds                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIER 3: Human-in-the-Loop                          │
│                      (periodic calibration, ground truth)                    │
│                                                                             │
│  Platform: Argilla (self-hosted or Hugging Face Spaces)                     │
│                                                                             │
│  Annotation tasks:                                                          │
│  ├── Citation precision (human rates each citation)                         │
│  ├── Line range accuracy (too narrow / correct / too broad)                │
│  ├── Section quality (accuracy, completeness, clarity)                      │
│  └── Overall report usefulness                                              │
│                                                                             │
│  Output: annotated_dataset.json with human labels                           │
│  Cost: ~$1-5 per report (human time)                                       │
│  Latency: hours to days                                                     │
│                                                                             │
│  Purpose:                                                                   │
│  ├── Establish ground truth for metrics                                     │
│  ├── Calibrate LLM-as-judge prompts                                        │
│  ├── Identify failure modes                                                 │
│  └── Build training data for future improvements                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Evaluation Dashboard                             │
│                                                                             │
│  Aggregations:                                                              │
│  ├── Per-run metrics (single report)                                        │
│  ├── Per-repo metrics (same repo, different prompts)                        │
│  ├── Cross-repo metrics (different repos, similar prompts)                  │
│  └── Trend tracking over time / versions                                    │
│                                                                             │
│  Outputs:                                                                   │
│  ├── CI pass/fail gates                                                     │
│  ├── Regression alerts                                                      │
│  └── Quality reports for stakeholders                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tier 1: Automated Checks

### Implementation

Create `tech_writer/eval/automated.py`:

```python
"""
Automated evaluation checks that run without LLM calls.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from tech_writer.citations import extract_citations, verify_all_citations
from tech_writer.store import CacheStore


@dataclass
class AutomatedEvalResult:
    """Results from automated evaluation."""

    # Citation metrics
    citation_validity: float  # % of citations that resolve
    citation_coverage: float  # % of claims with citations
    total_citations: int
    valid_citations: int
    invalid_citations: int

    # Content metrics
    section_count: int
    total_words: int

    # Operational metrics
    files_cached: int
    exploration_efficiency: float  # files_cached / repo_files

    # Pass/fail
    passed: bool
    failures: list[str]


# Minimum thresholds for passing
CITATION_VALIDITY_THRESHOLD = 0.95
CITATION_COVERAGE_THRESHOLD = 0.50
MIN_SECTIONS = 1
MAX_SECTIONS = 50
MIN_WORDS = 100


def run_automated_eval(
    report: str,
    store: CacheStore,
    repo_root: Path,
    max_sections: int = 20,
) -> AutomatedEvalResult:
    """
    Run all automated evaluation checks.

    Args:
        report: Generated markdown report
        store: Cache store with read files
        repo_root: Repository root path
        max_sections: Expected maximum sections

    Returns:
        AutomatedEvalResult with all metrics
    """
    failures = []

    # Citation validity
    results, valid, invalid = verify_all_citations(report, store)
    total_citations = valid + invalid
    citation_validity = valid / total_citations if total_citations > 0 else 1.0

    if citation_validity < CITATION_VALIDITY_THRESHOLD:
        failures.append(
            f"Citation validity {citation_validity:.1%} below threshold {CITATION_VALIDITY_THRESHOLD:.1%}"
        )

    # Citation coverage
    claims = extract_claims(report)
    claims_with_citations = sum(1 for c in claims if has_citation(c))
    citation_coverage = claims_with_citations / len(claims) if claims else 0.0

    if citation_coverage < CITATION_COVERAGE_THRESHOLD:
        failures.append(
            f"Citation coverage {citation_coverage:.1%} below threshold {CITATION_COVERAGE_THRESHOLD:.1%}"
        )

    # Section count
    section_count = count_sections(report)
    if section_count < MIN_SECTIONS:
        failures.append(f"Only {section_count} sections, expected at least {MIN_SECTIONS}")
    if section_count > MAX_SECTIONS:
        failures.append(f"Too many sections ({section_count}), expected at most {MAX_SECTIONS}")

    # Word count
    total_words = len(report.split())
    if total_words < MIN_WORDS:
        failures.append(f"Report too short ({total_words} words)")

    # Exploration efficiency
    files_cached = len(store.list_cached_files())
    repo_files = count_repo_files(repo_root)
    exploration_efficiency = files_cached / repo_files if repo_files > 0 else 0.0

    return AutomatedEvalResult(
        citation_validity=citation_validity,
        citation_coverage=citation_coverage,
        total_citations=total_citations,
        valid_citations=valid,
        invalid_citations=invalid,
        section_count=section_count,
        total_words=total_words,
        files_cached=files_cached,
        exploration_efficiency=exploration_efficiency,
        passed=len(failures) == 0,
        failures=failures,
    )


def extract_claims(markdown: str) -> list[str]:
    """
    Extract factual claims from markdown.

    A claim is a sentence that makes a statement about the code.
    Excludes headers, code blocks, and meta-statements.
    """
    claims = []

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', markdown)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove headers
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Skip very short sentences
        if len(sentence.split()) < 4:
            continue
        # Skip meta-statements
        if sentence.lower().startswith(('this section', 'in this section', 'we will', 'let us')):
            continue
        claims.append(sentence)

    return claims


def has_citation(claim: str) -> bool:
    """Check if a claim contains a citation."""
    return bool(re.search(r'\[[^\]]+:\d+-\d+\]', claim))


def count_sections(markdown: str) -> int:
    """Count the number of ## sections in markdown."""
    return len(re.findall(r'^##\s+', markdown, flags=re.MULTILINE))


def count_repo_files(repo_root: Path) -> int:
    """Count total files in repository (excluding hidden/ignored)."""
    count = 0
    for path in repo_root.rglob('*'):
        if path.is_file():
            # Skip hidden files and common ignored patterns
            parts = path.relative_to(repo_root).parts
            if any(p.startswith('.') for p in parts):
                continue
            if any(p in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build') for p in parts):
                continue
            count += 1
    return count
```

### CLI Integration

Add `--eval` flag to CLI that runs automated checks after generation:

```bash
python -m tech_writer --prompt prompt.md --repo ./myrepo --eval
```

Output:
```
Citation validity: 97.2% (35/36 valid) ✓
Citation coverage: 82.1% (23/28 claims) ✓
Sections: 5 ✓
Words: 2,847 ✓
Exploration efficiency: 12.3% (15/122 files)

Evaluation: PASSED
```

## Tier 2: LLM-as-Judge

### Design Principles

Based on research into LLM-as-judge best practices:

1. **Criteria decomposition**: One evaluator per criterion. Don't ask a single prompt to rate "overall quality" - split into citation precision, faithfulness, completeness, coherence.

2. **Chain-of-thought**: Always ask the judge to explain reasoning before giving a score. This improves accuracy and enables debugging.

3. **Binary/simple over continuous**: Prefer yes/no questions or small discrete scales (0-3) over continuous scales (1-100). LLMs struggle with fine-grained distinctions.

4. **Additive rubrics**: When possible, use additive scoring where points are awarded for specific criteria:
   - +1 if the citation exists
   - +1 if the file path is correct
   - +1 if the line range contains relevant code
   - +1 if the code actually supports the claim

5. **Position randomization**: When comparing options, randomize order to avoid position bias.

6. **Multi-judge consensus**: For high-stakes evaluations, use multiple models (GPT-4, Claude, Gemini) and aggregate scores.

### Implementation

Create `tech_writer/eval/judge.py`:

```python
"""
LLM-as-judge evaluation for tech_writer outputs.
"""

import json
from dataclasses import dataclass
from typing import Optional

from tech_writer.llm import LLMClient


@dataclass
class CitationJudgment:
    """Judgment on a single citation."""
    citation: str
    claim: str
    cited_code: str
    supports_claim: bool
    reasoning: str
    confidence: str  # "high", "medium", "low"


@dataclass
class FaithfulnessJudgment:
    """Judgment on section faithfulness."""
    section_title: str
    score: int  # 0-3
    reasoning: str
    hallucinations: list[str]  # Claims not grounded in code


@dataclass
class CompletenessJudgment:
    """Judgment on report completeness."""
    score: int  # 0-3
    reasoning: str
    covered_topics: list[str]
    missing_topics: list[str]


@dataclass
class CoherenceJudgment:
    """Judgment on report coherence."""
    score: int  # 0-3
    reasoning: str
    issues: list[str]


@dataclass
class JudgeEvalResult:
    """Complete LLM-as-judge evaluation results."""
    citation_judgments: list[CitationJudgment]
    citation_precision: float
    faithfulness_judgments: list[FaithfulnessJudgment]
    faithfulness_score: float
    completeness: CompletenessJudgment
    coherence: CoherenceJudgment
    total_llm_calls: int
    total_tokens: int


CITATION_JUDGE_SYSTEM = """You are an expert code reviewer evaluating whether citations in technical documentation are accurate.

You will be given:
1. A claim from a technical document
2. A citation reference (file path and line numbers)
3. The actual code from those lines

Your task is to determine whether the cited code supports the claim being made.

Respond in JSON format:
{
  "supports_claim": true/false,
  "reasoning": "Step-by-step explanation of your judgment",
  "confidence": "high/medium/low"
}

Guidelines:
- A citation supports a claim if the code provides evidence for what the claim states
- The code doesn't need to be the ONLY evidence, just sufficient evidence
- Be strict: vague or tangential code should not count as support
- Consider whether the line range is appropriate (not too narrow or too broad)
"""

CITATION_JUDGE_USER = """Claim: {claim}

Citation: {citation}

Cited code:
```
{code}
```

Does this code support the claim? Respond in JSON format."""


FAITHFULNESS_JUDGE_SYSTEM = """You are an expert evaluating whether technical documentation is faithful to source code.

A document is "faithful" if all its claims are grounded in the source code - no hallucinations or made-up information.

You will be given:
1. A section of documentation
2. All the code that was cited in that section

Your task is to identify any claims that are NOT supported by the provided code.

Respond in JSON format:
{
  "score": 0-3,
  "reasoning": "Explanation of your assessment",
  "hallucinations": ["List of claims not grounded in the code"]
}

Scoring rubric:
- 0: Multiple significant hallucinations, section is unreliable
- 1: Some hallucinations or unsupported claims
- 2: Minor issues, mostly faithful
- 3: Fully faithful, all claims grounded in code
"""

FAITHFULNESS_JUDGE_USER = """Section: {section_title}

Documentation content:
{content}

All cited code from this section:
{all_cited_code}

Evaluate the faithfulness of this section. Respond in JSON format."""


COMPLETENESS_JUDGE_SYSTEM = """You are an expert evaluating whether technical documentation adequately addresses the user's request.

You will be given:
1. The original prompt/request from the user
2. The generated documentation

Your task is to assess whether the documentation covers what was asked for.

Respond in JSON format:
{
  "score": 0-3,
  "reasoning": "Explanation of your assessment",
  "covered_topics": ["Topics that were addressed"],
  "missing_topics": ["Topics that should have been covered but weren't"]
}

Scoring rubric:
- 0: Documentation doesn't address the prompt at all
- 1: Partially addresses the prompt, major gaps
- 2: Mostly addresses the prompt, minor gaps
- 3: Fully addresses the prompt
"""

COMPLETENESS_JUDGE_USER = """Original prompt:
{prompt}

Generated documentation:
{report}

Evaluate the completeness of this documentation. Respond in JSON format."""


COHERENCE_JUDGE_SYSTEM = """You are an expert evaluating the organization and flow of technical documentation.

You will be given a technical document and asked to assess its coherence.

Respond in JSON format:
{
  "score": 0-3,
  "reasoning": "Explanation of your assessment",
  "issues": ["List of specific coherence issues found"]
}

Consider:
- Do sections follow a logical order?
- Are transitions between sections smooth?
- Is terminology consistent throughout?
- Are there redundant or misplaced sections?
- Does the document have a clear structure?

Scoring rubric:
- 0: Incoherent, poorly organized, hard to follow
- 1: Some logical issues, inconsistent terminology
- 2: Generally coherent with minor issues
- 3: Well-organized, flows naturally, consistent
"""

COHERENCE_JUDGE_USER = """Document:
{report}

Evaluate the coherence of this document. Respond in JSON format."""


class JudgeEvaluator:
    """LLM-as-judge evaluator for tech_writer outputs."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.llm = LLMClient(model=model, api_key=api_key, base_url=base_url)
        self.total_calls = 0
        self.total_tokens = 0

    def judge_citation(
        self,
        claim: str,
        citation: str,
        cited_code: str,
    ) -> CitationJudgment:
        """
        Judge whether a citation supports its claim.

        Args:
            claim: The claim text from the report
            citation: The citation reference [path:start-end]
            cited_code: The actual code from those lines

        Returns:
            CitationJudgment with verdict and reasoning
        """
        messages = [
            {"role": "system", "content": CITATION_JUDGE_SYSTEM},
            {"role": "user", "content": CITATION_JUDGE_USER.format(
                claim=claim,
                citation=citation,
                code=cited_code,
            )},
        ]

        response = self.llm.chat(messages)
        self.total_calls += 1
        self.total_tokens += response.get("usage", {}).get("total_tokens", 0)

        # Parse JSON response
        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            # Try to extract JSON from response
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {
                    "supports_claim": False,
                    "reasoning": "Failed to parse judge response",
                    "confidence": "low",
                }

        return CitationJudgment(
            citation=citation,
            claim=claim,
            cited_code=cited_code,
            supports_claim=result.get("supports_claim", False),
            reasoning=result.get("reasoning", ""),
            confidence=result.get("confidence", "low"),
        )

    def judge_faithfulness(
        self,
        section_title: str,
        content: str,
        all_cited_code: str,
    ) -> FaithfulnessJudgment:
        """
        Judge whether a section is faithful to its cited code.

        Args:
            section_title: Title of the section
            content: Section markdown content
            all_cited_code: Concatenated code from all citations

        Returns:
            FaithfulnessJudgment with score and hallucinations
        """
        messages = [
            {"role": "system", "content": FAITHFULNESS_JUDGE_SYSTEM},
            {"role": "user", "content": FAITHFULNESS_JUDGE_USER.format(
                section_title=section_title,
                content=content,
                all_cited_code=all_cited_code,
            )},
        ]

        response = self.llm.chat(messages)
        self.total_calls += 1
        self.total_tokens += response.get("usage", {}).get("total_tokens", 0)

        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"score": 0, "reasoning": "Parse error", "hallucinations": []}

        return FaithfulnessJudgment(
            section_title=section_title,
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            hallucinations=result.get("hallucinations", []),
        )

    def judge_completeness(
        self,
        prompt: str,
        report: str,
    ) -> CompletenessJudgment:
        """
        Judge whether the report addresses the prompt.

        Args:
            prompt: Original user prompt
            report: Generated report

        Returns:
            CompletenessJudgment with score and topic analysis
        """
        messages = [
            {"role": "system", "content": COMPLETENESS_JUDGE_SYSTEM},
            {"role": "user", "content": COMPLETENESS_JUDGE_USER.format(
                prompt=prompt,
                report=report,
            )},
        ]

        response = self.llm.chat(messages)
        self.total_calls += 1
        self.total_tokens += response.get("usage", {}).get("total_tokens", 0)

        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"score": 0, "reasoning": "Parse error", "covered_topics": [], "missing_topics": []}

        return CompletenessJudgment(
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            covered_topics=result.get("covered_topics", []),
            missing_topics=result.get("missing_topics", []),
        )

    def judge_coherence(self, report: str) -> CoherenceJudgment:
        """
        Judge the coherence of the report.

        Args:
            report: Generated report

        Returns:
            CoherenceJudgment with score and issues
        """
        messages = [
            {"role": "system", "content": COHERENCE_JUDGE_SYSTEM},
            {"role": "user", "content": COHERENCE_JUDGE_USER.format(report=report)},
        ]

        response = self.llm.chat(messages)
        self.total_calls += 1
        self.total_tokens += response.get("usage", {}).get("total_tokens", 0)

        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"score": 0, "reasoning": "Parse error", "issues": []}

        return CoherenceJudgment(
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            issues=result.get("issues", []),
        )


def run_judge_eval(
    report: str,
    prompt: str,
    store: CacheStore,
    model: str = "gpt-4o",
) -> JudgeEvalResult:
    """
    Run complete LLM-as-judge evaluation.

    Args:
        report: Generated markdown report
        prompt: Original user prompt
        store: Cache store with file contents
        model: LLM model to use as judge

    Returns:
        JudgeEvalResult with all judgments and scores
    """
    from tech_writer.citations import extract_citations, verify_citation

    evaluator = JudgeEvaluator(model=model)

    # Extract and judge citations
    citations = extract_citations(report)
    citation_judgments = []

    for citation in citations:
        # Get the claim surrounding this citation
        claim = extract_claim_for_citation(report, citation)

        # Get the cited code
        result = verify_citation(citation, store)
        if result.valid and result.content:
            judgment = evaluator.judge_citation(
                claim=claim,
                citation=f"[{citation.path}:{citation.start_line}-{citation.end_line}]",
                cited_code=result.content,
            )
            citation_judgments.append(judgment)

    # Calculate citation precision
    if citation_judgments:
        supporting = sum(1 for j in citation_judgments if j.supports_claim)
        citation_precision = supporting / len(citation_judgments)
    else:
        citation_precision = 0.0

    # Judge faithfulness per section
    sections = extract_sections(report)
    faithfulness_judgments = []

    for title, content in sections:
        # Get all code cited in this section
        section_citations = extract_citations(content)
        all_code_parts = []
        for cit in section_citations:
            result = verify_citation(cit, store)
            if result.valid and result.content:
                all_code_parts.append(f"# {cit.path}:{cit.start_line}-{cit.end_line}\n{result.content}")

        all_cited_code = "\n\n".join(all_code_parts) if all_code_parts else "(no citations)"

        judgment = evaluator.judge_faithfulness(
            section_title=title,
            content=content,
            all_cited_code=all_cited_code,
        )
        faithfulness_judgments.append(judgment)

    # Calculate average faithfulness
    if faithfulness_judgments:
        faithfulness_score = sum(j.score for j in faithfulness_judgments) / (3 * len(faithfulness_judgments))
    else:
        faithfulness_score = 0.0

    # Judge completeness
    completeness = evaluator.judge_completeness(prompt, report)

    # Judge coherence
    coherence = evaluator.judge_coherence(report)

    return JudgeEvalResult(
        citation_judgments=citation_judgments,
        citation_precision=citation_precision,
        faithfulness_judgments=faithfulness_judgments,
        faithfulness_score=faithfulness_score,
        completeness=completeness,
        coherence=coherence,
        total_llm_calls=evaluator.total_calls,
        total_tokens=evaluator.total_tokens,
    )


def extract_claim_for_citation(report: str, citation) -> str:
    """Extract the sentence/claim containing a citation."""
    citation_str = f"[{citation.path}:{citation.start_line}-{citation.end_line}]"

    # Find the citation in the report
    idx = report.find(citation_str)
    if idx == -1:
        return ""

    # Find sentence boundaries
    start = report.rfind(".", 0, idx)
    start = start + 1 if start != -1 else 0

    end = report.find(".", idx)
    end = end + 1 if end != -1 else len(report)

    return report[start:end].strip()


def extract_sections(report: str) -> list[tuple[str, str]]:
    """Extract sections from markdown report."""
    import re

    sections = []
    current_title = "Introduction"
    current_content = []

    for line in report.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections.append((current_title, "\n".join(current_content)))
            current_title = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append((current_title, "\n".join(current_content)))

    return sections
```

### CLI Integration

Add `--eval-judge` flag:

```bash
python -m tech_writer --prompt prompt.md --repo ./myrepo --eval --eval-judge
```

Output:
```
=== Automated Evaluation ===
Citation validity: 97.2% ✓
Citation coverage: 82.1% ✓
...

=== LLM-as-Judge Evaluation ===
Citation precision: 88.9% (32/36 supporting)
Faithfulness: 0.83 (avg 2.5/3.0)
Completeness: 2/3 - "Covers main topics but missing error handling section"
Coherence: 3/3 - "Well-organized with clear transitions"

LLM calls: 42
Tokens used: 28,450

Evaluation: PASSED
```

## Tier 3: Human-in-the-Loop (Argilla)

### Platform Overview

Argilla is an open-source data curation platform for building high-quality datasets with human feedback. Key features:

- **Web UI**: Browser-based annotation interface
- **Python SDK**: Programmatic dataset management
- **Flexible questions**: Rating scales, labels, text input, rankings
- **Collaboration**: Multiple annotators, workload distribution
- **Export**: JSON, CSV, Parquet, Hugging Face datasets

### Deployment Options

#### Option A: Hugging Face Spaces (Recommended)

Free hosting, no infrastructure to manage.

1. Go to https://huggingface.co/new-space
2. Select "Argilla" template
3. Configure Space (name, visibility)
4. Deploy (takes ~2 minutes)
5. Get API URL and key from Space settings

#### Option B: Self-Hosted (Docker)

For private/on-premise deployment:

```bash
# Pull and run Argilla server
docker run -d \
  --name argilla \
  -p 6900:6900 \
  -e ARGILLA_AUTH_SECRET_KEY=your-secret-key \
  argilla/argilla-server:latest

# Access at http://localhost:6900
# Default credentials: admin / 12345678
```

#### Option C: Docker Compose (with Elasticsearch)

For production with persistent storage:

```yaml
# docker-compose.yml
version: "3.8"

services:
  argilla:
    image: argilla/argilla-server:latest
    ports:
      - "6900:6900"
    environment:
      ARGILLA_ELASTICSEARCH: http://elasticsearch:9200
      ARGILLA_AUTH_SECRET_KEY: your-secret-key
    depends_on:
      - elasticsearch

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  elasticsearch_data:
```

### Dataset Schema for tech_writer

Create `tech_writer/eval/argilla_setup.py`:

```python
"""
Argilla dataset setup for tech_writer evaluation.
"""

import argilla as rg
from typing import Optional


def create_citation_dataset(
    client: rg.Argilla,
    dataset_name: str = "tech_writer_citations",
    workspace: str = "default",
) -> rg.Dataset:
    """
    Create Argilla dataset for citation evaluation.

    Fields:
    - claim: The claim text from the report
    - citation: The citation reference [path:line-line]
    - cited_code: The actual code from those lines
    - context: Surrounding paragraph for context

    Questions:
    - support_score: Does the code support the claim? (0-3)
    - line_range: Is the line range appropriate?
    - correction: What should the citation be? (optional text)
    - notes: Annotator notes (optional text)
    """
    settings = rg.Settings(
        fields=[
            rg.TextField(
                name="claim",
                title="Claim from report",
                use_markdown=False,
            ),
            rg.TextField(
                name="citation",
                title="Citation reference",
                use_markdown=False,
            ),
            rg.TextField(
                name="cited_code",
                title="Cited code",
                use_markdown=True,  # Renders as code block
            ),
            rg.TextField(
                name="context",
                title="Surrounding context",
                use_markdown=True,
            ),
        ],
        questions=[
            rg.RatingQuestion(
                name="support_score",
                title="Does the cited code support the claim?",
                description=(
                    "0 = No support (code is unrelated)\n"
                    "1 = Weak support (tangentially related)\n"
                    "2 = Partial support (supports part of claim)\n"
                    "3 = Full support (code clearly supports claim)"
                ),
                values=[0, 1, 2, 3],
                required=True,
            ),
            rg.LabelQuestion(
                name="line_range",
                title="Is the line range appropriate?",
                description="Does the citation include the right amount of code?",
                labels={
                    "too_narrow": "Too narrow - missing relevant context",
                    "correct": "Correct - appropriate scope",
                    "too_broad": "Too broad - includes unrelated code",
                },
                required=True,
            ),
            rg.TextQuestion(
                name="correction",
                title="If incorrect, what should the citation be?",
                description="Provide the correct file:line-line if the citation is wrong",
                required=False,
            ),
            rg.TextQuestion(
                name="notes",
                title="Additional notes",
                description="Any other observations about this citation",
                required=False,
            ),
        ],
        guidelines=(
            "# Citation Evaluation Guidelines\n\n"
            "You are evaluating whether citations in AI-generated documentation "
            "correctly support the claims they're attached to.\n\n"
            "## Support Score\n"
            "- **0 (No support)**: The code has nothing to do with the claim\n"
            "- **1 (Weak)**: The code is tangentially related but doesn't really support the claim\n"
            "- **2 (Partial)**: The code supports part of the claim, or the claim overstates what the code shows\n"
            "- **3 (Full)**: The code clearly and directly supports what the claim states\n\n"
            "## Line Range\n"
            "- **Too narrow**: Important context is missing that would be needed to understand the code\n"
            "- **Correct**: The citation includes the right functions/classes without extra noise\n"
            "- **Too broad**: The citation includes a lot of unrelated code\n\n"
            "## When in Doubt\n"
            "- Be strict: if you're unsure whether code supports a claim, lean toward lower scores\n"
            "- Consider whether a reader would find this citation helpful\n"
        ),
    )

    dataset = rg.Dataset(
        name=dataset_name,
        workspace=workspace,
        settings=settings,
    )

    dataset.create()
    return dataset


def create_section_dataset(
    client: rg.Argilla,
    dataset_name: str = "tech_writer_sections",
    workspace: str = "default",
) -> rg.Dataset:
    """
    Create Argilla dataset for section-level evaluation.

    Fields:
    - section_title: Title of the section
    - section_content: Full section markdown
    - prompt: Original user prompt (for context)

    Questions:
    - accuracy: Is the content technically accurate?
    - completeness: Does it cover the topic adequately?
    - clarity: Is it clear and well-written?
    - usefulness: Would this be useful to a developer?
    """
    settings = rg.Settings(
        fields=[
            rg.TextField(
                name="section_title",
                title="Section title",
                use_markdown=False,
            ),
            rg.TextField(
                name="section_content",
                title="Section content",
                use_markdown=True,
            ),
            rg.TextField(
                name="prompt",
                title="Original prompt",
                use_markdown=False,
            ),
        ],
        questions=[
            rg.RatingQuestion(
                name="accuracy",
                title="Technical accuracy",
                description="Are the technical statements correct?",
                values=[1, 2, 3, 4, 5],
                required=True,
            ),
            rg.RatingQuestion(
                name="completeness",
                title="Completeness",
                description="Does it cover the topic adequately?",
                values=[1, 2, 3, 4, 5],
                required=True,
            ),
            rg.RatingQuestion(
                name="clarity",
                title="Clarity",
                description="Is it clear and well-written?",
                values=[1, 2, 3, 4, 5],
                required=True,
            ),
            rg.RatingQuestion(
                name="usefulness",
                title="Usefulness",
                description="Would this be useful to a developer?",
                values=[1, 2, 3, 4, 5],
                required=True,
            ),
            rg.TextQuestion(
                name="issues",
                title="Issues found",
                description="Describe any problems with this section",
                required=False,
            ),
        ],
        guidelines=(
            "# Section Evaluation Guidelines\n\n"
            "Rate each section on four dimensions using a 1-5 scale.\n\n"
            "## Accuracy (1-5)\n"
            "- 1: Multiple incorrect statements\n"
            "- 3: Mostly correct with minor errors\n"
            "- 5: Completely accurate\n\n"
            "## Completeness (1-5)\n"
            "- 1: Major gaps, missing key information\n"
            "- 3: Covers basics but lacks depth\n"
            "- 5: Thoroughly covers the topic\n\n"
            "## Clarity (1-5)\n"
            "- 1: Confusing, poorly organized\n"
            "- 3: Understandable but could be clearer\n"
            "- 5: Crystal clear, well-structured\n\n"
            "## Usefulness (1-5)\n"
            "- 1: Not helpful for understanding the code\n"
            "- 3: Somewhat helpful\n"
            "- 5: Very helpful, would save significant time\n"
        ),
    )

    dataset = rg.Dataset(
        name=dataset_name,
        workspace=workspace,
        settings=settings,
    )

    dataset.create()
    return dataset


def upload_citations_for_review(
    client: rg.Argilla,
    dataset_name: str,
    report: str,
    store,  # CacheStore
) -> int:
    """
    Upload citations from a report to Argilla for human review.

    Args:
        client: Argilla client
        dataset_name: Name of the citation dataset
        report: Generated markdown report
        store: Cache store with file contents

    Returns:
        Number of records uploaded
    """
    from tech_writer.citations import extract_citations, verify_citation

    dataset = client.datasets(name=dataset_name)

    citations = extract_citations(report)
    records = []

    for citation in citations:
        # Get claim and context
        claim = extract_claim_for_citation(report, citation)
        context = extract_context_for_citation(report, citation)

        # Get cited code
        result = verify_citation(citation, store)
        if not result.valid:
            continue

        citation_str = f"[{citation.path}:{citation.start_line}-{citation.end_line}]"

        records.append(
            rg.Record(
                fields={
                    "claim": claim,
                    "citation": citation_str,
                    "cited_code": f"```\n{result.content}\n```",
                    "context": context,
                },
            )
        )

    dataset.records.log(records)
    return len(records)


def extract_claim_for_citation(report: str, citation) -> str:
    """Extract the sentence containing a citation."""
    citation_str = f"[{citation.path}:{citation.start_line}-{citation.end_line}]"

    idx = report.find(citation_str)
    if idx == -1:
        return ""

    # Find sentence boundaries
    start = report.rfind(".", 0, idx)
    start = start + 1 if start != -1 else 0

    end = report.find(".", idx)
    end = end + 1 if end != -1 else len(report)

    return report[start:end].strip()


def extract_context_for_citation(report: str, citation) -> str:
    """Extract surrounding paragraph for context."""
    citation_str = f"[{citation.path}:{citation.start_line}-{citation.end_line}]"

    idx = report.find(citation_str)
    if idx == -1:
        return ""

    # Find paragraph boundaries (double newline)
    start = report.rfind("\n\n", 0, idx)
    start = start + 2 if start != -1 else 0

    end = report.find("\n\n", idx)
    end = end if end != -1 else len(report)

    return report[start:end].strip()


def export_annotations(
    client: rg.Argilla,
    dataset_name: str,
    output_path: str,
) -> dict:
    """
    Export annotations from Argilla dataset.

    Args:
        client: Argilla client
        dataset_name: Name of the dataset
        output_path: Path to save JSON export

    Returns:
        Summary statistics
    """
    import json

    dataset = client.datasets(name=dataset_name)

    records = list(dataset.records)

    annotations = []
    for record in records:
        if record.responses:
            annotations.append({
                "fields": record.fields,
                "responses": [
                    {
                        "user": r.user_id,
                        "values": {k: v.value for k, v in r.values.items()},
                    }
                    for r in record.responses
                ],
            })

    with open(output_path, "w") as f:
        json.dump(annotations, f, indent=2)

    # Compute statistics
    total = len(records)
    annotated = len(annotations)

    if annotations:
        support_scores = []
        for ann in annotations:
            for resp in ann["responses"]:
                if "support_score" in resp["values"]:
                    support_scores.append(resp["values"]["support_score"])

        avg_support = sum(support_scores) / len(support_scores) if support_scores else 0
    else:
        avg_support = 0

    return {
        "total_records": total,
        "annotated_records": annotated,
        "annotation_rate": annotated / total if total > 0 else 0,
        "avg_support_score": avg_support,
    }
```

### Workflow: Calibrating LLM Judge with Human Annotations

```python
"""
Workflow for calibrating LLM-as-judge against human annotations.
"""

import json
from scipy.stats import spearmanr, pearsonr
import argilla as rg

from tech_writer.eval.judge import JudgeEvaluator
from tech_writer.eval.argilla_setup import export_annotations


def calibrate_judge(
    argilla_client: rg.Argilla,
    citation_dataset: str,
    judge_model: str = "gpt-4o",
) -> dict:
    """
    Compare LLM judge scores against human annotations.

    Args:
        argilla_client: Argilla client
        citation_dataset: Name of annotated citation dataset
        judge_model: Model to use as judge

    Returns:
        Calibration results with correlation metrics
    """
    # Export human annotations
    annotations = export_annotations(
        argilla_client,
        citation_dataset,
        "/tmp/annotations.json",
    )

    with open("/tmp/annotations.json") as f:
        data = json.load(f)

    # Run LLM judge on same citations
    evaluator = JudgeEvaluator(model=judge_model)

    human_scores = []
    llm_scores = []
    disagreements = []

    for item in data:
        fields = item["fields"]
        human_responses = item["responses"]

        # Get average human score
        human_support = [
            r["values"]["support_score"]
            for r in human_responses
            if "support_score" in r["values"]
        ]
        if not human_support:
            continue
        avg_human = sum(human_support) / len(human_support)

        # Get LLM judgment
        judgment = evaluator.judge_citation(
            claim=fields["claim"],
            citation=fields["citation"],
            cited_code=fields["cited_code"].strip("`\n"),
        )

        # Convert bool to 0-3 scale for comparison
        # This is a simplification; could use confidence for finer scores
        llm_score = 3 if judgment.supports_claim else 0

        human_scores.append(avg_human)
        llm_scores.append(llm_score)

        # Track disagreements
        if abs(avg_human - llm_score) > 1.5:
            disagreements.append({
                "claim": fields["claim"],
                "citation": fields["citation"],
                "human_score": avg_human,
                "llm_score": llm_score,
                "llm_reasoning": judgment.reasoning,
            })

    # Compute correlations
    if len(human_scores) >= 3:
        spearman_corr, spearman_p = spearmanr(human_scores, llm_scores)
        pearson_corr, pearson_p = pearsonr(human_scores, llm_scores)
    else:
        spearman_corr = spearman_p = pearson_corr = pearson_p = None

    # Compute agreement rate
    agreements = sum(
        1 for h, l in zip(human_scores, llm_scores)
        if abs(h - l) <= 1  # Within 1 point
    )
    agreement_rate = agreements / len(human_scores) if human_scores else 0

    return {
        "n_samples": len(human_scores),
        "spearman_correlation": spearman_corr,
        "spearman_p_value": spearman_p,
        "pearson_correlation": pearson_corr,
        "pearson_p_value": pearson_p,
        "agreement_rate": agreement_rate,
        "n_disagreements": len(disagreements),
        "disagreements": disagreements[:10],  # Top 10 for review
        "recommendation": (
            "GOOD: LLM judge is well-calibrated"
            if agreement_rate > 0.7 and (spearman_corr or 0) > 0.6
            else "NEEDS WORK: Review disagreements and refine judge prompts"
        ),
    }
```

### Inter-Annotator Agreement

For reliable human evaluation, measure agreement between annotators:

```python
"""
Inter-annotator agreement metrics.
"""

from collections import defaultdict
from itertools import combinations


def compute_inter_annotator_agreement(annotations: list[dict]) -> dict:
    """
    Compute agreement metrics between annotators.

    Args:
        annotations: List of annotation records with multiple responses

    Returns:
        Agreement metrics (Krippendorff's alpha, pairwise agreement)
    """
    # Group by record
    records_with_multiple = [
        ann for ann in annotations
        if len(ann["responses"]) >= 2
    ]

    if not records_with_multiple:
        return {"error": "No records with multiple annotations"}

    # Compute pairwise agreement for support_score
    agreements = []
    for record in records_with_multiple:
        scores = [
            r["values"]["support_score"]
            for r in record["responses"]
            if "support_score" in r["values"]
        ]

        for s1, s2 in combinations(scores, 2):
            # Exact agreement
            agreements.append(1 if s1 == s2 else 0)

    exact_agreement = sum(agreements) / len(agreements) if agreements else 0

    # Within-1 agreement (more lenient)
    within_1 = []
    for record in records_with_multiple:
        scores = [
            r["values"]["support_score"]
            for r in record["responses"]
            if "support_score" in r["values"]
        ]

        for s1, s2 in combinations(scores, 2):
            within_1.append(1 if abs(s1 - s2) <= 1 else 0)

    within_1_agreement = sum(within_1) / len(within_1) if within_1 else 0

    return {
        "n_records_with_multiple": len(records_with_multiple),
        "exact_agreement": exact_agreement,
        "within_1_agreement": within_1_agreement,
        "interpretation": (
            "GOOD: Annotators agree well"
            if within_1_agreement > 0.8
            else "FAIR: Some disagreement, review guidelines"
            if within_1_agreement > 0.6
            else "POOR: High disagreement, need clearer guidelines"
        ),
    }
```

## Integration: Running the Full Evaluation Pipeline

### Complete Evaluation Script

Create `tech_writer/eval/run_eval.py`:

```python
"""
Complete evaluation pipeline for tech_writer outputs.
"""

import argparse
import json
from pathlib import Path
from typing import Optional

from tech_writer.orchestrator import run_pipeline
from tech_writer.eval.automated import run_automated_eval, AutomatedEvalResult
from tech_writer.eval.judge import run_judge_eval, JudgeEvalResult


def run_full_evaluation(
    prompt_path: str,
    repo_path: str,
    output_dir: str,
    run_judge: bool = False,
    judge_model: str = "gpt-4o",
) -> dict:
    """
    Run tech_writer and evaluate the output.

    Args:
        prompt_path: Path to prompt file
        repo_path: Path to repository
        output_dir: Directory for outputs
        run_judge: Whether to run LLM-as-judge evaluation
        judge_model: Model for judge evaluation

    Returns:
        Complete evaluation results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read prompt
    prompt = Path(prompt_path).read_text()

    # Generate report
    print("Generating report...")
    report, store = run_pipeline(
        prompt=prompt,
        repo=repo_path,
        db_path=str(output_dir / "cache.db"),
    )

    # Save report
    report_path = output_dir / "report.md"
    report_path.write_text(report)
    print(f"Report saved to {report_path}")

    # Run automated evaluation
    print("\nRunning automated evaluation...")
    repo_root = Path(repo_path)
    auto_result = run_automated_eval(report, store, repo_root)

    print(f"  Citation validity: {auto_result.citation_validity:.1%}")
    print(f"  Citation coverage: {auto_result.citation_coverage:.1%}")
    print(f"  Sections: {auto_result.section_count}")
    print(f"  Words: {auto_result.total_words}")
    print(f"  Files explored: {auto_result.files_cached}")
    print(f"  Exploration efficiency: {auto_result.exploration_efficiency:.1%}")

    if auto_result.passed:
        print("  Status: PASSED ✓")
    else:
        print("  Status: FAILED ✗")
        for failure in auto_result.failures:
            print(f"    - {failure}")

    results = {
        "automated": {
            "citation_validity": auto_result.citation_validity,
            "citation_coverage": auto_result.citation_coverage,
            "total_citations": auto_result.total_citations,
            "valid_citations": auto_result.valid_citations,
            "invalid_citations": auto_result.invalid_citations,
            "section_count": auto_result.section_count,
            "total_words": auto_result.total_words,
            "files_cached": auto_result.files_cached,
            "exploration_efficiency": auto_result.exploration_efficiency,
            "passed": auto_result.passed,
            "failures": auto_result.failures,
        }
    }

    # Run LLM-as-judge evaluation
    if run_judge:
        print("\nRunning LLM-as-judge evaluation...")
        judge_result = run_judge_eval(report, prompt, store, model=judge_model)

        print(f"  Citation precision: {judge_result.citation_precision:.1%}")
        print(f"  Faithfulness score: {judge_result.faithfulness_score:.2f}")
        print(f"  Completeness: {judge_result.completeness.score}/3")
        print(f"  Coherence: {judge_result.coherence.score}/3")
        print(f"  LLM calls: {judge_result.total_llm_calls}")
        print(f"  Tokens used: {judge_result.total_tokens:,}")

        results["judge"] = {
            "citation_precision": judge_result.citation_precision,
            "faithfulness_score": judge_result.faithfulness_score,
            "completeness_score": judge_result.completeness.score,
            "completeness_reasoning": judge_result.completeness.reasoning,
            "completeness_missing": judge_result.completeness.missing_topics,
            "coherence_score": judge_result.coherence.score,
            "coherence_reasoning": judge_result.coherence.reasoning,
            "coherence_issues": judge_result.coherence.issues,
            "total_llm_calls": judge_result.total_llm_calls,
            "total_tokens": judge_result.total_tokens,
        }

        # Save detailed citation judgments
        citation_details = [
            {
                "citation": j.citation,
                "claim": j.claim,
                "supports": j.supports_claim,
                "reasoning": j.reasoning,
                "confidence": j.confidence,
            }
            for j in judge_result.citation_judgments
        ]

        citations_path = output_dir / "citation_judgments.json"
        citations_path.write_text(json.dumps(citation_details, indent=2))
        print(f"\nCitation judgments saved to {citations_path}")

    # Save results
    results_path = output_dir / "eval_results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nEvaluation results saved to {results_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate tech_writer output")
    parser.add_argument("--prompt", required=True, help="Path to prompt file")
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--output", default="./eval_output", help="Output directory")
    parser.add_argument("--judge", action="store_true", help="Run LLM-as-judge evaluation")
    parser.add_argument("--judge-model", default="gpt-4o", help="Model for judge")

    args = parser.parse_args()

    run_full_evaluation(
        prompt_path=args.prompt,
        repo_path=args.repo,
        output_dir=args.output,
        run_judge=args.judge,
        judge_model=args.judge_model,
    )


if __name__ == "__main__":
    main()
```

### CI Integration

Example GitHub Actions workflow:

```yaml
# .github/workflows/eval.yml
name: Evaluation

on:
  push:
    branches: [main]
  pull_request:

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest

      - name: Run automated evaluation
        run: |
          python -m tech_writer.eval.run_eval \
            --prompt tests/fixtures/prompts/api_docs.md \
            --repo tests/fixtures/sample_flask_app \
            --output eval_results

      - name: Check evaluation passed
        run: |
          python -c "
          import json
          with open('eval_results/eval_results.json') as f:
              results = json.load(f)
          if not results['automated']['passed']:
              print('Evaluation failed:')
              for f in results['automated']['failures']:
                  print(f'  - {f}')
              exit(1)
          print('Evaluation passed!')
          "

      - name: Upload evaluation artifacts
        uses: actions/upload-artifact@v4
        with:
          name: eval-results
          path: eval_results/
```

## Reference Test: Axios Repository

### Test Setup

Create `tests/e2e/test_axios_eval.py`:

```python
"""
End-to-end evaluation test using axios repository.
"""

import os
import pytest
from pathlib import Path

from tech_writer.orchestrator import run_pipeline
from tech_writer.eval.automated import run_automated_eval
from tech_writer.eval.judge import run_judge_eval
from tech_writer.repo import resolve_repo


AXIOS_REPO = "https://github.com/axios/axios"
SKIP_AXIOS = os.environ.get("SKIP_AXIOS_TEST", "").lower() in ("1", "true", "yes")


@pytest.fixture(scope="module")
def axios_repo(tmp_path_factory):
    """Clone axios repository for testing."""
    if SKIP_AXIOS:
        pytest.skip("Axios test skipped via SKIP_AXIOS_TEST")

    cache_dir = tmp_path_factory.mktemp("repos")
    repo_path, _ = resolve_repo(AXIOS_REPO, str(cache_dir))
    return repo_path


class TestAxiosEvaluation:
    """Evaluation tests against axios repository."""

    PROMPT = """
    Document the architecture of axios, a popular HTTP client library.

    Cover:
    1. Core request/response flow
    2. Interceptor system
    3. Adapter pattern (browser vs node)
    4. Configuration and defaults

    Include code citations for all claims.
    """

    def test_generates_report_with_citations(self, axios_repo, tmp_path):
        """Test that report is generated with valid citations."""
        report, store = run_pipeline(
            prompt=self.PROMPT,
            repo=str(axios_repo),
            max_exploration=30,
            max_sections=6,
            db_path=str(tmp_path / "cache.db"),
        )

        # Basic checks
        assert len(report) > 1000, "Report too short"
        assert "[" in report and ":" in report, "No citations found"

        # Automated evaluation
        auto_result = run_automated_eval(report, store, axios_repo)

        assert auto_result.citation_validity >= 0.90, \
            f"Citation validity {auto_result.citation_validity:.1%} below 90%"

        assert auto_result.citation_coverage >= 0.50, \
            f"Citation coverage {auto_result.citation_coverage:.1%} below 50%"

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_citation_precision_with_judge(self, axios_repo, tmp_path):
        """Test citation precision using LLM judge."""
        report, store = run_pipeline(
            prompt=self.PROMPT,
            repo=str(axios_repo),
            max_exploration=30,
            max_sections=6,
            db_path=str(tmp_path / "cache.db"),
        )

        judge_result = run_judge_eval(report, self.PROMPT, store)

        assert judge_result.citation_precision >= 0.80, \
            f"Citation precision {judge_result.citation_precision:.1%} below 80%"

        assert judge_result.faithfulness_score >= 0.70, \
            f"Faithfulness {judge_result.faithfulness_score:.2f} below 0.70"

        assert judge_result.completeness.score >= 2, \
            f"Completeness {judge_result.completeness.score}/3 below 2"
```

### Reference Prompt

Create `prompts/architecture-overview-lite.prompt.txt`:

```
Document the architecture of this codebase.

Focus on:
1. High-level structure and organization
2. Core abstractions and their responsibilities
3. Data flow through the system
4. Extension points and configuration

Requirements:
- Every factual claim must include a citation in [file:line-line] format
- Focus on architecture, not implementation details
- Target length: 1500-3000 words
- Structure: Introduction, 3-5 topic sections, Conclusion
```

## Metrics Summary Table

| Metric | Type | Threshold | Tier | Implementation |
|--------|------|-----------|------|----------------|
| Citation validity | Automated | >95% | 1 | Complete |
| Citation coverage | Automated | >50% | 1 | Not implemented |
| Section count | Automated | 1-50 | 1 | Not implemented |
| Word count | Automated | >100 | 1 | Not implemented |
| Exploration efficiency | Automated | 5-30% | 1 | Partial |
| Citation precision | LLM Judge | >85% | 2 | Not implemented |
| Faithfulness | LLM Judge | >0.85 | 2 | Not implemented |
| Completeness | LLM Judge | ≥2/3 | 2 | Not implemented |
| Coherence | LLM Judge | ≥2/3 | 2 | Not implemented |
| Human citation score | HIL | Ground truth | 3 | Not implemented |
| Human section quality | HIL | Ground truth | 3 | Not implemented |
| LLM-human correlation | Calibration | >0.6 | 3 | Not implemented |

## Implementation Roadmap

### Phase 1: Automated Baseline

**Tasks:**
1. Implement `tech_writer/eval/automated.py` with all automated checks
2. Add `--eval` flag to CLI
3. Add CI workflow for automated checks
4. Create threshold constants in config

**Effort:** 1-2 days
**Dependencies:** None

### Phase 2: LLM-as-Judge

**Tasks:**
1. Implement `tech_writer/eval/judge.py` with all judge functions
2. Add `--eval-judge` flag to CLI
3. Create judge prompt templates
4. Add token usage tracking
5. Write tests for judge functions

**Effort:** 2-3 days
**Dependencies:** Phase 1

### Phase 3: Argilla Integration

**Tasks:**
1. Implement `tech_writer/eval/argilla_setup.py`
2. Create datasets for citation and section evaluation
3. Build upload/export scripts
4. Document Argilla setup process
5. Create annotation guidelines

**Effort:** 2-3 days
**Dependencies:** None (parallel with Phase 2)

### Phase 4: Calibration

**Tasks:**
1. Generate reports for 3-5 repos
2. Upload to Argilla, collect human annotations
3. Run calibration analysis
4. Refine judge prompts based on disagreements
5. Document calibration results

**Effort:** 1-2 weeks (includes annotation time)
**Dependencies:** Phases 2, 3

### Phase 5: CI Integration

**Tasks:**
1. Create comprehensive CI workflow
2. Add regression tracking
3. Build evaluation dashboard (optional)
4. Create axios reference test

**Effort:** 1-2 days
**Dependencies:** Phases 1, 2

## Sources

### HIL Tools
- [Argilla GitHub Repository](https://github.com/argilla-io/argilla)
- [Argilla for LLMs Blog Post](https://argilla.io/blog/argilla-for-llms/)
- [Data Annotation with Argilla Spaces - Hugging Face Cookbook](https://huggingface.co/learn/cookbook/enterprise_cookbook_argilla)
- [Argilla RLHF Documentation](https://argilla.io/blog/mantisnlp-rlhf-part-2/)

### LLM-as-Judge
- [LLM-as-a-Judge Complete Guide (EvidentlyAI)](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)
- [LLM-as-Judge Best Practices (Monte Carlo Data)](https://www.montecarlodata.com/blog-llm-as-judge/)
- [Evaluating LLM Evaluators (Eugene Yan)](https://eugeneyan.com/writing/llm-evaluators/)
- [Using LLM-as-a-judge - Hugging Face Cookbook](https://huggingface.co/learn/cookbook/en/llm_judge)
- [LLM-as-a-Judge (Cameron Wolfe)](https://cameronrwolfe.substack.com/p/llm-as-a-judge)
- [LLM-as-a-Judge (Confident AI)](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method)
- [LLM as a Judge (Arize AI)](https://arize.com/llm-as-a-judge/)

### RAG Evaluation
- [RAG Evaluation Metrics (Confident AI)](https://www.confident-ai.com/blog/rag-evaluation-metrics-answer-relevancy-faithfulness-and-more)
- [RAGAS Documentation - Available Metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [RAGAS for RAG Guide (Medium)](https://dkaarthick.medium.com/ragas-for-rag-in-llms-a-comprehensive-guide-to-evaluation-metrics-3aca142d6e38)
- [RAG Evaluation Survey (arXiv)](https://arxiv.org/html/2405.07437v2)
- [Awesome RAG Evaluation (GitHub)](https://github.com/YHPeter/Awesome-RAG-Evaluation)

### General LLM Evaluation
- [LLM Evaluation Metrics (Confident AI)](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation)
- [Evaluation Metrics List (Microsoft)](https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/generative-ai/working-with-llms/evaluation/list-of-eval-metrics)
- [LLM Evaluation Guide (Weights & Biases)](https://wandb.ai/onlineinference/genai-research/reports/LLM-evaluation-Metrics-frameworks-and-best-practices--VmlldzoxMTMxNjQ4NA)
- [LLM Evaluation Guide (SuperAnnotate)](https://www.superannotate.com/blog/llm-evaluation-guide)
- [Evaluating LLM Systems (Microsoft Data Science Blog)](https://medium.com/data-science-at-microsoft/evaluating-llm-systems-metrics-challenges-and-best-practices-664ac25be7e5)
