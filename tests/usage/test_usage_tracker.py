"""Tests for the UsageTracker class."""

from unittest.mock import Mock

import pytest

from sidekick.usage import ModelUsage, UsageTracker

# Tests for ModelUsage dataclass


def test_model_usage_initial_state():
    """Test initial state of ModelUsage."""
    usage = ModelUsage()
    assert usage.requests == 0
    assert usage.input_tokens == 0
    assert usage.cached_tokens == 0
    assert usage.output_tokens == 0
    assert usage.total_cost == 0.0


def test_model_usage_add_usage():
    """Test adding usage data."""
    usage = ModelUsage()
    usage.add_usage(1000, 200, 500, 0.01)

    assert usage.requests == 1
    assert usage.input_tokens == 1000
    assert usage.cached_tokens == 200
    assert usage.output_tokens == 500
    assert usage.total_cost == 0.01

    # Add more usage
    usage.add_usage(500, 100, 250, 0.005)

    assert usage.requests == 2
    assert usage.input_tokens == 1500
    assert usage.cached_tokens == 300
    assert usage.output_tokens == 750
    assert usage.total_cost == 0.015


# Tests for UsageTracker class


def test_usage_tracker_initial_state():
    """Test initial state of UsageTracker."""
    tracker = UsageTracker()
    assert tracker.model_usage == {}
    assert tracker.last_request is None
    assert tracker.total_tokens == 0
    assert tracker.total_cost == 0.0
    assert tracker.total_requests == 0


def test_record_usage_basic():
    """Test basic usage recording without cached tokens."""
    tracker = UsageTracker()

    # Mock usage object
    usage = Mock()
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.details = []

    tracker.record_usage("openai:o4-mini", usage)

    # Check model usage was recorded
    assert "openai:o4-mini" in tracker.model_usage
    model_usage = tracker.model_usage["openai:o4-mini"]
    assert model_usage.requests == 1
    assert model_usage.input_tokens == 1000
    assert model_usage.output_tokens == 500
    assert model_usage.cached_tokens == 0

    # Check last request
    assert tracker.last_request is not None
    assert tracker.last_request["model"] == "openai:o4-mini"
    assert tracker.last_request["input_tokens"] == 1000
    assert tracker.last_request["output_tokens"] == 500

    # Check totals
    assert tracker.total_tokens == 1500
    assert tracker.total_requests == 1


def test_record_usage_with_cached_tokens():
    """Test usage recording with cached tokens."""
    tracker = UsageTracker()

    # Mock usage object with cached tokens
    usage = Mock()
    usage.request_tokens = 1000
    usage.response_tokens = 500

    detail = Mock()
    detail.cached_tokens = 300
    usage.details = [detail]

    tracker.record_usage("anthropic:claude-3-7-sonnet-latest", usage)

    # Check cached tokens were recorded
    model_usage = tracker.model_usage["anthropic:claude-3-7-sonnet-latest"]
    assert model_usage.cached_tokens == 300

    # Check last request has cached tokens
    assert tracker.last_request["cached_tokens"] == 300


def test_record_usage_multiple_models():
    """Test recording usage for multiple models."""
    tracker = UsageTracker()

    # First model
    usage1 = Mock()
    usage1.request_tokens = 1000
    usage1.response_tokens = 500
    usage1.details = []

    tracker.record_usage("openai:o4-mini", usage1)

    # Second model
    usage2 = Mock()
    usage2.request_tokens = 2000
    usage2.response_tokens = 1000
    usage2.details = []

    tracker.record_usage("anthropic:claude-3-7-sonnet-latest", usage2)

    # Check both models are tracked
    assert len(tracker.model_usage) == 2
    assert "openai:o4-mini" in tracker.model_usage
    assert "anthropic:claude-3-7-sonnet-latest" in tracker.model_usage

    # Check totals include both models
    assert tracker.total_tokens == 4500  # 1500 + 3000
    assert tracker.total_requests == 2


def test_record_usage_same_model_multiple_times():
    """Test recording multiple usages for the same model."""
    tracker = UsageTracker()

    # First usage
    usage1 = Mock()
    usage1.request_tokens = 1000
    usage1.response_tokens = 500
    usage1.details = []

    tracker.record_usage("openai:o4-mini", usage1)

    # Second usage for same model
    usage2 = Mock()
    usage2.request_tokens = 500
    usage2.response_tokens = 250
    usage2.details = []

    tracker.record_usage("openai:o4-mini", usage2)

    # Check cumulative stats
    model_usage = tracker.model_usage["openai:o4-mini"]
    assert model_usage.requests == 2
    assert model_usage.input_tokens == 1500
    assert model_usage.output_tokens == 750

    assert tracker.total_tokens == 2250
    assert tracker.total_requests == 2


def test_cost_calculation():
    """Test that costs are calculated correctly."""
    tracker = UsageTracker()

    usage = Mock()
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.details = []

    tracker.record_usage("openai:o4-mini", usage)

    # Check cost calculation (o4-mini pricing: $1.10/$0.275/$4.40 per 1M)
    expected_input_cost = 1000 / 1_000_000 * 1.10
    expected_output_cost = 500 / 1_000_000 * 4.40
    expected_total = expected_input_cost + expected_output_cost

    assert tracker.last_request["input_cost"] == pytest.approx(expected_input_cost)
    assert tracker.last_request["output_cost"] == pytest.approx(expected_output_cost)
    assert tracker.last_request["request_cost"] == pytest.approx(expected_total)
    assert tracker.total_cost == pytest.approx(expected_total)


def test_unknown_model_fallback():
    """Test that unknown models fall back to first model pricing."""
    tracker = UsageTracker()

    usage = Mock()
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.details = []

    tracker.record_usage("unknown:model", usage)

    # Should use first model's pricing (anthropic:claude-opus-4-0)
    expected_input_cost = 1000 / 1_000_000 * 3.00
    expected_output_cost = 500 / 1_000_000 * 15.00

    assert tracker.last_request["input_cost"] == pytest.approx(expected_input_cost)
    assert tracker.last_request["output_cost"] == pytest.approx(expected_output_cost)
