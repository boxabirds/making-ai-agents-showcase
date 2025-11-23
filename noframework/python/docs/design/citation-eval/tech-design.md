# Citation Evaluation System: Technical Design

> **Created:** 2025-11-23
> **Parent:** [`docs/design/eval.md`](../eval.md)
> **Status:** Draft

## 1. Overview

### 1.1 Purpose

This document specifies the technical design for evaluating citations in tech_writer generated reports. The system must handle two citation modes:

- **Extractive citations**: Claims quote or closely paraphrase source code
- **Abstractive citations**: Claims summarize or interpret source code

### 1.2 Design Principles

1. **Use the right tool for the job**: Regex/heuristics for structural checks; LLMs for semantic judgment
2. **Fail fast with cheap checks**: Run automated checks before expensive LLM calls
3. **Ground truth via humans**: LLM judges must be calibrated against human annotations
4. **Incremental cost**: Simple queries should cost less than complex ones

### 1.3 Scope

In scope:
- Citation validity (structural)
- Citation precision (semantic)
- Citation coverage
- Faithfulness assessment
- Calibration infrastructure

Out of scope:
- Report generation improvements (separate concern)
- Multi-modal citations (images, diagrams)

---

## 2. Citation Model

### 2.1 Citation Format

Citations in tech_writer follow this format:
```
[file_path:start_line-end_line]
```

Examples:
- `[src/auth.py:10-25]`
- `[lib/core/Axios.js:100-150]`

### 2.2 Citation Components

| Component | Description | Validation |
|-----------|-------------|------------|
| `file_path` | Relative path from repo root | Must exist in cache |
| `start_line` | First line (1-indexed) | Must be positive integer |
| `end_line` | Last line (inclusive) | Must be >= start_line |

### 2.3 Claim-Citation Relationship

A citation appears within a claim. The claim is the textual assertion; the citation is the evidence reference.

```
"The AuthManager class validates credentials [src/auth.py:10-25]."
 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 CLAIM                                        ^^^^^^^^^^^^^^^^^^
                                              CITATION
```

### 2.4 Extractive vs Abstractive Claims

#### 2.4.1 Extractive Claims

The claim directly states what the code contains, using terminology from the code.

**Characteristics:**
- Function/class/variable names appear verbatim
- Describes structure or syntax
- Can be verified by string matching

**Examples:**
- "The `validate_token` function checks expiry" → Look for `def validate_token` and `expiry`
- "The User model has fields `name` and `email`" → Look for `name` and `email` in class

**Verification method:** Regex + heuristics

#### 2.4.2 Abstractive Claims

The claim interprets, summarizes, or infers from the code.

**Characteristics:**
- Uses different terminology than the code
- Describes behavior, purpose, or intent
- Requires understanding code semantics

**Examples:**
- "The authentication system prevents replay attacks" → Code may show timestamp checks, nonce validation
- "This module handles user lifecycle" → Code may have create/update/delete functions

**Verification method:** LLM semantic judgment

---

## 3. Evaluation Pipeline

