# Implementation Tasks: Citation Evaluation System

> **Design Document:** [`docs/design/citation-eval/tech-design.md`](../../design/citation-eval/tech-design.md)
> **Created:** 2025-11-23

## Status

| # | Task | Status | Deps | Phase | Design Ref |
|---|------|--------|------|-------|------------|
| 1 | Citation extraction | ⬚ todo | - | 1 | §3.2.1, §4.1 |
| 2 | Structural validation | ⬚ todo | 1 | 1 | §3.2.2 |
| 3 | Coverage calculation | ⬚ todo | 1 | 1 | §6 |
| 4 | Claim classification | ⬚ todo | 1 | 2 | §3.2.3, §4 |
| 5 | Extractive verification | ⬚ todo | 4 | 2 | §4, §3.2.4 |
| 6 | Abstractive verification | ⬚ todo | 2 | 3 | §5, §3.2.5 |
| 7 | LLM batching | ⬚ todo | 6 | 3 | §5.3 |
| 8 | Pipeline orchestration | ⬚ todo | 2,5,6 | 4 | §3.1 |
| 9 | Aggregation & metrics | ⬚ todo | 8 | 4 | §3.2.6, §8.6 |
| 10 | CLI integration | ⬚ todo | 9 | 4 | - |
| 11 | Argilla dataset setup | ⬚ todo | - | 5 | §7.2 |
| 12 | Calibration workflow | ⬚ todo | 9,11 | 5 | §7.3, §7.4 |
| 13 | Failed citation output | ⬚ todo | 8,9 | 6 | §15.2, §8.6 |
| 14 | Correction workflow | ⬚ todo | 13 | 6 | §15 |

## Phases

### Phase 1: Structural Foundation (Tasks 1-3)
Regex-based extraction and validation. No LLM cost.
**Ref:** tech-design.md §12.1

### Phase 2: Extractive Verification (Tasks 4-5)
Heuristic classification and term matching. No LLM cost.
**Ref:** tech-design.md §12.2

### Phase 3: Abstractive Verification (Tasks 6-7)
LLM-as-judge for semantic claims. Batched for cost control.
**Ref:** tech-design.md §12.3

### Phase 4: Integration (Tasks 8-10)
Pipeline assembly and CLI.
**Ref:** tech-design.md §12.4

### Phase 5: Calibration (Tasks 11-12)
Human-in-the-loop validation and LLM judge tuning.
**Ref:** tech-design.md §12.5

### Phase 6: Correction Workflow (Tasks 13-14)
Iterative correction loop targeting 100% citation accuracy.
**Ref:** tech-design.md §15

## Dependency Graph

```
Phase 1          Phase 2         Phase 3         Phase 4         Phase 5         Phase 6
────────         ────────        ────────        ────────        ────────        ────────
   1 ─────────────→ 4 ──→ 5 ─────────────────────→ 8 ────→ 9 ───→ 12
   │                              │                │       │       ↑
   ├──→ 2 ────────────────────────┼───→ 6 ──→ 7 ──┘       │       │
   │                              │                        │       │
   └──→ 3 ────────────────────────┴────────────────────────┘       │
                                                           10      11
                                                            │
                                                            └───────────→ 13 ──→ 14
```

**Note:** Phase 6 (correction workflow) depends on the evaluation pipeline (Tasks 8-9) being complete.
Target: 100% citation accuracy through iterative correction (see tech-design.md §15.1).

## Execution Strategy

**Parallel tracks:**
- Track A (no LLM): 1 → 2 → 3 (can ship as MVP)
- Track B (heuristics): 1 → 4 → 5
- Track C (LLM): 2 → 6 → 7
- Track D (integration): 8 → 9 → 10
- Track E (calibration): 11 → 12
- Track F (correction): 13 → 14 (requires Track D)

**Milestones:**
1. **Structural eval:** Tasks 1-3 complete → can report validity & coverage
2. **Full automated:** Tasks 1-9 complete → can report precision (extractive + abstractive)
3. **100% accuracy:** Tasks 1-14 complete → iterative correction until perfect
4. **Production ready:** Tasks 1-14 + calibration → human-validated judges

## Estimated Effort

| Phase | Tasks | Effort | LLM Cost |
|-------|-------|--------|----------|
| 1 | 1-3 | 1 day | $0 |
| 2 | 4-5 | 1 day | $0 |
| 3 | 6-7 | 1-2 days | ~$0.002/report* |
| 4 | 8-10 | 1 day | - |
| 5 | 11-12 | 3-5 days | ~$5 (human time) |
| 6 | 13-14 | 2-3 days | ~$0.006/report** |

*Per tech-design.md §14: batched gpt-4o-mini. With 20% escalation to gpt-4o: ~$0.02/report.
**Per tech-design.md §15.8: eval + correction + re-eval for 10% failure rate.

**Total:** ~2-3 weeks including calibration and correction workflow
