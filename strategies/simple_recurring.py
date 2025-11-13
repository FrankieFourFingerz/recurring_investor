#!/usr/bin/env python3
"""
Simple Recurring Strategy: Invest a fixed amount every trading day.
"""

from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import fetch_and_update_prices, get_daily_prices


class SimpleRecurringStrategy(Strategy):
    """
    Simple Recurring Strategy: Invest a fixed amount every trading day.
    """
    
    @property
    def name(self) -> str:
        return "Simple Recurring Strategy"
    
    @property
    def description(self) -> str:
        return "Invest a fixed amount every trading day (dollar-cost averaging)"
    
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
                'help': 'Amount to invest each trading day'
            }
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate investment growth for simple recurring strategy.
        Note: The 'ticker' parameter is ignored - we use params['ticker'] instead.
        """
        ticker = params['ticker'].strip().upper()
        start_date = params['start_date']
        end_date = params['end_date']
        daily_investment = params['daily_investment']
        
        # Ensure we have data in the database
        fetch_and_update_prices(db_path, ticker, start_date, end_date)
        
        # Get daily prices
        prices_df = get_daily_prices(db_path, ticker, start_date, end_date)
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker} in the specified date range.")
        
        # Calculate investment growth
        results = []
        total_stocks = 0.0
        total_invested = 0.0
        
        for date_idx, row in prices_df.iterrows():
            # Use close price for buying
            close_price = row['close']
            
            # Calculate fractional stocks bought
            stocks_bought = daily_investment / close_price if close_price > 0 else 0
            
            # Update totals
            total_stocks += stocks_bought
            total_invested += daily_investment
            
            # Calculate current account value
            current_account_value = total_stocks * close_price
            
            # Calculate profit/loss
            profit_loss = current_account_value - total_invested
            
            results.append({
                'Date': date_idx.date(),
                'Investment $': round(daily_investment, 2),
                'Stocks Bought': round(stocks_bought, 6),
                'Stocks': round(total_stocks, 6),
                'Total Account': round(current_account_value, 2),
                'Profit/Loss': round(profit_loss, 2),
                'Principal Invested': round(total_invested, 2)
            })
        
        return pd.DataFrame(results)
