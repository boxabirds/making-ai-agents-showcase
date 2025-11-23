# Feature 2: V1-Compatible Metadata Output

## Problem Statement

tech_writer v2 only outputs the markdown report. Users migrating from v1 lose:
- Machine-readable metadata (model, repo, timestamp)
- Ability to track runs programmatically
- Evaluation output capture
- Integration with CI/CD pipelines that parse JSON

V1 generates a sidecar `.metadata.json` file with run metadata. V2 needs feature parity.

## User Stories

### US-2.1: Run Metadata
As a developer, I want metadata about each run (model, timestamp, repo) so that I can track which configuration produced which output.

### US-2.2: CI/CD Integration
As a CI/CD pipeline operator, I want JSON output so that I can parse results programmatically and integrate with reporting tools.

### US-2.3: Evaluation Capture
As a quality engineer, I want evaluation results captured in metadata so that I can track documentation quality over time.

## Proposed Solution

Add `--metadata` flag that generates a sidecar JSON file alongside the output:

```bash
python -m tech_writer --prompt p.txt --repo . --output report.md --metadata
# Creates: report.md and report.metadata.json
```

## Success Criteria

- [ ] `--metadata` flag generates `<output>.metadata.json` alongside output file
- [ ] Metadata includes: model, repo_path, timestamp, prompt_file
- [ ] Metadata includes citation stats when `--verify-citations` is used
- [ ] Metadata structure is extensible for future fields (e.g., cost)
- [ ] `--metadata` requires `--output` (no sidecar for stdout)

## Out of Scope

- Streaming metadata during execution
- Metadata database/history tracking
- Cost tracking (see Feature 1: OpenRouter Integration)

## Dependencies

- None (standalone feature)
- Feature 1 will extend metadata with cost fields

## Risks

| Risk | Mitigation |
|------|------------|
| Schema changes break consumers | Version field in metadata, document schema |
| Large metadata files | Keep metadata minimal, reference output file |
