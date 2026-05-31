"""
Negative-path tests for src/amoa/llm.py.

W1 harness deliverable: verify malformed LLM outputs trigger correct error
paths, categories are logged to failures.jsonl, and exceptions propagate.

All tests patch _call_provider so no real API calls are made.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from pydantic import BaseModel

from amoa.llm import (
    structured_completion,
    CATEGORY_MALFORMED_JSON,
    CATEGORY_SCHEMA_VIOLATION,
    CATEGORY_RATE_LIMIT,
)


class _Sample(BaseModel):
    value: int
    label: str


def _read_failures(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.asyncio
async def test_malformed_json_logs_failure_and_raises(tmp_path, monkeypatch):
    """_call_provider returns unparseable text → malformed_json logged, ValueError raised."""
    monkeypatch.setattr("amoa.llm.FAILURES_LOG", tmp_path / "failures.jsonl")

    with patch("amoa.llm._call_provider", new=AsyncMock(return_value="not {{ valid json")):
        with pytest.raises(ValueError, match="structured_completion failed"):
            await structured_completion("sys", "user", _Sample, provider="groq")

    records = _read_failures(tmp_path / "failures.jsonl")
    assert len(records) == 1
    assert records[0]["category"] == CATEGORY_MALFORMED_JSON
    assert records[0]["schema"] == "_Sample"


@pytest.mark.asyncio
async def test_schema_violation_logs_failure_and_raises(tmp_path, monkeypatch):
    """_call_provider returns valid JSON with wrong fields → schema_violation logged, ValueError raised."""
    monkeypatch.setattr("amoa.llm.FAILURES_LOG", tmp_path / "failures.jsonl")

    bad_payload = json.dumps({"unexpected_key": "oops"})  # missing value + label
    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=bad_payload)):
        with pytest.raises(ValueError, match="structured_completion failed"):
            await structured_completion("sys", "user", _Sample, provider="groq")

    records = _read_failures(tmp_path / "failures.jsonl")
    assert len(records) == 1
    assert records[0]["category"] == CATEGORY_SCHEMA_VIOLATION
    assert records[0]["schema"] == "_Sample"


@pytest.mark.asyncio
async def test_rate_limit_logs_failure_and_reraises(tmp_path, monkeypatch):
    """_call_provider raises 429 error → rate_limit logged, original exception re-raised immediately."""
    monkeypatch.setattr("amoa.llm.FAILURES_LOG", tmp_path / "failures.jsonl")

    api_error = Exception("HTTP 429 Too Many Requests — rate limit exceeded")
    with patch("amoa.llm._call_provider", new=AsyncMock(side_effect=api_error)):
        with pytest.raises(Exception, match="429"):
            await structured_completion("sys", "user", _Sample, provider="groq")

    records = _read_failures(tmp_path / "failures.jsonl")
    assert len(records) == 1
    assert records[0]["category"] == CATEGORY_RATE_LIMIT
    # Rate-limit error exits on first attempt — _call_provider called once only
