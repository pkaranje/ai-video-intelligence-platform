import json
import re
from dataclasses import dataclass


class MalformedAggregationError(ValueError):
    pass


@dataclass
class AggregationResult:
    summary: str
    timeline: list[dict]


def validate_timeline(timeline: list) -> None:
    for i, item in enumerate(timeline):
        if not isinstance(item.get("timestamp"), (int, float)):
            raise MalformedAggregationError(
                f"Timeline item {i} missing valid 'timestamp' (float)."
            )
        if not isinstance(item.get("event"), str):
            raise MalformedAggregationError(
                f"Timeline item {i} missing valid 'event' (str)."
            )


def validate_aggregation_json(raw: str) -> AggregationResult:
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise MalformedAggregationError(
            f"Invalid JSON from aggregation: {exc}"
        ) from exc
    if not isinstance(data.get("summary"), str):
        raise MalformedAggregationError("Aggregation JSON missing 'summary' field.")
    if not isinstance(data.get("timeline"), list):
        raise MalformedAggregationError("Aggregation JSON missing 'timeline' field.")
    return AggregationResult(summary=data["summary"], timeline=data["timeline"])
