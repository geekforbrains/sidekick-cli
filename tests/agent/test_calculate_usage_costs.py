"""Tests for the _calculate_usage_costs function."""

from unittest.mock import Mock, patch

import pytest

from sidekick.agent import _calculate_usage_costs


def test_basic_usage_calculation():
    """Test basic usage calculation without cached tokens."""
    usage = Mock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500
    usage.details = []

    # Mock session to have a model and total cost
    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "openai:gpt-4o"
        mock_session.total_cost = 0.0

        result = _calculate_usage_costs(usage)

        # Verify the structure
        assert result["requests"] == 1
        assert result["input_tokens"] == 1000
        assert result["cached_tokens"] == 0
        assert result["output_tokens"] == 500

        # Verify costs (based on gpt-4o pricing: $2.50/$1.25/$10.00 per 1M)
        expected_input_cost = 1000 / 1_000_000 * 2.50
        expected_output_cost = 500 / 1_000_000 * 10.00
        expected_request_cost = expected_input_cost + expected_output_cost

        assert result["input_cost"] == pytest.approx(expected_input_cost)
        assert result["cached_cost"] == 0.0
        assert result["output_cost"] == pytest.approx(expected_output_cost)
        assert result["request_cost"] == pytest.approx(expected_request_cost)
        assert result["total_cost"] == pytest.approx(expected_request_cost)


def test_usage_with_cached_tokens():
    """Test usage calculation with cached tokens."""
    usage = Mock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500

    # Mock details with cached tokens
    detail = Mock()
    detail.cached_tokens = 300
    usage.details = [detail]

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "openai:gpt-4o"
        mock_session.total_cost = 0.01  # Existing cost

        result = _calculate_usage_costs(usage)

        # Verify token breakdown
        assert result["input_tokens"] == 1000
        assert result["cached_tokens"] == 300
        assert result["output_tokens"] == 500

        # Verify costs (non-cached: 700 tokens)
        expected_input_cost = 700 / 1_000_000 * 2.50
        expected_cached_cost = 300 / 1_000_000 * 1.25
        expected_output_cost = 500 / 1_000_000 * 10.00
        expected_request_cost = expected_input_cost + expected_cached_cost + expected_output_cost

        assert result["input_cost"] == pytest.approx(expected_input_cost)
        assert result["cached_cost"] == pytest.approx(expected_cached_cost)
        assert result["output_cost"] == pytest.approx(expected_output_cost)
        assert result["request_cost"] == pytest.approx(expected_request_cost)
        assert result["total_cost"] == pytest.approx(0.01 + expected_request_cost)


def test_usage_with_multiple_cached_details():
    """Test usage calculation with multiple detail objects containing cached tokens."""
    usage = Mock()
    usage.requests = 2
    usage.request_tokens = 2000
    usage.response_tokens = 1000
    usage.total_tokens = 3000

    # Multiple details with cached tokens
    detail1 = Mock()
    detail1.cached_tokens = 300
    detail2 = Mock()
    detail2.cached_tokens = 200
    usage.details = [detail1, detail2]

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "anthropic:claude-3-7-sonnet-latest"
        mock_session.total_cost = 0.0

        result = _calculate_usage_costs(usage)

        # Total cached tokens should be sum
        assert result["cached_tokens"] == 500

        # Verify costs with Claude pricing: $3.00/$1.50/$15.00 per 1M
        non_cached = 1500  # 2000 - 500
        expected_input_cost = non_cached / 1_000_000 * 3.00
        expected_cached_cost = 500 / 1_000_000 * 1.50
        expected_output_cost = 1000 / 1_000_000 * 15.00

        assert result["input_cost"] == pytest.approx(expected_input_cost)
        assert result["cached_cost"] == pytest.approx(expected_cached_cost)
        assert result["output_cost"] == pytest.approx(expected_output_cost)


def test_usage_without_details_attribute():
    """Test usage calculation when usage object has no details attribute."""
    usage = Mock(spec=["requests", "request_tokens", "response_tokens", "total_tokens"])
    usage.requests = 1
    usage.request_tokens = 500
    usage.response_tokens = 250
    usage.total_tokens = 750
    # No details attribute

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "openai:gpt-4o"
        mock_session.total_cost = 0.0

        result = _calculate_usage_costs(usage)

        # Should handle missing details gracefully
        assert result["cached_tokens"] == 0
        assert result["input_tokens"] == 500


def test_fallback_to_first_model_pricing():
    """Test that unknown model falls back to first model's pricing."""
    usage = Mock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500
    usage.details = []

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "unknown:model"
        mock_session.total_cost = 0.0

        result = _calculate_usage_costs(usage)

        # Should use first model's pricing (anthropic:claude-3-7-sonnet-latest)
        expected_input_cost = 1000 / 1_000_000 * 3.00
        expected_output_cost = 500 / 1_000_000 * 15.00

        assert result["input_cost"] == pytest.approx(expected_input_cost)
        assert result["output_cost"] == pytest.approx(expected_output_cost)


def test_detail_without_cached_tokens_attribute():
    """Test handling details that don't have cached_tokens attribute."""
    usage = Mock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500

    # Mix of details with and without cached_tokens
    detail1 = Mock()
    detail1.cached_tokens = 200
    detail2 = Mock(spec=[])  # No cached_tokens attribute
    detail3 = Mock()
    detail3.cached_tokens = 100
    usage.details = [detail1, detail2, detail3]

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "openai:gpt-4o"
        mock_session.total_cost = 0.0

        result = _calculate_usage_costs(usage)

        # Should only sum the available cached tokens
        assert result["cached_tokens"] == 300


def test_cumulative_total_cost():
    """Test that total_cost accumulates correctly across multiple calls."""
    usage = Mock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500
    usage.details = []

    with patch("sidekick.agent.session") as mock_session:
        mock_session.current_model = "openai:gpt-4o"
        mock_session.total_cost = 0.05  # Existing total

        result = _calculate_usage_costs(usage)

        # Calculate expected cost
        expected_request_cost = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)

        # Total should include previous total
        assert result["total_cost"] == pytest.approx(0.05 + expected_request_cost)
