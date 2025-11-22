from dataclasses import dataclass
from typing import List

from .models import ClaimRecord


@dataclass
class CoverageResult:
    expected: int
    covered: int

    @property
    def score(self) -> float:
        if self.expected == 0:
            return 1.0
        return min(1.0, self.covered / self.expected)


def assess_coverage(expected_items: int, claims: List[ClaimRecord]) -> CoverageResult:
    """
    Placeholder coverage: assume expected_items provided; covered = supported claims.
    """
    supported = sum(1 for c in claims if c.status == c.status.SUPPORTED)
    return CoverageResult(expected=expected_items, covered=supported)
