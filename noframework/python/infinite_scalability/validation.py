from typing import List

from .citations import validate_citation
from .models import SummaryRecord
from .store import Store


def validate_summary(store: Store, summary: SummaryRecord) -> None:
    if not summary.text.strip():
        raise ValueError("Summary text is empty")
    citations = [tok.strip("[]") for tok in summary.text.split() if tok.startswith("[") and tok.endswith("]")]
    if not citations:
        raise ValueError("Summary missing citations")
    for cit in citations:
        path, start, end = validate_citation(cit)
        file_rec = store.get_file_by_path(path)
        if not file_rec:
            raise ValueError(f"Citation references unknown file: {path}")
        chunk = store.find_chunk_covering_range(file_rec.id, start, end)
        if not chunk:
            raise ValueError(f"Citation range not found in file: {cit}")