### 3.1 Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INPUT: Report + Cache                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Citation Extraction                                        │
│                                                                      │
│  Method: Regex                                                       │
│  Input: Report markdown                                              │
│  Output: List of (claim_text, citation, position)                   │
│  Cost: O(n) string scan, ~0                                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Structural Validation                                      │
│                                                                      │
│  Method: Deterministic checks                                        │
│  Checks:                                                             │
│    - File exists in cache                                            │
│    - Line numbers valid                                              │
│    - File readable (not binary)                                      │
│  Output: Valid citations, invalid citations with errors              │
│  Cost: O(citations) cache lookups, ~0                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Claim Classification                                       │
│                                                                      │
│  Method: Heuristics + optional LLM                                  │
│  Purpose: Determine if claim is extractive or abstractive           │
│  Heuristics:                                                         │
│    - Contains backtick code spans → likely extractive               │
│    - Contains "function", "class", "method" + name → extractive     │
│    - Contains "handles", "manages", "provides" → likely abstractive │
│  Output: Claim classification (extractive/abstractive/unknown)       │
│  Cost: O(claims) regex, ~0 (LLM optional for unknown)              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│  STAGE 4a: Extractive Check │   │  STAGE 4b: Abstractive Check    │
│                             │   │                                  │
│  Method: Regex + fuzzy      │   │  Method: LLM-as-judge           │
│  Checks:                    │   │  Input: Claim + cited code       │
│    - Key terms present      │   │  Output: supports/not + reason   │
│    - Names match code       │   │  Cost: See §14 (Cost Model)       │
│    - Structure aligns       │   │                                  │
│  Cost: O(1) per citation    │   │                                  │
└─────────────────────────────┘   └─────────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5: Aggregation                                                │
│                                                                      │
│  Compute:                                                            │
│    - Citation validity rate                                          │
│    - Citation precision (extractive)                                │
│    - Citation precision (abstractive)                               │
│    - Overall precision                                               │
│    - Citation coverage                                               │
│  Output: EvalResult with metrics                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stage Details

#### 3.2.1 Stage 1: Citation Extraction

**Input:** Markdown report text

**Method:** Regex pattern matching

**Pattern:**
```
\[([^:\]]+):(\d+)-(\d+)\]
```

**Output per citation:**
```
{
  "citation": "[src/auth.py:10-25]",
  "file_path": "src/auth.py",
  "start_line": 10,
  "end_line": 25,
  "position": 1234,  # Character offset in report
  "claim_text": "The AuthManager class validates credentials"
}
```

**Claim extraction:** Extract sentence containing citation using sentence boundary detection (period, exclamation, question mark).

#### 3.2.2 Stage 2: Structural Validation

**Checks (all deterministic):**

| Check | Pass Condition | Error |
|-------|---------------|-------|
| File cached | `store.has_file(path)` | "File not in cache" |
| Start line valid | `start_line >= 1` | "Invalid start line" |
| End line valid | `end_line >= start_line` | "End before start" |
| Lines exist | `end_line <= file.line_count` | "Line out of range" |

**Output:** `StructuralValidationResult`
- `valid: bool`
- `error: Optional[str]`
- `cited_content: Optional[str]` (if valid)

#### 3.2.3 Stage 3: Claim Classification

**Purpose:** Route claims to appropriate verification method.

**Classification heuristics (regex-based):**

| Pattern | Classification | Rationale |
|---------|---------------|-----------|
| Contains `` `identifier` `` | Extractive | References specific code element |
| "function X", "class X", "method X" | Extractive | Names specific symbol |
| "defined in", "located at", "found in" | Extractive | Describes location |
| "handles", "manages", "responsible for" | Abstractive | Describes purpose |
| "implements", "provides", "supports" | Abstractive | Describes capability |
| "architecture", "design", "pattern" | Abstractive | High-level concept |

**Decision tree:**
```
Has code span (`...`)? → EXTRACTIVE
Has symbol name pattern? → EXTRACTIVE
Has behavioral verb? → ABSTRACTIVE
Default → UNKNOWN (use LLM or conservative extractive check)
```

**LLM fallback for UNKNOWN:** Optional. Can classify with single LLM call if needed.

#### 3.2.4 Stage 4a: Extractive Verification

**Method:** Regex and fuzzy string matching (no LLM)

**Checks:**

1. **Symbol presence**: Extract identifiers from claim, check if present in cited code
   ```python
   # Claim: "The `validate_token` function checks expiry"
   # Extract: ["validate_token", "expiry"]
   # Check: Both terms appear in cited code
   ```

2. **Name matching**: Compare claimed names against actual code symbols
   ```python
   # Claim: "The User class has a save method"
   # Parse cited code for class/function definitions
   # Check: "User" is a class, "save" is a method
   ```

3. **Structural alignment**: For claims about structure, verify structure exists
   ```python
   # Claim: "The module exports three functions"
   # Count function definitions in cited code
   # Check: Count matches claim
   ```

