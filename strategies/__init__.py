#!/usr/bin/env python3
"""
Investment Strategies - Registry and exports
"""

from strategies.base import Strategy

# Import all strategies
from strategies.simple_recurring import SimpleRecurringStrategy
from strategies.rsi_swing import RSISwingStrategy

# Registry of available strategies
STRATEGIES = {
    'simple_recurring': SimpleRecurringStrategy,
    'rsi_swing': RSISwingStrategy
}


def get_strategy(strategy_id: str) -> Strategy:
    """Get a strategy instance by ID."""
    if strategy_id not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_id}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy_id]()
