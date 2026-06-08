import json

import pytest

from api.domain.summary import (
    AggregationResult,
    MalformedAggregationError,
    validate_aggregation_json,
    validate_timeline,
)


def test_validate_timeline_happy_path():
    validate_timeline([{"timestamp": 1.0, "event": "Person enters frame"}])


def test_validate_timeline_missing_timestamp():
    with pytest.raises(MalformedAggregationError):
        validate_timeline([{"event": "something"}])


def test_validate_timeline_missing_event():
    with pytest.raises(MalformedAggregationError):
        validate_timeline([{"timestamp": 2.5}])


def test_validate_timeline_empty_list_passes():
    validate_timeline([])


def test_validate_aggregation_json_happy_path():
    raw = json.dumps({"summary": "A busy street.", "timeline": [{"timestamp": 0.0, "event": "Cars pass"}]})
    result = validate_aggregation_json(raw)
    assert isinstance(result, AggregationResult)
    assert result.summary == "A busy street."


def test_validate_aggregation_json_strips_markdown_fences():
    payload = {"summary": "Quiet park.", "timeline": []}
    raw = f"```json\n{json.dumps(payload)}\n```"
    result = validate_aggregation_json(raw)
    assert result.summary == "Quiet park."


def test_validate_aggregation_json_missing_summary():
    raw = json.dumps({"timeline": []})
    with pytest.raises(MalformedAggregationError):
        validate_aggregation_json(raw)


def test_validate_aggregation_json_missing_timeline():
    raw = json.dumps({"summary": "Something happened."})
    with pytest.raises(MalformedAggregationError):
        validate_aggregation_json(raw)