**Scoring:**
- All key terms found → `SUPPORTS`
- Some key terms found → `PARTIAL`
- No key terms found → `NOT_SUPPORTS`

**Confidence:** Based on term coverage percentage

#### 3.2.5 Stage 4b: Abstractive Verification

**Method:** LLM-as-judge (required for semantic understanding)

**When used:**
- Claim classified as ABSTRACTIVE
- Claim classified as UNKNOWN and extractive check inconclusive
- High-stakes evaluation requiring semantic judgment

**Prompt structure:**
```
System: You evaluate whether code supports a documentation claim.

The claim may paraphrase or summarize the code rather than quote it directly.
Judge whether the code provides sufficient evidence for the claim.

Respond: {"supports": true/false, "reasoning": "...", "confidence": "high/medium/low"}

User:
Claim: {claim}
Code:
```
{cited_code}
```
```

**Cost control:**
- Only run for abstractive/unknown claims
- Batch multiple claims per LLM call where possible
- Use smaller model (gpt-4o-mini) for initial pass, escalate uncertain to gpt-4o

#### 3.2.6 Stage 5: Aggregation

**Metrics computed:**

| Metric | Formula | Description |
|--------|---------|-------------|
| `validity_rate` | `valid_citations / total_citations` | Structural validity |
| `extractive_precision` | `extractive_supports / extractive_total` | Extractive claim accuracy |
| `abstractive_precision` | `abstractive_supports / abstractive_total` | Abstractive claim accuracy |
| `overall_precision` | `all_supports / all_checked` | Combined precision |
| `coverage` | `claims_with_citations / total_claims` | Citation presence |

---

## 4. Extractive Verification Design

### 4.1 Term Extraction

**From claims:**
1. Extract code spans (text within backticks)
2. Extract capitalized identifiers (likely class names)
3. Extract snake_case/camelCase identifiers
4. Filter common words ("function", "class", "method", "the")

**From code:**
1. Parse with tree-sitter for symbol names
2. Extract string literals
3. Extract comments for documentation claims

### 4.2 Matching Rules

| Claim Pattern | Code Must Contain | Match Type |
|---------------|-------------------|------------|
| "`foo` function" | `def foo` or `function foo` | Exact |
| "Foo class" | `class Foo` | Exact |
| "handles X" | Symbol or comment mentioning X | Fuzzy |
| "has field Y" | `self.Y` or `this.Y` or property Y | Exact |

### 4.3 Fuzzy Matching

For near-matches (typos, case differences):
- Levenshtein distance <= 2 for short identifiers
- Case-insensitive matching for prose
- Stemming for verb forms ("validates" ↔ "validation")

### 4.4 Scoring Algorithm

```
score = matched_terms / total_claim_terms

if score >= 0.8:
    result = SUPPORTS (high confidence)
elif score >= 0.5:
    result = PARTIAL (medium confidence)
else:
    result = NOT_SUPPORTS (high confidence)
```

---

## 5. Abstractive Verification Design

### 5.1 When LLM Required

LLM judgment is required when:
1. Claim uses different terminology than code
2. Claim describes intent, purpose, or behavior
3. Claim makes inferences from code structure
4. Extractive check returns PARTIAL with low confidence

### 5.2 Judge Prompt Design

**Principles:**
- Chain-of-thought: Ask for reasoning before verdict
- Binary output: supports/not (avoid scales for this task)
- Confidence calibration: Ask for uncertainty indication

**Prompt template:**
```
You are evaluating whether source code supports a documentation claim.

The claim may summarize, paraphrase, or interpret the code.
It does NOT need to quote the code verbatim.

A claim is SUPPORTED if:
- The code provides evidence for what the claim states
- A reasonable developer would agree the claim follows from the code
- The claim doesn't overstate or misrepresent what the code does

A claim is NOT SUPPORTED if:
- The code doesn't contain evidence for the claim
- The claim describes behavior not evident in the code
- The claim contradicts what the code does

Claim: "{claim}"

Code from {citation}:
```
{code}
```

Think step by step:
1. What does the claim assert?
2. What does the code show?
3. Does the code support the assertion?

Then respond in JSON:
{"supports": true/false, "reasoning": "your analysis", "confidence": "high/medium/low"}
```

