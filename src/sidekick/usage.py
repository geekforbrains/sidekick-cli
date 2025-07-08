"""Usage tracking for model API calls."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sidekick.constants import MODELS


@dataclass
class ModelUsage:
    """Usage statistics for a specific model."""

    requests: int = 0
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0

    def add_usage(
        self, input_tokens: int, cached_tokens: int, output_tokens: int, cost: float
    ) -> None:
        """Add usage data to this model's totals."""
        self.requests += 1
        self.input_tokens += input_tokens
        self.cached_tokens += cached_tokens
        self.output_tokens += output_tokens
        self.total_cost += cost


@dataclass
class UsageTracker:
    """Tracks token usage and costs across multiple models."""

    # Usage per model
    model_usage: Dict[str, ModelUsage] = field(default_factory=dict)

    # Last request details (for display)
    last_request: Optional[Dict[str, Any]] = None

    def record_usage(self, model: str, usage: Any) -> None:
        """Record usage from a model run.

        Args:
            model: Model identifier
            usage: Usage object from pydantic_ai
        """
        # Extract token counts
        cached_tokens = 0
        if hasattr(usage, "details") and usage.details:
            for detail in usage.details:
                if hasattr(detail, "cached_tokens"):
                    cached_tokens += detail.cached_tokens

        input_tokens = usage.request_tokens
        non_cached_input = input_tokens - cached_tokens
        output_tokens = usage.response_tokens

        # Calculate costs
        model_ids = list(MODELS.keys())
        pricing = MODELS.get(model, MODELS[model_ids[0]])["pricing"]

        input_cost = non_cached_input / 1_000_000 * pricing["input"]
        cached_cost = cached_tokens / 1_000_000 * pricing["cached_input"]
        output_cost = output_tokens / 1_000_000 * pricing["output"]
        request_cost = input_cost + cached_cost + output_cost

        # Store usage
        if model not in self.model_usage:
            self.model_usage[model] = ModelUsage()

        self.model_usage[model].add_usage(input_tokens, cached_tokens, output_tokens, request_cost)

        # Store last request details for display
        self.last_request = {
            "model": model,
            "input_tokens": input_tokens,
            "cached_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "cached_cost": cached_cost,
            "output_cost": output_cost,
            "request_cost": request_cost,
            "total_cost": self.total_cost,
        }

    @property
    def total_tokens(self) -> int:
        """Get total tokens across all models."""
        return sum(usage.input_tokens + usage.output_tokens for usage in self.model_usage.values())

    @property
    def total_cost(self) -> float:
        """Get total cost across all models."""
        return sum(usage.total_cost for usage in self.model_usage.values())

    @property
    def total_requests(self) -> int:
        """Get total requests across all models."""
        return sum(usage.requests for usage in self.model_usage.values())


# Global usage tracker instance
usage_tracker = UsageTracker()
