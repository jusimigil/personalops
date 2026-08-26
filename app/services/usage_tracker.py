import json
from datetime import datetime
from pathlib import Path


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

USAGE_FILE = BASE_DIR / "data" / "usage.json"

MODEL_NAME = "gemini-3.7-flash"

INPUT_COST_PER_MILLION = 0.75
OUTPUT_COST_PER_MILLION = 3.75

MONTHLY_BUDGET = 10.00


# --------------------------------------------------
# Storage
# --------------------------------------------------

def load_usage():
    """Load usage data from the local JSON database."""

    if not USAGE_FILE.exists():
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_thought_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests": []
        }

    with open(USAGE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_usage(usage):
    """Save usage data to the local JSON database."""

    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(USAGE_FILE, "w", encoding="utf-8") as file:
        json.dump(usage, file, indent=2)


# --------------------------------------------------
# Cost calculation
# --------------------------------------------------

def calculate_cost(input_tokens, output_tokens):
    """Calculate estimated API cost."""

    input_cost = (
        input_tokens / 1_000_000
    ) * INPUT_COST_PER_MILLION

    output_cost = (
        output_tokens / 1_000_000
    ) * OUTPUT_COST_PER_MILLION

    return input_cost + output_cost


# --------------------------------------------------
# Record usage
# --------------------------------------------------

def record_usage(
    input_tokens,
    output_tokens,
    thought_tokens=0,
    total_tokens=0,
    model=MODEL_NAME
):
    """Record one Gemini API interaction."""

    usage = load_usage()

    cost = calculate_cost(
        input_tokens,
        output_tokens
    )

    usage["total_requests"] += 1

    usage["total_input_tokens"] += input_tokens

    usage["total_output_tokens"] += output_tokens

    usage["total_thought_tokens"] += thought_tokens

    usage["total_tokens"] += total_tokens

    usage["total_cost"] += cost

    usage["requests"].append({
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thought_tokens": thought_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": cost
    })

    save_usage(usage)


# --------------------------------------------------
# Budget
# --------------------------------------------------

def get_remaining_budget():
    """Return remaining API budget."""

    usage = load_usage()

    return max(
        MONTHLY_BUDGET - usage["total_cost"],
        0
    )


def budget_exceeded():
    """Return True if the API budget has been reached."""

    return get_remaining_budget() <= 0


# --------------------------------------------------
# Summary
# --------------------------------------------------

def get_usage_summary():
    """Return a summary of API usage."""

    usage = load_usage()

    return {
        "requests": usage["total_requests"],
        "input_tokens": usage["total_input_tokens"],
        "output_tokens": usage["total_output_tokens"],
        "thought_tokens": usage["total_thought_tokens"],
        "total_tokens": usage["total_tokens"],
        "estimated_cost": usage["total_cost"],
        "remaining_budget": get_remaining_budget()
    }