### 5.3 Batching Strategy

To reduce LLM calls:
1. Group citations from same file
2. Send up to 5 claim-code pairs per request
3. Parallelize across files

**Batch prompt:**
```
Evaluate each claim against its cited code.

[Claim 1]: "..."
[Code 1]: ```...```

[Claim 2]: "..."
[Code 2]: ```...```

Respond with JSON array:
[{"claim_id": 1, "supports": ..., "reasoning": ..., "confidence": ...}, ...]
```

### 5.4 Model Selection

| Scenario | Model | Rationale |
|----------|-------|-----------|
| Initial pass | gpt-4o-mini | Cost-effective, good enough for clear cases |
| Low confidence | gpt-4o | Better judgment for ambiguous cases |
| Calibration | gpt-4o | Need best quality for ground truth comparison |

---

## 6. Coverage Analysis

### 6.1 Claim Detection

**What counts as a claim:**
- Declarative sentence about the code
- Statement that could be true or false
- Assertion that should have evidence

**What doesn't count:**
- Section headers
- Meta-statements ("This section covers...")
- Questions
- Code blocks
- Navigation text ("See also...")

### 6.2 Detection Method

**Regex patterns for non-claims:**
```python
NON_CLAIM_PATTERNS = [
    r'^#+\s',                    # Headers
    r'^```',                     # Code blocks
    r'^[-*]\s*$',               # Empty list items
    r'^this section',           # Meta-statements
    r'^in this section',
    r'^see also',
    r'^note:',
    r'\?$',                     # Questions
]
```

**Sentence extraction:**
```python
# Split on sentence boundaries
# Filter short sentences (< 4 words)
# Filter non-claim patterns
# Result: list of claims
```

### 6.3 Coverage Calculation

```
coverage = claims_with_citation / total_claims

where:
  claims_with_citation = count(claims containing [path:line-line])
  total_claims = count(all extracted claims)
```

---

## 7. Human-in-the-Loop Integration

### 7.1 Purpose

HIL serves two functions:
1. **Ground truth**: Human annotations are the standard for correctness
2. **Calibration**: Measure how well LLM judge matches human judgment

### 7.2 Annotation Schema

**Citation annotation:**
```
{
  "claim": "The AuthManager validates credentials",
  "citation": "[src/auth.py:10-25]",
  "cited_code": "class AuthManager:\n    def validate...",

  "annotations": {
    "supports_claim": 0-3,     // 0=no, 1=weak, 2=partial, 3=full
    "line_range": "correct" | "too_narrow" | "too_broad",
    "notes": "optional text"
  }
}
```

### 7.3 Calibration Metrics

**LLM-Human agreement:**
```
agreement_rate = matching_verdicts / total_annotations

where matching = (LLM says supports AND human >= 2) OR (LLM says not AND human <= 1)
```

**Correlation:**
- Spearman correlation between LLM confidence and human score
- Target: ρ > 0.6 for judge to be considered calibrated

### 7.4 Disagreement Analysis

When LLM and human disagree:
1. Log the case for review
2. Categorize disagreement type:
   - LLM false positive (said supports, human disagrees)
   - LLM false negative (said not supports, human disagrees)
3. Use disagreements to refine judge prompt

---

## 8. Data Structures

### 8.1 Citation

```python
@dataclass
class Citation:
    file_path: str
    start_line: int
    end_line: int

    def __str__(self) -> str:
        return f"[{self.file_path}:{self.start_line}-{self.end_line}]"
```

### 8.2 ExtractedCitation

```python
@dataclass
class ExtractedCitation:
    citation: Citation
    claim_text: str
    position: int  # Character offset in report
    context: str   # Surrounding paragraph
```

### 8.3 ValidationResult

```python
@dataclass
class ValidationResult:
    citation: Citation
    valid: bool
    error: Optional[str]
    cited_content: Optional[str]
