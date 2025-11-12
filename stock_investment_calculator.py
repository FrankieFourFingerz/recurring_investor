#!/usr/bin/env python3
"""
Stock Investment Calculator

This script:
1. Checks local database for daily prices from provided start date for a stock ticker
2. Fetches daily OHLC data from the last missing date till current and updates the db
3. Calculates and tables the growth rate of an account if per-day investment was used
   to buy that stock every day till the end date
"""

import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import argparse
import sys


class StockInvestmentCalculator:
    def __init__(self, db_path: str = "stock_prices.db"):
        """Initialize the calculator with database path."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prices (
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_last_date_in_db(self, ticker: str) -> Optional[date]:
        """Get the last date for which we have data in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(date) FROM daily_prices WHERE ticker = ?
        ''', (ticker,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return datetime.strptime(result[0], '%Y-%m-%d').date()
        return None
    
    def fetch_and_update_prices(self, ticker: str, start_date: date, end_date: Optional[date] = None) -> int:
        """
        Fetch daily OHLC data from the last missing date till current and update the db.
        Returns the number of records inserted.
        """
        if end_date is None:
            end_date = date.today()
        
        # Get the last date we have in the database
        last_date = self.get_last_date_in_db(ticker)
        
        # If we already have data up to or past the end_date, no need to fetch
        if last_date and last_date >= end_date:
            print(f"Database already has data up to {last_date}. No new data needed.")
            return 0
        
        # Determine the fetch start date
        if last_date:
            # Start from the day after the last date we have
            fetch_start = last_date + timedelta(days=1)
        else:
            # No data exists, fetch from the provided start_date
            fetch_start = start_date
        
        # Make sure we don't fetch past the end_date
        if fetch_start > end_date:
            print(f"No new data to fetch. Last date in DB: {last_date}, End date: {end_date}")
            return 0
        
        # Fetch data from yfinance
        print(f"Fetching data for {ticker} from {fetch_start} to {end_date}...")
        stock = yf.Ticker(ticker)
        
        # yfinance expects datetime, not date
        fetch_start_dt = datetime.combine(fetch_start, datetime.min.time())
        end_date_dt = datetime.combine(end_date, datetime.min.time())
        
        hist = stock.history(start=fetch_start_dt, end=end_date_dt)
        
        if hist.empty:
            print(f"No data found for {ticker} in the specified date range.")
            return 0
        
        # Insert data into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        records_inserted = 0
        for idx, row in hist.iterrows():
            # Skip if we already have this date (shouldn't happen, but just in case)
            date_str = idx.date().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO daily_prices 
                (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker,
                date_str,
                float(row['Open']),
                float(row['High']),
                float(row['Low']),
                float(row['Close']),
                int(row['Volume']) if pd.notna(row['Volume']) else None
            ))
            records_inserted += 1
        
        conn.commit()
        conn.close()
        
        print(f"Inserted {records_inserted} records into database.")
        return records_inserted
    
    def get_daily_prices(self, ticker: str, start_date: date, end_date: Optional[date] = None) -> pd.DataFrame:
        """Get daily prices from the database for the specified date range."""
        if end_date is None:
            end_date = date.today()
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT date, open, high, low, close, volume
            FROM daily_prices
            WHERE ticker = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(ticker, start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        return df
    
    def calculate_investment_growth(
        self,
        ticker: str,
        start_date: date,
        daily_investment: float,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Calculate and table the growth rate of the account if per-day investment
        was used to buy that stock every day till the end date.
        
        Returns a DataFrame with columns:
        Date, Investment $, Stocks Bought, Stocks, Total Account, Profit/Loss
        """
        if end_date is None:
            end_date = date.today()
        
        # Ensure we have data in the database
        self.fetch_and_update_prices(ticker, start_date, end_date)
        
        # Get daily prices
        prices_df = self.get_daily_prices(ticker, start_date, end_date)
        
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
                'Profit/Loss': round(profit_loss, 2)
            })
        
        return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate investment growth for a stock with daily investments'
    )
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('start_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('daily_investment', type=float, help='Daily investment amount in dollars')
    parser.add_argument('--end_date', type=str, default=None, help='End date (YYYY-MM-DD). Defaults to today.')
    parser.add_argument('--db', type=str, default='stock_prices.db', help='Database file path (default: stock_prices.db)')
    parser.add_argument('--output', type=str, default=None, help='Output CSV file path (optional)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    except ValueError:
        print(f"Error: Invalid start_date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Error: Invalid end_date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize calculator
    calculator = StockInvestmentCalculator(db_path=args.db)
    
    # Calculate investment growth
    try:
        results_df = calculator.calculate_investment_growth(
            ticker=args.ticker,
            start_date=start_date,
            daily_investment=args.daily_investment,
            end_date=end_date
        )
        
        # Display results
        print("\n" + "="*80)
        print(f"Investment Growth Analysis for {args.ticker}")
        print(f"Start Date: {start_date}, End Date: {end_date or date.today()}")
        print(f"Daily Investment: ${args.daily_investment:.2f}")
        print("="*80 + "\n")
        
        # Set pandas display options for better formatting
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        print(results_df.to_string(index=False))
        
        # Save to CSV if requested
        if args.output:
            results_df.to_csv(args.output, index=False)
            print(f"\nResults saved to {args.output}")
        
        # Print summary
        if not results_df.empty:
            final_row = results_df.iloc[-1]
            print(f"\nSummary:")
            print(f"  Total Invested: ${final_row['Total Account'] - final_row['Profit/Loss']:.2f}")
            print(f"  Final Account Value: ${final_row['Total Account']:.2f}")
            print(f"  Total Profit/Loss: ${final_row['Profit/Loss']:.2f}")
            print(f"  Return Percentage: {(final_row['Profit/Loss'] / (final_row['Total Account'] - final_row['Profit/Loss']) * 100):.2f}%")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

