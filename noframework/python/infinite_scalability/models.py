from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Tuple, Literal

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"
    MISSING = "missing"


class FileRecord(BaseModel):
    id: Optional[int] = None
    path: str
    hash: str
    lang: str
    size: int
    mtime: datetime
    parsed: bool = True


class ChunkRecord(BaseModel):
    id: Optional[int] = None
    file_id: int
    start_line: int
    end_line: int
    kind: str
    text: str
    hash: str

    @field_validator("start_line", "end_line")
    @classmethod
    def positive_lines(cls, v: int) -> int:
        if v < 1:
            raise ValueError("line numbers must be >= 1")
        return v

    @field_validator("end_line")
    @classmethod
    def end_not_before_start(cls, v: int, info):
        start = info.data.get("start_line", 1)
        if v < start:
            raise ValueError("end_line must be >= start_line")
        return v


class SymbolRecord(BaseModel):
    id: Optional[int] = None
    file_id: int
    name: str
    kind: str
    signature: Optional[str] = None
    start_line: int
    end_line: int
    doc: Optional[str] = None
    parent_symbol_id: Optional[int] = None


class EdgeRecord(BaseModel):
    src_symbol_id: int
    dst_symbol_id: int
    edge_type: str  # import|call|inherits|uses|exports|declares


class SummaryRecord(BaseModel):
    id: Optional[int] = None
    level: Literal["file", "module", "package"]
    target_id: int
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClaimRecord(BaseModel):
    id: Optional[int] = None
    report_version: int
    text: str
    citation_refs: List[str] = Field(default_factory=list)
    status: ClaimStatus
    severity: Severity
    rationale: str


class ReportVersionRecord(BaseModel):
    id: Optional[int] = None
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    coverage_score: float
    citation_score: float
    issues_high: int
    issues_med: int
    issues_low: int


class ChunkEmbedding(BaseModel):
    chunk_id: int
    vector: bytes
    dim: int


class SymbolEmbedding(BaseModel):
    symbol_id: int
    vector: bytes
    dim: int


class ToolListFilesRequest(BaseModel):
    root: str
    respect_gitignore: bool = True


class ToolListFilesResponse(BaseModel):
    files: List[FileRecord]


class ToolGetChunksRequest(BaseModel):
    path: str
    line_range: Optional[Tuple[int, int]] = None


class ToolGetChunksResponse(BaseModel):
    chunks: List[ChunkRecord]


class SummaryOutput(BaseModel):
    text: str
    citations: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class ClaimCheckInput(BaseModel):
    claim: str
    citations: List[str]
    retrieved_chunks: List[ChunkRecord]


class ClaimCheckResult(BaseModel):
    status: ClaimStatus
    severity: Severity
    rationale: str


class RetrievedContext(BaseModel):
    chunks: List[ChunkRecord] = Field(default_factory=list)
    summaries: List["SummaryRecord"] = Field(default_factory=list)
    symbols: List["SymbolRecord"] = Field(default_factory=list)
    edges: List["EdgeRecord"] = Field(default_factory=list)


class CoverageGate(BaseModel):
    min_support_rate: float = 0.8
    min_coverage: float = 0.8
    min_citation_rate: float = 0.8
    max_high_issues: int = 0
    max_medium_issues: int = 5


class Issue(BaseModel):
    severity: Severity
    description: str
    fix_hint: Optional[str] = None


class IterationStatus(BaseModel):
    support_rate: float
    coverage: float
    citation_rate: float
    issues_high: int
    issues_med: int
    issues_low: int