```

### 8.4 ClassificationResult

```python
@dataclass
class ClassificationResult:
    citation: ExtractedCitation
    classification: Literal["extractive", "abstractive", "unknown"]
    confidence: float
    matched_patterns: list[str]
```

### 8.5 VerificationResult

```python
@dataclass
class VerificationResult:
    citation: ExtractedCitation
    supports: bool
    method: Literal["extractive", "abstractive"]
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    matched_terms: list[str]  # For extractive
```

### 8.6 EvalResult

```python
@dataclass
class EvalResult:
    # Structural
    total_citations: int
    valid_citations: int
    validity_rate: float

    # Precision
    extractive_checked: int
    extractive_supports: int
    extractive_precision: float

    abstractive_checked: int
    abstractive_supports: int
    abstractive_precision: float

    overall_precision: float

    # Coverage
    total_claims: int
    cited_claims: int
    coverage: float

    # Cost
    llm_calls: int
    llm_tokens: int

    # Details
    results: list[VerificationResult]

    # Failed citations for correction workflow (see §15.2)
    failed_citations: list[FailedCitation]

    @property
    def needs_correction(self) -> bool:
        """True if any citations failed verification."""
        return len(self.failed_citations) > 0

    @property
    def is_perfect(self) -> bool:
        """True if all citations valid and supporting."""
        return (
            self.validity_rate == 1.0
            and self.overall_precision == 1.0
            and len(self.failed_citations) == 0
        )
```

---

## 9. Configuration

### 9.1 Detection Thresholds

> **Note:** These are detection thresholds, not acceptance thresholds. The target is 100% citation accuracy (see §15). These values determine what triggers the correction workflow.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `extractive_term_threshold` | 0.5 | Min term match for extractive "supports" |
| `confidence_threshold` | 0.7 | Below this, escalate to better model |

**Removed:** `validity_threshold`, `precision_threshold`, `coverage_threshold`. Any failure triggers correction—there is no "acceptable failure rate."

### 9.2 LLM Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `judge_model` | "gpt-4o-mini" | Model for abstractive verification |
| `escalation_model` | "gpt-4o" | Model for low-confidence escalation |
| `max_batch_size` | 5 | Max claims per LLM call |

### 9.3 Classification Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_llm_classification` | false | Use LLM for unknown claims |
| `default_unknown_handling` | "extractive" | How to handle unknown claims |

---

## 10. Error Handling

### 10.1 Structural Errors

| Error | Handling |
|-------|----------|
| File not in cache | Mark invalid, include in report |
| Line out of range | Mark invalid, include in report |
| Binary file | Mark invalid, skip verification |

### 10.2 LLM Errors

| Error | Handling |
|-------|----------|
| Rate limit | Exponential backoff, retry 3x |
| Timeout | Retry once, then mark as "unverified" |
| Parse error | Log response, use conservative default |
| API error | Retry 3x, then fail pipeline |

### 10.3 Graceful Degradation

If LLM unavailable:
1. Run structural validation (always possible)
2. Run extractive checks (no LLM needed)
3. Mark abstractive claims as "unverified"
4. Report partial results with warning

---

## 11. Testing Strategy

### 11.1 Unit Tests

| Component | Test Focus |
|-----------|------------|
| Citation extraction | Regex edge cases, nested brackets |
| Structural validation | All error conditions |
| Claim classification | Pattern matching accuracy |
| Extractive verification | Term extraction, matching |
| Aggregation | Math correctness |

### 11.2 Integration Tests

| Scenario | Validation |
|----------|------------|
| Valid report | All stages complete, metrics computed |
| Invalid citations | Errors captured, pipeline continues |
| Mixed claims | Both extractive and abstractive handled |
| LLM failure | Graceful degradation works |

### 11.3 Calibration Tests

| Test | Criteria |
|------|----------|
| LLM-human agreement | Agreement rate > 70% |
| Precision | Extractive precision > 90%, abstractive > 80% |
| Recall | Not missing obvious support/non-support |

