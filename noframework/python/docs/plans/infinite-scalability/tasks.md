# Infinite-Scalability Plan — Task Index

Status legend: TODO | IN_PROGRESS | DONE

Cross-cutting rule: the agent must honor arbitrary user prompts (from `--prompt`) with no hard-coded report templates or prompt-specific assumptions; every task should preserve that generality.

| # | Task | Status | Notes | Depends on |
|---|------|--------|-------|------------|
| 1 | SQLite schema, lifecycle, Pydantic models | DONE | Working store defaults to ephemeral; `--persist-store` retains | - |
| 2 | Tree-sitter parsing & ingestion pipeline | DONE | Tree-sitter-based chunking for supported langs; unsupported skipped | 1 |
| 3 | Summaries map/reduce + validation | DONE | DSPy map/reduce with enforced citations and validation | 2 |
| 4 | Retrieval engine (FTS, hybrid) & store API | DONE | Hybrid re-rank combining FTS, symbols/edges, embeddings; web harness pending | 1,2 |
| 5 | Report drafting & citation enforcement | DONE | Draft citations enforced/validated with repair; web harness required | 3,4 |
| 6 | Claim extraction & verification | TODO | Citation-aware check; richer grading pending; web harness required | 5 |
| 7 | Coverage assessment, issue planning, gating | TODO | Coverage uses symbols; iteration/gating refinement pending; web harness required | 6 |
| 8 | Orchestrator & CLI (`--persist-store`, lifecycle) | TODO | Pipeline wired; iterative loop pending; web harness required | 3,4,5,6,7 |
| 9 | Persisted-store tooling for audits/evals | TODO | Audit CLI exists; eval harness/golden exports pending; web harness required | 8 |
| 10 | BDD end-to-end & regression harness | TODO | Pytest E2E with citation parsing; full BDD/golden/regression pending | 8,9 |
| 11 | Eval harness & citation verification | TODO | Evaluation runner + metrics; citation veracity checks pending; web harness required | 5,6,9 |
