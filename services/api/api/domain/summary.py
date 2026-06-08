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
