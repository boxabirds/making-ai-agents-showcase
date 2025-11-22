# Infinite-Scalability Plan — Task Index

Status legend: TODO | IN_PROGRESS | DONE

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | SQLite schema, lifecycle, Pydantic models | TODO | Working store defaults to ephemeral; `--persist-store` retains |
| 2 | Tree-sitter parsing & ingestion pipeline | TODO | Chunking, symbol/edge extraction, hashing |
| 3 | Summaries map/reduce + validation | TODO | Chunk→file→module/package summaries with citations |
| 4 | Retrieval engine (FTS, hybrid) & store API | TODO | Deterministic-first; optional embeddings with re-rank |
| 5 | Report drafting & citation enforcement | TODO | Structured prompts; primary Markdown output |
| 6 | Claim extraction & verification | TODO | Supported/contradicted/uncertain/missing with severity |
| 7 | Coverage assessment, issue planning, gating | TODO | Expected-surface derivation, thresholds, loop control |
| 8 | Orchestrator & CLI (`--persist-store`, lifecycle) | TODO | DSPy wiring, teardown logic, logging |
| 9 | Persisted-store tooling for audits/evals | TODO | Query tools when `--persist-store` is set |
| 10 | BDD end-to-end & regression harness | TODO | Full pipeline scenarios + golden/regression checks |
