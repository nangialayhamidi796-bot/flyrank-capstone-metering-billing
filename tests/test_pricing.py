from app.pricing import (
    CACHED_INPUT_PRICE_MICROCENTS_PER_1K,
    INPUT_PRICE_MICROCENTS_PER_1K,
    OUTPUT_PRICE_MICROCENTS_PER_1K,
    calculate_token_cost_microcents,
)


def test_pricing_constants_are_pinned():
    """Pricing constants must not change accidentally."""

    assert INPUT_PRICE_MICROCENTS_PER_1K == 250_000
    assert CACHED_INPUT_PRICE_MICROCENTS_PER_1K == 25_000
    assert OUTPUT_PRICE_MICROCENTS_PER_1K == 1_000_000


def test_token_categories_are_priced_separately():
    """Fresh, cached, and output tokens use different prices."""

    cost = calculate_token_cost_microcents(
        input_tokens=1000,
        cached_input_tokens=1000,
        output_tokens=1000,
        reasoning_tokens=0,
    )

    assert cost == 1_275_000


def test_reasoning_tokens_use_output_price():
    """Reasoning tokens must be billed as output tokens."""

    cost = calculate_token_cost_microcents(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=500,
        reasoning_tokens=500,
    )

    assert cost == 1_000_000


def test_cached_input_is_cheaper_than_fresh_input():
    """Cached input must not use the normal input rate."""

    fresh_cost = calculate_token_cost_microcents(
        input_tokens=1000,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_tokens=0,
    )

    cached_cost = calculate_token_cost_microcents(
        input_tokens=0,
        cached_input_tokens=1000,
        output_tokens=0,
        reasoning_tokens=0,
    )

    assert fresh_cost == 250_000
    assert cached_cost == 25_000
    assert cached_cost < fresh_cost