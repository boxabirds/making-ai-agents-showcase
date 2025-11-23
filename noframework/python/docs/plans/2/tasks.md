# Feature 2: V1-Compatible Metadata Output - Task Plan

## Overview

Implementation tasks for metadata JSON output.

## Task Summary

| ID | Task | Status | Dependencies |
|----|------|--------|--------------|
| 2-1 | Create metadata.py with dataclasses | done | - |
| 2-2 | Implement create_metadata function | done | 2-1 |
| 2-3 | Add --metadata CLI argument | done | - |
| 2-4 | Integrate metadata generation in CLI | done | 2-2, 2-3 |
| 2-5 | Add unit tests | done | 2-2 |
| 2-6 | Add BDD feature tests | done | 2-4 |

## Task Details

### 2-1: Create metadata.py with dataclasses

**Requirements:**
- Create `tech_writer/metadata.py`
- Define `METADATA_VERSION = "1.0"` constant
- Define `InvalidCitation` dataclass with: `path`, `start_line`, `end_line`, `error`
- Define `CitationStats` dataclass with: `total`, `valid`, `invalid`, `invalid_citations`
- Define `RunMetadata` dataclass with: `version`, `model`, `repo_path`, `prompt_file`, `timestamp`, `output_file`, `citations`
- Add `to_dict()` method that excludes None values

**Acceptance Criteria:**
- All dataclasses importable from `tech_writer.metadata`
- `to_dict()` excludes fields with None values

---

### 2-2: Implement create_metadata function

**Requirements:**
- Implement `create_metadata(output_file, model, repo_path, prompt_file, citations=None) -> Path`
- Generate ISO 8601 UTC timestamp
- Create metadata file at `<output_stem>.metadata.json`
- Write JSON with indent=2 for readability
- Return path to created metadata file

**Acceptance Criteria:**
- Metadata file created in same directory as output
- JSON is valid and properly formatted
- Timestamp is UTC ISO 8601

---

### 2-3: Add --metadata CLI argument

**Requirements:**
- Add `--metadata` flag to argument parser
- Add validation: `--metadata` requires `--output`
- Help text explains sidecar file behavior

**Acceptance Criteria:**
- `--help` shows `--metadata` with description
- Error raised if `--metadata` used without `--output`

---

### 2-4: Integrate metadata generation in CLI

**Requirements:**
- After report output, check if `--metadata` flag set
- Build `CitationStats` from citation verification results if `--verify-citations` used
- Call `create_metadata()` with appropriate arguments
- Print metadata file path to stderr

**Acceptance Criteria:**
- Metadata file created when `--metadata` flag used
- Citation stats included when `--verify-citations` also used
- Path printed to stderr

---

### 2-5: Add unit tests

**Requirements:**
- Test `RunMetadata.to_dict()` excludes None values
- Test `create_metadata()` creates file at correct path
- Test metadata contains all required fields
- Test timestamp is valid ISO 8601
- Test citation stats included when provided

**Acceptance Criteria:**
- All tests pass
- No file system side effects (use tmp directories)

---

### 2-6: Add BDD feature tests

**Requirements:**
- Create `tests/features/metadata.feature`
- Scenario: metadata file created with --metadata flag
- Scenario: metadata includes citations with --verify-citations
- Scenario: --metadata requires --output
- Implement step definitions

**Acceptance Criteria:**
- All scenarios pass
- Feature file follows Gherkin syntax
