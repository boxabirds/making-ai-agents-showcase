# Infinite-Scalability Plan — Task Index

Status legend: TODO | IN_PROGRESS | DONE

Cross-cutting rule: the agent must honor arbitrary user prompts (from `--prompt`) with no hard-coded report templates or prompt-specific assumptions; every task should preserve that generality.

Tracks are grouped for orthogonality; numbering is stable but tasks are not strictly sequential. Use the Depends column to plan execution.

| # | Task | Status | Notes | Depends on |
|---|------|--------|-------|------------|
| 1 | SQLite schema, lifecycle, Pydantic models | DONE | Working store defaults to ephemeral; `--persist-store` retains | - |
| 2 | Tree-sitter parsing & ingestion pipeline | DONE | Tree-sitter-based chunking for supported langs; unsupported skipped | 1 |
| 3 | Summaries map/reduce + validation | DONE | DSPy map/reduce with enforced citations and validation | 2 |
| 4 | Retrieval engine (FTS, hybrid) & store API | DONE | Hybrid re-rank combining FTS, symbols/edges, embeddings; web harness pending | 1,2 |
| 5 | Report drafting & citation enforcement | DONE | Draft citations enforced/validated with repair; web harness required | 3,4 |
| 6 | Claim extraction & verification | DONE | Citation parsing/validation, grading with severity mapping; retrieval repair; tests added | 5 |
| 7 | Coverage assessment, issue planning, gating | DONE | Coverage from symbols, issue planning, gate helper; tests added | 6 |
| 8 | Orchestrator & CLI (`--persist-store`, lifecycle) | DONE | CLI supports gating overrides, persist flag, iterations; orchestration wired | 3,4,5,6,7 |
| 9 | Persisted-store tooling for audits/evals | DONE | Audit CLI extended (summaries, neighbors, export); ready for persisted stores | 8 |
| 10 | BDD end-to-end & regression harness | DONE | Stubbed deterministic BDD/regression test added; E2E coverage expanded | 8,9 |
| 11 | Eval harness & citation verification | DONE | Eval metrics include citation veracity; runner emits metrics; tests updated | 5,6,9 |
| 12 | Ingestion/graph completeness | TODO | Fallback chunking or explicit skips for unsupported langs; real symbol/edge extraction; keep skipped files in coverage | 2,18 |
| 13 | Multi-level summaries with validation | TODO | Add chunk/package summaries, real module/package ids, propagate citations, validate before insert | 3,12 |
| 14 | Retrieval fidelity | TODO | Add FTS5 on summaries, integrate symbols/edges in scoring, replace hash embeddings with optional real vectors re-ranked lex/graph | 4,12,18 |
| 15 | Drafting & citation repair | TODO | Repair missing citations via retrieved chunks; ensure drafts only use evidence citations while preserving prompt sections | 5,14 |
| 16 | Claim loop & revision | TODO | Structured claim grading tied to cited chunks; compute citation_score/support_rate; add ReviseReport using issues until gates pass | 6,14,15 |
| 17 | Coverage modeling | TODO | Expected surface from symbols + endpoints/routes/config/build; include skipped/unparsed files; remove string-contains coverage heuristic | 7,12,16 |
| 18 | Schema/index hardening | TODO | Index symbols/edges/summaries/claims, FTS on summaries, add FKs for summaries targets and embeddings | 1 |
| 19 | Evaluation & tests | TODO | Eval runner reruns retrieval/claim checks; add regression/property/golden tests for iteration, citation enforcement, retrieval rerank, gating | 10,11,16,17 |
