# Prices are stored as integer microcents per 1,000 tokens.
#
# 1 cent = 1,000,000 microcents.
# Using integers prevents floating-point money errors.

INPUT_PRICE_MICROCENTS_PER_1K = 250_000
CACHED_INPUT_PRICE_MICROCENTS_PER_1K = 25_000
OUTPUT_PRICE_MICROCENTS_PER_1K = 1_000_000


def calculate_token_cost_microcents(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> int:
    """Calculate token cost using integer-only arithmetic."""

    input_cost = (
        input_tokens
        * INPUT_PRICE_MICROCENTS_PER_1K
        // 1000
    )

    cached_input_cost = (
        cached_input_tokens
        * CACHED_INPUT_PRICE_MICROCENTS_PER_1K
        // 1000
    )

    billable_output_tokens = (
        output_tokens
        + reasoning_tokens
    )

    output_cost = (
        billable_output_tokens
        * OUTPUT_PRICE_MICROCENTS_PER_1K
        // 1000
    )

    return (
        input_cost
        + cached_input_cost
        + output_cost
    )