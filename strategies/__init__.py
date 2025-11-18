#!/usr/bin/env python3
"""
Investment Strategies - Registry and exports
"""

from strategies.base import Strategy

# Import all strategies
from strategies.simple_recurring import SimpleRecurringStrategy
from strategies.rsi_swing import RSISwingStrategy
from strategies.macd_swing import MACDSwingStrategy
from strategies.macd_ema_trailing_stop import MACDEMATrailingStopStrategy

# Registry of available strategies
STRATEGIES = {
    'simple_recurring': SimpleRecurringStrategy,
    'rsi_swing': RSISwingStrategy,
    'macd_swing': MACDSwingStrategy,
    'macd_ema_trailing_stop': MACDEMATrailingStopStrategy
}


def get_strategy(strategy_id: str) -> Strategy:
    """Get a strategy instance by ID."""
    if strategy_id not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_id}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy_id]()
