#!/usr/bin/env python3
"""
MACD Swing Strategy: Buy when MACD crosses up, keep buying until MACD crosses down, repeat.
"""

import logging
from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import (
    fetch_and_update_prices,
    get_daily_prices,
    check_macd_crossover,
    check_macd_crossdown,
    is_macd_above_signal,
    calculate_macd
)

logger = logging.getLogger(__name__)


class MACDSwingStrategy(Strategy):
    """
    MACD Swing Strategy:
    - Buy when MACD crosses above Signal (bullish crossover)
    - Keep buying daily while MACD is above Signal
    - Stop buying when MACD crosses below Signal (bearish crossdown)
    - Wait for next MACD crossover up
    - Repeat cycle
    """
    
    @property
    def name(self) -> str:
        return "MACD Swing Strategy"
    
    @property
    def description(self) -> str:
        return "Buy when MACD crosses up, keep buying until MACD crosses down, repeat."
    
    @property
    def input_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'ticker',
                'label': 'Stock Ticker',
                'type': 'text',
                'default': 'AAPL',
                'required': True,
                'help': 'Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)'
            },
            {
                'name': 'start_date',
                'label': 'Start Date',
                'type': 'date',
                'default': date(2024, 1, 1),
                'required': True,
                'help': 'Start date for the investment period'
            },
            {
                'name': 'end_date',
                'label': 'End Date',
                'type': 'date',
                'default': date.today(),
                'required': True,
                'help': 'End date for the investment period'
            },
            {
                'name': 'daily_investment',
                'label': 'Daily Investment ($)',
                'type': 'number',
                'default': 100.0,
                'required': True,
                'min': 0.01,
                'help': 'Amount to invest each trading day when in buying mode'
            },
            {
                'name': 'macd_fast',
                'label': 'MACD Fast Period',
                'type': 'number',
                'default': 12,
                'required': False,
                'min': 2,
                'max': 50,
                'help': 'Fast EMA period for MACD calculation (default: 12)'
            },
            {
                'name': 'macd_slow',
                'label': 'MACD Slow Period',
                'type': 'number',
                'default': 26,
                'required': False,
                'min': 2,
                'max': 100,
                'help': 'Slow EMA period for MACD calculation (default: 26)'
            },
            {
                'name': 'macd_signal',
                'label': 'MACD Signal Period',
                'type': 'number',
                'default': 9,
                'required': False,
                'min': 2,
                'max': 50,
                'help': 'Signal line EMA period for MACD calculation (default: 9)'
            }
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate investment growth for MACD swing strategy.
        """
        ticker = params['ticker'].strip().upper()
        start_date = params['start_date']
        end_date = params['end_date']
        daily_investment = params['daily_investment']
        macd_fast = int(params.get('macd_fast', 12))
        macd_slow = int(params.get('macd_slow', 26))
        macd_signal = int(params.get('macd_signal', 9))
        
        logger.debug(f"MACD Swing Strategy: Starting calculation for {ticker}")
        logger.debug(f"Parameters: start_date={start_date}, end_date={end_date}, daily_investment=${daily_investment}")
        logger.debug(f"MACD parameters: fast={macd_fast}, slow={macd_slow}, signal={macd_signal}")
        
        # Calculate lookback period needed for MACD calculation
        # We need at least slow_period + signal_period + buffer days before start_date
        from datetime import timedelta
        lookback_days = macd_slow + macd_signal + 60  # Extra buffer for safety (accounting for weekends/holidays)
        fetch_start_date = start_date - timedelta(days=lookback_days)
        
        logger.debug(f"Fetching data from {fetch_start_date} to {end_date} (lookback: {lookback_days} days for MACD calculation)")
        
        # Ensure we have data in the database (with lookback for MACD calculation)
        fetch_and_update_prices(db_path, ticker, fetch_start_date, end_date)
        
        # Get daily prices for the investment period
        prices_df = get_daily_prices(db_path, ticker, start_date, end_date)
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker} in the specified date range.")
        
        logger.debug(f"Retrieved {len(prices_df)} trading days of data")
        
        # Pre-calculate MACD for all dates we'll need (more efficient than recalculating each time)
        # Get all historical prices needed for MACD calculation
        all_prices_df = get_daily_prices(db_path, ticker, fetch_start_date, end_date)
        
        # Pre-calculate MACD for all available dates (more efficient)
        macd_all_df = None
        if not all_prices_df.empty and len(all_prices_df) >= (macd_slow + macd_signal):
            macd_all_df = calculate_macd(all_prices_df['close'], macd_fast, macd_slow, macd_signal)
            logger.debug(f"Pre-calculated MACD for {len(macd_all_df)} dates")
        else:
            logger.debug(f"Warning: Not enough data for MACD calculation. Got {len(all_prices_df) if not all_prices_df.empty else 0} days, need at least {macd_slow + macd_signal}")
        
        # Initialize tracking variables
        stocks_owned = 0.0
        total_invested = 0.0
        cash = 0.0
        
        # Check initial state: if MACD is above Signal at start date, start buying immediately
        is_buying = is_macd_above_signal(
            db_path, ticker, start_date,
            macd_fast, macd_slow, macd_signal
        )
        
        # Get initial MACD values for logging (use pre-calculated MACD if available)
        initial_macd_val, initial_signal_val, initial_histogram_val = None, None, None
        if macd_all_df is not None and not macd_all_df.empty:
            initial_macd_filtered = macd_all_df[macd_all_df.index.date <= start_date]
            if not initial_macd_filtered.empty:
                initial_row = initial_macd_filtered.iloc[-1]
                initial_macd_val = initial_row['macd'] if pd.notna(initial_row['macd']) else None
                initial_signal_val = initial_row['signal'] if pd.notna(initial_row['signal']) else None
                initial_histogram_val = initial_row['histogram'] if pd.notna(initial_row['histogram']) else None
        
        if is_buying:
            if initial_macd_val is not None:
                logger.debug(
                    f"Initial state on {start_date}: MACD > Signal, starting in buying mode. "
                    f"MACD Line={initial_macd_val:.4f}, Signal Line={initial_signal_val:.4f}, Histogram={initial_histogram_val:.4f}"
                )
            else:
                logger.debug(f"Initial state on {start_date}: MACD > Signal, starting in buying mode. MACD values unavailable")
        else:
            if initial_macd_val is not None:
                logger.debug(
                    f"Initial state on {start_date}: MACD <= Signal, starting in waiting mode. "
                    f"MACD Line={initial_macd_val:.4f}, Signal Line={initial_signal_val:.4f}, Histogram={initial_histogram_val:.4f}"
                )
            else:
                logger.debug(f"Initial state on {start_date}: MACD <= Signal, starting in waiting mode. MACD values unavailable")
        
        results = []
        
        # Helper function to get MACD values for a specific date from pre-calculated data
        def get_macd_values(check_date: date):
            """Get MACD, Signal, and Histogram values for a specific date from pre-calculated MACD."""
            if macd_all_df is None or macd_all_df.empty:
                return None, None, None
            
            # Filter to dates up to check_date
            macd_filtered = macd_all_df[macd_all_df.index.date <= check_date]
            
            if macd_filtered.empty:
                return None, None, None
            
            # Get the most recent MACD values
            latest_row = macd_filtered.iloc[-1]
            
            macd_val = latest_row['macd'] if pd.notna(latest_row['macd']) else None
            signal_val = latest_row['signal'] if pd.notna(latest_row['signal']) else None
            histogram_val = latest_row['histogram'] if pd.notna(latest_row['histogram']) else None
            
            return macd_val, signal_val, histogram_val
        
        for date_idx, row in prices_df.iterrows():
            current_date = date_idx.date()
            current_price = row['close']
            
            # Get MACD values for current date
            macd_val, signal_val, histogram_val = get_macd_values(current_date)
            
            # Calculate current portfolio value
            portfolio_value = cash + (stocks_owned * current_price)
            
            # Check current MACD state and crossovers
            if not is_buying:
                # Check for MACD crossover (bullish - start buying)
                crossover_up = check_macd_crossover(
                    db_path, ticker, current_date,
                    macd_fast, macd_slow, macd_signal
                )
                # Also check if MACD is currently above Signal (in case we missed the crossover)
                macd_above_signal = (macd_val is not None and signal_val is not None and macd_val > signal_val)
                
                if crossover_up or macd_above_signal:
                    # Start buying
                    is_buying = True
                    if macd_val is not None:
                        if crossover_up:
                            logger.debug(
                                f"MACD crossover detected on {current_date}: Entering buying mode. "
                                f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                            )
                        else:
                            logger.debug(
                                f"MACD above Signal on {current_date}: Entering buying mode (no crossover, but MACD > Signal). "
                                f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                            )
                    else:
                        logger.debug(f"MACD crossover/above Signal detected on {current_date}: Entering buying mode. MACD values unavailable")
            
            # Check for MACD crossdown (bearish - stop buying and sell)
            if is_buying:
                crossdown = check_macd_crossdown(
                    db_path, ticker, current_date,
                    macd_fast, macd_slow, macd_signal
                )
                # Also check if MACD is currently below Signal (in case we missed the crossdown)
                macd_below_signal = (macd_val is not None and signal_val is not None and macd_val <= signal_val)
                
                if crossdown or macd_below_signal:
                    # Sell all shares and convert to cash
                    shares_to_sell = stocks_owned
                    portfolio_value_before_sell = cash + (stocks_owned * current_price)
                    cash = portfolio_value_before_sell  # Convert all shares to cash
                    stocks_owned = 0.0  # Sell all shares
                    
                    # Stop buying
                    is_buying = False
                    if macd_val is not None:
                        if crossdown:
                            logger.debug(
                                f"MACD crossdown detected on {current_date}: Selling all shares and entering waiting mode. "
                                f"Sold {shares_to_sell:.6f} shares @ ${current_price:.2f}, Cash: ${cash:.2f}. "
                                f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                            )
                        else:
                            logger.debug(
                                f"MACD below/equal Signal on {current_date}: Selling all shares and entering waiting mode. "
                                f"Sold {shares_to_sell:.6f} shares @ ${current_price:.2f}, Cash: ${cash:.2f}. "
                                f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                            )
                    else:
                        logger.debug(f"MACD crossdown/below Signal detected on {current_date}: Selling all shares and entering waiting mode. Sold {shares_to_sell:.6f} shares, Cash: ${cash:.2f}. MACD values unavailable")
            
            # Buy if in buying mode
            investment_amount = 0.0
            shares_bought = 0.0
            
            if is_buying:
                # Use cash first, then add daily investment
                total_available = cash + daily_investment
                if total_available > 0 and current_price > 0:
                    shares_bought = total_available / current_price
                    stocks_owned += shares_bought
                    total_invested += daily_investment
                    cash = 0.0  # All cash used for buying
                    investment_amount = total_available
                    if macd_val is not None:
                        logger.debug(
                            f"Date: {current_date}, Buying: {shares_bought:.6f} shares at ${current_price:.2f}, "
                            f"Investment: ${investment_amount:.2f} (cash=${cash:.2f} + daily=${daily_investment:.2f}). "
                            f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                        )
                    else:
                        logger.debug(
                            f"Date: {current_date}, Buying: {shares_bought:.6f} shares at ${current_price:.2f}, "
                            f"Investment: ${investment_amount:.2f} (cash=${cash:.2f} + daily=${daily_investment:.2f}). "
                            f"MACD values unavailable"
                        )
            else:
                if macd_val is not None:
                    logger.debug(
                        f"Date: {current_date}, Waiting mode: No investment. "
                        f"Cash: ${cash:.2f}, Shares: {stocks_owned:.6f}, Portfolio Value: ${portfolio_value:.2f}. "
                        f"MACD Line={macd_val:.4f}, Signal Line={signal_val:.4f}, Histogram={histogram_val:.4f}"
                    )
                else:
                    logger.debug(
                        f"Date: {current_date}, Waiting mode: No investment. "
                        f"Cash: ${cash:.2f}, Shares: {stocks_owned:.6f}, Portfolio Value: ${portfolio_value:.2f}. "
                        f"MACD values unavailable"
                    )
            
            # Recalculate portfolio value after all transactions
            portfolio_value = cash + (stocks_owned * current_price)
            profit_loss = portfolio_value - total_invested
            
            # Determine current state for display
            current_state = "Buying" if is_buying else "Waiting for MACD Crossover Up"
            
            results.append({
                'Date': current_date,
                'Investment $': round(investment_amount, 2),
                'Stocks Bought': round(shares_bought, 6),
                'Stocks': round(stocks_owned, 6),
                'Total Account': round(portfolio_value, 2),
                'Profit/Loss': round(profit_loss, 2),
                'Principal Invested': round(total_invested, 2),
                'Current State': current_state
            })
        
        return pd.DataFrame(results)