---

## 12. Implementation Phases

### 12.1 Phase 1: Structural Foundation
- Citation extraction (regex)
- Structural validation
- Coverage calculation
- Basic aggregation

### 12.2 Phase 2: Extractive Verification
- Claim classification heuristics
- Term extraction
- Matching algorithm
- Extractive precision calculation

### 12.3 Phase 3: Abstractive Verification
- LLM judge implementation
- Batching strategy
- Confidence handling
- Model escalation

### 12.4 Phase 4: Integration
- Pipeline orchestration
- CLI integration
- Result formatting
- Error handling

### 12.5 Phase 5: Calibration
- HIL setup (Argilla)
- Annotation collection
- Agreement metrics
- Prompt refinement

---

## 13. Appendix

### 13.1 Regex Patterns Reference

```python
# Citation extraction
CITATION_PATTERN = r'\[([^:\]]+):(\d+)-(\d+)\]'

# Code span extraction
CODE_SPAN_PATTERN = r'`([^`]+)`'

# Identifier extraction
IDENTIFIER_PATTERN = r'\b([A-Z][a-zA-Z0-9]*|[a-z][a-zA-Z0-9_]*)\b'

# Extractive claim indicators
EXTRACTIVE_INDICATORS = [
    r'`[^`]+`',                           # Code spans
    r'\b(function|class|method|variable)\s+\w+',
    r'\b(defined|located|found)\s+(in|at)',
    r'\bnamed?\s+`?\w+`?',
]

# Abstractive claim indicators
ABSTRACTIVE_INDICATORS = [
    r'\b(handles?|manages?|responsible)\b',
    r'\b(implements?|provides?|supports?)\b',
    r'\b(architecture|design|pattern)\b',
    r'\b(ensures?|guarantees?|prevents?)\b',
]

# Non-claim patterns
NON_CLAIM_PATTERNS = [
    r'^#+\s',
    r'^```',
    r'^\s*[-*]\s*$',
    r'^(this|in this)\s+section',
    r'^see\s+(also|more)',
    r'^note:',
    r'\?\s*$',
]
```

### 13.2 Example Evaluations

**Example 1: Extractive (should pass)**
```
Claim: "The `validate_token` function checks the expiry timestamp"
Code:
  def validate_token(token):
      if token.expiry < datetime.now():
          raise TokenExpiredError()
      return True

Result: SUPPORTS
Method: Extractive
Reasoning: "validate_token" found as function, "expiry" found in code
```

**Example 2: Abstractive (should pass)**
```
Claim: "The authentication system prevents replay attacks"
Code:
  def authenticate(request):
      nonce = request.headers.get('X-Nonce')
      if nonce in self.used_nonces:
          raise SecurityError('Nonce reused')
      self.used_nonces.add(nonce)
      ...

Result: SUPPORTS
Method: Abstractive (LLM)
Reasoning: Nonce tracking is a standard replay attack prevention mechanism
```

**Example 3: Abstractive (should fail)**
```
Claim: "The API uses OAuth 2.0 for authentication"
Code:
  def authenticate(username, password):
      user = db.get_user(username)
      if user and check_password(password, user.hash):
          return create_session(user)
      return None

Result: NOT_SUPPORTS
Method: Abstractive (LLM)
Reasoning: Code shows username/password auth, no OAuth indicators
```

---

## 14. Cost Model

### 14.1 Pricing Reference

**OpenAI API Pricing (as of November 2024):**

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o-mini | $0.15 / 1M tokens | $0.60 / 1M tokens |
| gpt-4o | $5.00 / 1M tokens | $15.00 / 1M tokens |

Source: [OpenAI Pricing](https://openai.com/api/pricing/)

### 14.2 Per-Citation Cost Estimate

**Assumptions for single citation verification:**
- System prompt: ~300 tokens
- Claim text: ~50 tokens
- Cited code: ~400 tokens (varies widely)
- Total input: ~750 tokens
- Output (JSON + reasoning): ~200 tokens

**gpt-4o-mini cost per citation:**
```
Input:  750 tokens × $0.00000015 = $0.00011
Output: 200 tokens × $0.00000060 = $0.00012
Total:  $0.00023 per citation (~$0.0002)
```

**gpt-4o cost per citation:**
```
Input:  750 tokens × $0.000005 = $0.00375
Output: 200 tokens × $0.000015 = $0.00300
Total:  $0.00675 per citation (~$0.007)
```

### 14.3 Batched Cost Estimate

With batching (5 claims per request):
- System prompt: ~300 tokens (shared)
- 5 × (claim + code): ~2250 tokens
- Total input: ~2550 tokens
- Output (5 JSON objects): ~600 tokens

**gpt-4o-mini batched (per citation):**
```
Input:  2550 tokens × $0.00000015 = $0.00038
Output: 600 tokens × $0.00000060 = $0.00036
Total for 5: $0.00074
Per citation: $0.00015 (~$0.0001)
```

### 14.4 Report-Level Cost Estimate

**Typical report: 30 citations, 50% abstractive**
- Structural validation: $0 (no LLM)
- Extractive (15 citations): $0 (no LLM)
- Abstractive (15 citations, batched): 3 batches × $0.00074 = $0.0022

**Total per report: ~$0.002** (gpt-4o-mini, batched)

**With escalation (20% to gpt-4o):**
- 12 citations via gpt-4o-mini: $0.0015
- 3 citations via gpt-4o: 3 × $0.007 = $0.021
- Total: ~$0.023 per report

### 14.5 Cost Summary Table

| Scenario | Model | Per Citation | Per Report (30 cit) |
|----------|-------|--------------|---------------------|
| Single calls | gpt-4o-mini | $0.0002 | $0.003 |
| Batched (5) | gpt-4o-mini | $0.0001 | $0.002 |
| Single calls | gpt-4o | $0.007 | $0.10 |
| Mixed (80/20) | mini + 4o | ~$0.002 | $0.02 |

### 14.6 Cost Control Strategies

1. **Batch aggressively**: 5x cost reduction
2. **Classify before calling**: Skip LLM for extractive claims
3. **Use gpt-4o-mini first**: 30x cheaper than gpt-4o
4. **Escalate selectively**: Only low-confidence to gpt-4o
5. **Cache results**: Don't re-evaluate unchanged citations

---

## 15. Correction Workflow

### 15.1 Design Philosophy

**Target: 100% citation accuracy.** LLMs are probabilistic and produce errors. Evaluation is not a pass/fail gate—it drives an iterative correction loop until all citations are valid.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CORRECTION LOOP                                  │
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │ Generate │───►│ Evaluate │───►│ Extract  │───►│ Correct  │──┐  │
│   │ Report   │    │ Citations│    │ Failures │    │ Citations│  │  │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘  │  │
│        ▲                                                         │  │
│        │                                                         │  │
│        └─────────────────────────────────────────────────────────┘  │
│                          (until 0 failures)                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.2 Failed Citation Output

The evaluation produces a structured list of failed citations with enough context for correction:

```python
@dataclass
class FailedCitation:
    """A citation that failed verification, with correction context."""

    # Location
    section: str           # Section containing the citation
    paragraph_index: int   # Paragraph within section
    claim_text: str        # The claim making the citation

    # Citation details
    citation: Citation     # The parsed citation object
    cited_code: str        # The code that was cited

    # Failure details
    failure_type: Literal[
        "invalid_file",      # File doesn't exist in cache
        "invalid_range",     # Line range out of bounds
        "not_supporting",    # Code doesn't support claim (LLM verdict)
        "low_confidence",    # LLM uncertain
    ]
    failure_reason: str    # Human-readable explanation

    # For correction
    suggested_action: Literal[
        "fix_reference",     # Find correct file/lines
        "rewrite_claim",     # Claim doesn't match code
        "remove_citation",   # Citation unnecessary
        "expand_range",      # Need more context
    ]
    llm_reasoning: str | None  # LLM's explanation (if applicable)
```

### 15.3 Correction Interface

The correction process receives failed citations and produces fixes:

```python
@dataclass
class CitationCorrection:
    """A proposed fix for a failed citation."""

    failed: FailedCitation

    # Correction
    action_taken: Literal[
        "replaced_reference",  # New file:line reference
        "rewrote_claim",       # Modified claim text
        "removed_citation",    # Deleted citation
        "expanded_range",      # Widened line range
        "no_change",           # Manual review needed
    ]

    # New values (if applicable)
    new_citation: Citation | None
    new_claim_text: str | None

    # Explanation
    correction_reasoning: str

class CorrectionResult:
    """Result of correction pass."""

    corrections: list[CitationCorrection]
    remaining_failures: int  # Should be 0 for success
    iterations: int          # How many correction passes
```

### 15.4 Correction Strategies

#### 15.4.1 Invalid Reference (file/range)

```
Strategy: Search cache for correct location

Input:
  - Claim text
  - Invalid citation
  - File cache

Process:
  1. Extract key terms from claim
  2. Search cache for files containing terms
  3. Find line ranges matching context
  4. Propose new reference

Output:
  - New citation with correct file:lines
  - Or flag for manual review if ambiguous
```

#### 15.4.2 Non-Supporting Code

```
Strategy: Either find supporting code or rewrite claim

Input:
  - Claim text
  - Current citation
  - LLM reasoning for failure

Process:
  1. Parse LLM explanation for mismatch
  2. Option A: Search for code that DOES support claim
  3. Option B: Rewrite claim to match cited code
  4. Option C: Remove citation if claim is inferential

Output:
  - New citation, or
  - Rewritten claim, or
  - Claim without citation
```

#### 15.4.3 Low Confidence

```
Strategy: Gather more context

Input:
  - Claim + citation
  - LLM confidence score

Process:
  1. Expand line range for more context
  2. Re-evaluate with expanded range
  3. If still uncertain, escalate to gpt-4o
  4. If still uncertain, flag for human review

Output:
  - Verdict with higher confidence, or
  - Human review queue item
```

### 15.5 Integration with Reporting Pipeline

The correction loop integrates with tech_writer's agentic workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTEGRATED WORKFLOW                               │
│                                                                      │
│  tech_writer generate                                                │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────┐                                                         │
│  │ Report  │◄─────────────────────────────────────────┐             │
│  │ Draft   │                                          │             │
│  └────┬────┘                                          │             │
│       │                                               │             │
│       ▼                                               │             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│  │Citation │───►│ Failed  │───►│Correction│───►│ Apply   │          │
│  │  Eval   │    │Citations│    │  Pass    │    │ Fixes   │──────────┘
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘           │
│       │                                                              │
│       │ (0 failures)                                                 │
│       ▼                                                              │
│  ┌─────────┐                                                         │
│  │ Final   │                                                         │
│  │ Report  │                                                         │
│  └─────────┘                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.6 Iteration Limits

To prevent infinite loops:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_correction_iterations` | 3 | Max correction passes |
| `max_failures_for_auto` | 10 | Above this, require human review |

**Exit conditions:**
1. **Success**: 0 failed citations
2. **Iteration limit**: Max iterations reached, output remaining failures
3. **Manual required**: Failures exceed auto-correction threshold

### 15.7 Output Modes

```
--eval                    # Evaluate only, report failures
--eval --correct          # Evaluate and auto-correct
--eval --correct --strict # Fail if any citations remain unfixed
```

### 15.8 Correction Cost

Additional cost per correction iteration:
- Search/index operations: O(1) local
- LLM re-evaluation: Same as initial (~$0.0002/citation)
- Claim rewriting (if needed): ~$0.001/claim

**Typical scenario (30 citations, 10% failure rate):**
- Initial eval: $0.002
- Correction pass 1: 3 failures × $0.001 = $0.003
- Re-eval: 3 × $0.0002 = $0.0006
- Total: ~$0.006 per report with correction
