#!/usr/bin/env python3
"""
RSI Swing Strategy: Invests in stocks with best RSI values and switches when profit drops 10% from peak.
"""

from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import (
    fetch_and_update_prices, 
    get_daily_prices, 
    get_best_rsi_stock,
    calculate_rsi
)


class RSISwingStrategy(Strategy):
    """
    RSI Swing Strategy: 
    - Picks stock with best (lowest) RSI value from a list
    - Invests daily in that stock
    - Monitors profit and switches to new stock when profit drops 10% from peak
    """
    
    @property
    def name(self) -> str:
        return "RSI Swing Strategy"
    
    @property
    def description(self) -> str:
        return "Invests in stocks with best RSI entry points. Switches stocks when profit drops 10% from peak."
    
    @property
    def input_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'stock_list',
                'label': 'Stock List (comma-separated)',
                'type': 'text',
                'default': 'AAPL,MSFT,GOOGL,NVDA',
                'required': True,
                'help': 'Comma-separated list of stock tickers to choose from'
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
                'help': 'Amount to invest each trading day'
            },

            {
                'name': 'rsi_period',
                'label': 'RSI Period',
                'type': 'number',
                'default': 14,
                'required': False,
                'min': 2,
                'max': 50,
                'help': 'Number of days for RSI calculation (default: 14)'
            },
            {
                'name': 'profit_drop_threshold',
                'label': 'Profit Drop Threshold (%)',
                'type': 'number',
                'default': 10.0,
                'required': False,
                'min': 1.0,
                'max': 50.0,
                'help': 'Percentage drop from peak profit to trigger stock switch (default: 10%)'
            }
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate investment growth for RSI swing strategy.
        Note: The 'ticker' parameter is ignored - we use stock_list instead.
        """
        start_date = params['start_date']
        end_date = params['end_date']
        daily_investment = params['daily_investment']
        stock_list_str = params['stock_list']
        rsi_period = int(params.get('rsi_period', 14))
        profit_drop_threshold = params.get('profit_drop_threshold', 10.0) / 100.0
        
        # Parse stock list - ensure we only use what the user provided
        if not stock_list_str or not isinstance(stock_list_str, str):
            raise ValueError(f"Invalid stock_list parameter: {stock_list_str}")
        
        stock_list = [s.strip().upper() for s in stock_list_str.split(',') if s.strip()]
        if not stock_list:
            raise ValueError("Stock list cannot be empty")
        
        # Log the parsed stock list for debugging (remove spaces, ensure clean)
        print(f"Using stock list: {stock_list}")
        
        # Ensure we have data for all stocks (ONLY from the provided list)
        for stock in stock_list:
            fetch_and_update_prices(db_path, stock, start_date, end_date)
        
        # Get all trading dates (ONLY from stocks in the provided list)
        all_dates = []
        for stock in stock_list:
            # Double-check stock is in our list
            if stock not in stock_list:
                continue
            prices_df = get_daily_prices(db_path, stock, start_date, end_date)
            if not prices_df.empty:
                all_dates.extend([idx.date() for idx in prices_df.index])
        
        if not all_dates:
            raise ValueError(f"No price data found for any stock in the list: {stock_list}")
        
        # Get unique sorted dates
        unique_dates = sorted(set(all_dates))
        
        # Final validation: ensure stock_list hasn't been modified
        if set(stock_list) != set([s.strip().upper() for s in stock_list_str.split(',') if s.strip()]):
            raise ValueError(f"Stock list was modified! Original: {stock_list_str}, Current: {stock_list}")
        
        # Initialize tracking variables
        current_stock = None
        stocks_owned = {}  # {ticker: number of shares}
        total_invested_per_stock = {}  # {ticker: total invested}
        peak_profit = 0.0
        total_invested_all = 0.0
        cash = 0.0  # Cash from selling positions
        results = []
        
        for trade_date in unique_dates:
            # Check if we need to switch stocks
            if current_stock is None:
                # Initial stock selection (ONLY from the provided stock_list)
                # Make a copy to ensure we don't accidentally modify the original
                available_stocks = list(stock_list)
                current_stock = get_best_rsi_stock(db_path, available_stocks, trade_date, trade_date, rsi_period)
                if current_stock is None or current_stock not in stock_list:
                    # Fallback to first stock in the provided list
                    current_stock = stock_list[0] if stock_list else None
                    if current_stock is None:
                        raise ValueError(f"No valid stocks in the provided stock list: {stock_list}")
                # Validate one more time
                if current_stock not in stock_list:
                    raise ValueError(f"Selected stock {current_stock} is not in provided list: {stock_list}")
                stocks_owned[current_stock] = 0.0
                total_invested_per_stock[current_stock] = 0.0
                peak_profit = 0.0
            
            # Get current price for the stock we're investing in
            prices_df = get_daily_prices(db_path, current_stock, trade_date, trade_date)
            if prices_df.empty:
                continue
            
            current_price = prices_df.iloc[0]['close']
            
            # Calculate current portfolio value (stocks + cash)
            portfolio_value = cash
            for stock, shares in stocks_owned.items():
                if shares > 0:
                    stock_prices = get_daily_prices(db_path, stock, trade_date, trade_date)
                    if not stock_prices.empty:
                        stock_price = stock_prices.iloc[0]['close']
                        portfolio_value += shares * stock_price
            
            # Calculate current profit
            current_profit = portfolio_value - total_invested_all
            
            # Update peak profit
            if current_profit > peak_profit:
                peak_profit = current_profit
            
            # Check if we need to switch stocks (profit dropped 10% from peak)
            should_switch = False
            if peak_profit > 0 and current_profit < peak_profit * (1 - profit_drop_threshold):
                should_switch = True
            
            # If switching, "sell" all positions and pick new stock
            if should_switch:
                # Sell all positions - convert to cash
                cash = portfolio_value  # All portfolio value becomes cash
                stocks_owned = {}  # Clear all positions
                total_invested_per_stock = {}  # Reset per-stock tracking
                
                # Pick new stock with best RSI (ONLY from the provided stock_list)
                # Make a copy to ensure we don't accidentally modify the original
                available_stocks = list(stock_list)
                current_stock = get_best_rsi_stock(db_path, available_stocks, trade_date, trade_date, rsi_period)
                if current_stock is None or current_stock not in stock_list:
                    # Fallback to first stock in the provided list
                    current_stock = stock_list[0] if stock_list else None
                    if current_stock is None:
                        raise ValueError(f"No valid stocks in the provided stock list: {stock_list}")
                # Validate one more time
                if current_stock not in stock_list:
                    raise ValueError(f"Selected stock {current_stock} is not in provided list: {stock_list}")
                
                # Reset peak profit after switch (use current profit as new baseline)
                peak_profit = max(0.0, current_profit)
                
                # Initialize new stock
                stocks_owned[current_stock] = 0.0
                total_invested_per_stock[current_stock] = 0.0
                
                # Use cash + daily investment to buy shares in new stock
                # Get price for new stock
                new_stock_prices = get_daily_prices(db_path, current_stock, trade_date, trade_date)
                if not new_stock_prices.empty:
                    new_stock_price = new_stock_prices.iloc[0]['close']
                    # Use all available cash + daily investment to buy shares
                    total_to_invest = cash + daily_investment
                    shares_from_cash = cash / new_stock_price if new_stock_price > 0 else 0
                    shares_from_daily = daily_investment / new_stock_price if new_stock_price > 0 else 0
                    total_shares = shares_from_cash + shares_from_daily
                    
                    stocks_owned[current_stock] = total_shares
                    total_invested_per_stock[current_stock] = daily_investment  # Only track new investment
                    total_invested_all += daily_investment
                    cash = 0.0  # All cash used
                    
                    # Skip the normal investment step since we already invested
                    # Recalculate portfolio value
                    portfolio_value = 0.0
                    for stock, shares in stocks_owned.items():
                        if shares > 0:
                            stock_prices = get_daily_prices(db_path, stock, trade_date, trade_date)
                            if not stock_prices.empty:
                                stock_price = stock_prices.iloc[0]['close']
                                portfolio_value += shares * stock_price
                    
                    final_profit = portfolio_value - total_invested_all
                    
                    # Validate that current_stock is in the provided stock_list (safety check)
                    if current_stock not in stock_list:
                        raise ValueError(f"Invalid stock selected: {current_stock}. Must be one of: {stock_list}")
                    
                    results.append({
                        'Date': trade_date,
                        'Investment $': round(daily_investment, 2),
                        'Stocks Bought': round(total_shares, 6),
                        'Stocks': round(stocks_owned[current_stock], 6),
                        'Total Account': round(portfolio_value, 2),
                        'Profit/Loss': round(final_profit, 2),
                        'Principal Invested': round(total_invested_all, 2),
                        'Current Stock': current_stock,
                        'Total Shares (All Stocks)': round(sum(stocks_owned.values()), 6)
                    })
                    continue  # Skip normal investment logic
            
            # Invest in current stock (normal case, no switching)
            if current_stock not in stocks_owned:
                stocks_owned[current_stock] = 0.0
                total_invested_per_stock[current_stock] = 0.0
            
            # Buy shares with daily investment
            shares_bought = daily_investment / current_price if current_price > 0 else 0
            stocks_owned[current_stock] += shares_bought
            total_invested_per_stock[current_stock] += daily_investment
            total_invested_all += daily_investment
            
            # Recalculate portfolio value after purchase (stocks + cash)
            portfolio_value = cash
            for stock, shares in stocks_owned.items():
                if shares > 0:  # Only calculate for stocks we actually own
                    stock_prices = get_daily_prices(db_path, stock, trade_date, trade_date)
                    if not stock_prices.empty:
                        stock_price = stock_prices.iloc[0]['close']
                        portfolio_value += shares * stock_price
            
            # Calculate final profit
            final_profit = portfolio_value - total_invested_all
            
            # Validate that current_stock is in the provided stock_list (safety check)
            if current_stock not in stock_list:
                raise ValueError(f"Invalid stock selected: {current_stock}. Must be one of: {stock_list}")
            
            # Record the day's activity
            results.append({
                'Date': trade_date,
                'Investment $': round(daily_investment, 2),
                'Stocks Bought': round(shares_bought, 6),
                'Stocks': round(stocks_owned[current_stock], 6),
                'Total Account': round(portfolio_value, 2),
                'Profit/Loss': round(final_profit, 2),
                'Principal Invested': round(total_invested_all, 2),
                'Current Stock': current_stock,
                'Total Shares (All Stocks)': round(sum(stocks_owned.values()), 6)
            })
        
        return pd.DataFrame(results)

