from dataclasses import dataclass


@dataclass
class ExtractionMessage:
    job_id: str


@dataclass
class AnalysisBatchMessage:
    job_id: str
    frame_ids: list[str]


@dataclass
class AggregationMessage:
    job_id: str
