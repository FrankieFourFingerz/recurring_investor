#!/usr/bin/env python3
"""
MACD EMA Trailing Stop Strategy: Buy when MACD > Signal and price > 50 EMA, 
sell when profit drops 10% from previous high.
"""

import logging
from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import (
    fetch_and_update_prices,
    get_daily_prices,
    is_macd_above_signal,
    calculate_macd,
    is_price_above_ema
)

logger = logging.getLogger(__name__)


class MACDEMATrailingStopStrategy(Strategy):
    """
    MACD EMA Trailing Stop Strategy:
    - Buy when MACD > Signal AND price > 50 EMA (or just MACD > Signal if EMA unavailable)
    - Invest daily investment amount each day conditions are met
    - Sell all stocks when profit drops 10% from previous high
    - After selling, set the new high to the portfolio value at time of sale
    """
    
    @property
    def name(self) -> str:
        return "MACD EMA Trailing Stop Strategy"
    
    @property
    def description(self) -> str:
        return "Buy when MACD > Signal and price > 50 EMA, sell when profit drops 10% from previous high."
    
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
                'help': 'Amount to invest each trading day when buy conditions are met'
            },
            {
                'name': 'trailing_stop_percentage',
                'label': 'Trailing Stop Percentage (%)',
                'type': 'number',
                'default': 10.0,
                'required': False,
                'min': 0.1,
                'max': 50.0,
                'help': 'Percentage drop from high profit that triggers a sell (e.g., 10 means sell when profit drops 10% from high)'
            }
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate investment growth for MACD EMA Trailing Stop strategy.
        """
        ticker = params['ticker'].strip().upper()
        start_date = params['start_date']
        end_date = params['end_date']
        daily_investment = params['daily_investment']
        trailing_stop_pct = float(params.get('trailing_stop_percentage', 10.0))
        
        logger.debug(f"MACD EMA Trailing Stop Strategy: Starting calculation for {ticker}")
        logger.debug(f"Parameters: start_date={start_date}, end_date={end_date}, daily_investment=${daily_investment}, trailing_stop={trailing_stop_pct}%")
        
        # Calculate lookback period needed for MACD calculation AND 50-day EMA
        # We need at least 26 + 9 + buffer days before start_date for MACD
        # We also need at least 50 trading days before start_date for EMA calculation
        # Since 50 trading days ≈ 70-75 calendar days, we use 100 calendar days
        from datetime import timedelta
        macd_lookback_days = 26 + 9 + 60  # Extra buffer for safety (accounting for weekends/holidays)
        ema_lookback_calendar_days = 100  # Need ~50 trading days, which is ~100 calendar days
        lookback_days = max(macd_lookback_days, ema_lookback_calendar_days)
        fetch_start_date = start_date - timedelta(days=lookback_days)
        
        logger.debug(f"Fetching data from {fetch_start_date} to {end_date} (lookback: {lookback_days} days for MACD and EMA calculation)")
        
        # Ensure we have data in the database (with lookback for MACD and EMA calculation)
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
        if not all_prices_df.empty and len(all_prices_df) >= (26 + 9):
            macd_all_df = calculate_macd(all_prices_df['close'], 12, 26, 9)
            logger.debug(f"Pre-calculated MACD for {len(macd_all_df)} dates")
        else:
            logger.debug(f"Warning: Not enough data for MACD calculation. Got {len(all_prices_df) if not all_prices_df.empty else 0} days, need at least 35")
        
        # Initialize tracking variables
        stocks_owned = 0.0
        total_invested = 0.0
        cash = 0.0
        highest_profit = 0.0  # Track the highest profit seen so far
        last_known_high = 0.0  # Track the last known high after a sell
        
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
            
            # Check MACD condition: MACD > Signal
            macd_above_signal = False
            if macd_val is not None and signal_val is not None:
                macd_above_signal = macd_val > signal_val
            
            # Check EMA condition: price > 50 EMA
            # If EMA is not available (new stock), skip this condition and use only MACD condition
            price_above_ema, ema_50_value = is_price_above_ema(
                db_path, ticker, current_date, ema_period=50, 
                start_date=start_date, fetch_start_date=fetch_start_date
            )
            
            # Buy condition: MACD > Signal AND (price > 50 EMA OR EMA unavailable)
            can_buy = macd_above_signal and (price_above_ema or ema_50_value is None)
            
            # Calculate current portfolio value
            portfolio_value = cash + (stocks_owned * current_price)
            profit_loss = portfolio_value - total_invested
            
            # Update highest profit if we have a new high
            if profit_loss > highest_profit:
                highest_profit = profit_loss
                # If we've had a sell before, update last_known_high when we reach a new high
                if last_known_high > 0 and profit_loss > last_known_high:
                    last_known_high = profit_loss
            
            # Check sell conditions: sell if EITHER condition is met (whichever is earlier)
            # 1. Profit drops by trailing_stop_pct from previous known high
            # 2. Stock price goes below 50 EMA
            reference_high = last_known_high if last_known_high > 0 else highest_profit
            should_sell = False
            sell_reason = ""
            
            # Condition 1: Check trailing stop (profit protection)
            trailing_stop_triggered = False
            if reference_high > 0:
                # Calculate threshold (sell when profit drops by trailing_stop_pct% from high)
                # e.g., if trailing_stop_pct is 10%, threshold = reference_high * 0.9
                threshold = reference_high * (1 - trailing_stop_pct / 100.0)
                if profit_loss < threshold:
                    trailing_stop_triggered = True
                    should_sell = True
                    sell_reason = "trailing stop"
            
            # Condition 2: Check if price is below 50 EMA (only if EMA is available)
            ema_sell_triggered = False
            if ema_50_value is not None and current_price < ema_50_value:
                ema_sell_triggered = True
                should_sell = True
                if sell_reason:
                    sell_reason = f"{sell_reason} and price below 50 EMA"
                else:
                    sell_reason = "price below 50 EMA"
            
            # Execute sell if needed
            if should_sell and stocks_owned > 0:
                # Sell all shares and convert to cash
                shares_to_sell = stocks_owned
                portfolio_value_before_sell = cash + (stocks_owned * current_price)
                cash = portfolio_value_before_sell  # Convert all shares to cash
                stocks_owned = 0.0  # Sell all shares
                
                # Set the new last known high to the profit value at time of sale
                # This becomes the reference point for the next trailing stop
                last_known_high = portfolio_value_before_sell - total_invested
                # Don't reset highest_profit - keep tracking the actual highest profit we've seen
                
                # Format MACD values for logging
                macd_str = f"{macd_val:.4f}" if macd_val is not None else "N/A"
                signal_str = f"{signal_val:.4f}" if signal_val is not None else "N/A"
                histogram_str = f"{histogram_val:.4f}" if histogram_val is not None else "N/A"
                ema_str = f"${ema_50_value:.2f}" if ema_50_value is not None else "N/A"
                
                # Build detailed sell reason message
                sell_details = []
                if trailing_stop_triggered:
                    current_pct = (profit_loss / reference_high * 100) if reference_high > 0 else 0
                    sell_details.append(f"profit dropped to ${profit_loss:.2f} ({current_pct:.1f}% of high ${reference_high:.2f}, trailing stop: {trailing_stop_pct}%)")
                if ema_sell_triggered:
                    sell_details.append(f"price ${current_price:.2f} below 50 EMA ${ema_50_value:.2f}")
                
                sell_details_str = " | ".join(sell_details)
                logger.debug(
                    f"Sell triggered on {current_date} ({sell_reason}): Selling all shares. "
                    f"{sell_details_str}. "
                    f"Sold {shares_to_sell:.6f} shares @ ${current_price:.2f}, Cash: ${cash:.2f}. "
                    f"New last known high: ${last_known_high:.2f}. "
                    f"MACD Line={macd_str}, Signal Line={signal_str}, Histogram={histogram_str}, 50 EMA={ema_str}"
                )
            
            # Buy if conditions are met
            investment_amount = 0.0
            shares_bought = 0.0
            
            if can_buy:
                # Use cash first, then add daily investment
                total_available = cash + daily_investment
                if total_available > 0 and current_price > 0:
                    shares_bought = total_available / current_price
                    stocks_owned += shares_bought
                    total_invested += daily_investment
                    cash = 0.0  # All cash used for buying
                    investment_amount = total_available
                    
                    # Format MACD values for logging
                    macd_str = f"{macd_val:.4f}" if macd_val is not None else "N/A"
                    signal_str = f"{signal_val:.4f}" if signal_val is not None else "N/A"
                    histogram_str = f"{histogram_val:.4f}" if histogram_val is not None else "N/A"
                    ema_log_str = f", 50 EMA=${ema_50_value:.2f}" if ema_50_value is not None else ", 50 EMA=N/A (using MACD only)"
                    
                    logger.debug(
                        f"Date: {current_date}, Buying: {shares_bought:.6f} shares at ${current_price:.2f}, "
                        f"Investment: ${investment_amount:.2f} (cash=${cash:.2f} + daily=${daily_investment:.2f}). "
                        f"MACD Line={macd_str}, Signal Line={signal_str}, Histogram={histogram_str}{ema_log_str}"
                    )
            else:
                # Log why we're not buying
                if not macd_above_signal:
                    reason = "MACD <= Signal"
                elif ema_50_value is not None and not price_above_ema:
                    reason = f"Price ${current_price:.2f} <= 50 EMA ${ema_50_value:.2f}"
                else:
                    reason = "Unknown"
                
                # Format MACD values for logging
                macd_str = f"{macd_val:.4f}" if macd_val is not None else "N/A"
                signal_str = f"{signal_val:.4f}" if signal_val is not None else "N/A"
                histogram_str = f"{histogram_val:.4f}" if histogram_val is not None else "N/A"
                ema_log_str = f", 50 EMA=${ema_50_value:.2f}" if ema_50_value is not None else ", 50 EMA=N/A"
                
                logger.debug(
                    f"Date: {current_date}, Not buying ({reason}). "
                    f"Cash: ${cash:.2f}, Shares: {stocks_owned:.6f}, Portfolio Value: ${portfolio_value:.2f}, "
                    f"Profit: ${profit_loss:.2f}, High: ${reference_high:.2f}. "
                    f"MACD Line={macd_str}, Signal Line={signal_str}, Histogram={histogram_str}{ema_log_str}"
                )
            
            # Recalculate portfolio value after all transactions
            portfolio_value = cash + (stocks_owned * current_price)
            profit_loss = portfolio_value - total_invested
            
            # Determine current state for display
            if stocks_owned > 0:
                current_state = "Buying"
            else:
                current_state = "Waiting"
            
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

