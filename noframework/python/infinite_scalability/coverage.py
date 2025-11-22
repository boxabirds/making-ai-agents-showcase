from dataclasses import dataclass
from typing import Iterable, List, Set

from .models import ClaimRecord, Severity, CoverageGate, Issue
from .store import Store
from .citations import validate_citation


@dataclass
class CoverageResult:
    expected: int
    covered: int
    missing_items: List[str]

    @property
    def score(self) -> float:
        if self.expected == 0:
            return 1.0
        return min(1.0, self.covered / self.expected)


def _expected_surface(store: Store) -> Set[str]:
    """
    Build the expected surface from symbols; each symbol name is a target.
    """
    targets: Set[str] = set()
    for f in store.get_all_files():
        for sym in store.get_symbols_for_file(f.id):
            targets.add(f"{f.path}::{sym.name}")
    if not targets:
        targets = {f.path for f in store.get_all_files()}
    return targets


def assess_coverage(store: Store, claims: List[ClaimRecord]) -> CoverageResult:
    """
    Coverage = fraction of expected targets mentioned in supported claims.
    A claim "covers" a target if the claim cites a chunk belonging to the target file or names the target explicitly.
    """
    targets = _expected_surface(store)
    covered: Set[str] = set()
    for claim in claims:
        if claim.status != claim.status.SUPPORTED:
            continue
        # cover by citation path
        for cit in claim.citation_refs:
            try:
                path, _, _ = validate_citation(cit)
            except Exception:
                continue
            for tgt in targets:
                if tgt.startswith(path):
                    covered.add(tgt)
        # fallback: explicit mention
        for tgt in targets:
            if tgt in claim.text:
                covered.add(tgt)
    missing = sorted(list(targets - covered))
    return CoverageResult(expected=len(targets), covered=len(covered), missing_items=missing)


def plan_issues(coverage: CoverageResult, claims: List[ClaimRecord]) -> List[Issue]:
    """
    Merge claim problems and coverage gaps into an ordered issue list.
    """
    issues: List[Issue] = []
    # claim-derived issues
    for c in claims:
        if c.status == c.status.SUPPORTED:
            continue
        sev = Severity.HIGH if c.severity == Severity.HIGH else Severity.MEDIUM
        issues.append(
            Issue(
                severity=sev,
                description=f"Claim unresolved: {c.text}",
                fix_hint="Find supporting evidence or revise claim.",
            )
        )
    # coverage gaps
    for missing in coverage.missing_items:
        issues.append(
            Issue(
                severity=Severity.MEDIUM,
                description=f"Missing coverage for {missing}",
                fix_hint="Add claim with citation that covers this target.",
            )
        )
    # sort: high first, then medium, then low
    issues.sort(key=lambda i: {"high": 0, "medium": 1, "low": 2}[i.severity.value])
    return issues


def gate_should_continue(gate: CoverageGate, coverage: CoverageResult, claims: List[ClaimRecord]) -> bool:
    """
    Decide whether to continue iterating based on gate thresholds.
    """
    total_claims = len(claims) or 1
    support_rate = sum(1 for c in claims if c.status == c.status.SUPPORTED) / total_claims
    citation_rate = sum(1 for c in claims if c.citation_refs) / total_claims
    missing_citations = sum(1 for c in claims if not c.citation_refs)
    issues_high = sum(1 for c in claims if c.severity == Severity.HIGH)
    issues_med = sum(1 for c in claims if c.severity == Severity.MEDIUM)

    return not (
        issues_high <= gate.max_high_issues
        and issues_med <= gate.max_medium_issues
        and coverage.score >= gate.min_coverage
        and support_rate >= gate.min_support_rate
        and citation_rate >= gate.min_citation_rate
        and missing_citations == 0
    )
