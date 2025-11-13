#!/usr/bin/env python3
"""
Investment Library - Reusable functions for stock data management
"""

import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple


def init_database(db_path: str = "stock_prices.db"):
    """Initialize the database with required tables."""
    conn = sqlite3.connect(db_path)
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


def get_last_date_in_db(db_path: str, ticker: str) -> Optional[date]:
    """Get the last date for which we have data in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT MAX(date) FROM daily_prices WHERE ticker = ?
    ''', (ticker,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return datetime.strptime(result[0], '%Y-%m-%d').date()
    return None


def check_data_coverage(db_path: str, ticker: str, start_date: date, end_date: date) -> Tuple[bool, Optional[date]]:
    """
    Check if we have data coverage for the full date range.
    Returns (has_full_coverage, first_missing_date)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the first and last dates we have for this ticker
    cursor.execute('''
        SELECT MIN(date), MAX(date) FROM daily_prices WHERE ticker = ?
    ''', (ticker,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return (False, start_date)
    
    db_start = datetime.strptime(result[0], '%Y-%m-%d').date()
    db_end = datetime.strptime(result[1], '%Y-%m-%d').date()
    
    # Check if we have coverage for the requested range
    if db_start <= start_date and db_end >= end_date:
        # We might have the range, but check for gaps
        # For now, if we have data that covers the range, assume it's good
        # The actual gap checking would require querying all dates
        return (True, None)
    elif db_end < start_date:
        # No data before start_date
        return (False, start_date)
    elif db_start > end_date:
        # No data at all in range
        return (False, start_date)
    elif db_end < end_date:
        # Missing data at the end
        return (False, db_end + timedelta(days=1))
    else:
        # Missing data at the beginning
        return (False, start_date)


def fetch_and_update_prices(db_path: str, ticker: str, start_date: date, end_date: Optional[date] = None) -> int:
    """
    Fetch daily OHLC data from the last missing date till current and update the db.
    Returns the number of records inserted.
    Raises ValueError if no data was fetched and validation fails.
    """
    if end_date is None:
        end_date = date.today()
    
    # Initialize database
    init_database(db_path)
    
    # Check if we already have full coverage
    has_coverage, first_missing = check_data_coverage(db_path, ticker, start_date, end_date)
    if has_coverage:
        print(f"Database already has full data coverage for {ticker} from {start_date} to {end_date}.")
        return 0
    
    # Determine the fetch start date - always fetch from start_date to ensure full coverage
    # This is safer than trying to be smart about gaps
    fetch_start = start_date
    
    # Fetch data from yfinance for the full range
    print(f"Fetching data for {ticker} from {fetch_start} to {end_date}...")
    stock = yf.Ticker(ticker)
    
    # Check if dates are in the future
    if start_date > date.today():
        error_msg = f"Start date ({start_date}) is in the future. Please use a date on or before today ({date.today()})."
        print(error_msg)
        raise ValueError(error_msg)
    
    if end_date > date.today():
        error_msg = f"End date ({end_date}) is in the future. Please use a date on or before today ({date.today()})."
        print(error_msg)
        raise ValueError(error_msg)
    
    # yfinance expects datetime, not date
    fetch_start_dt = datetime.combine(fetch_start, datetime.min.time())
    end_date_dt = datetime.combine(end_date, datetime.min.time())
    
    hist = stock.history(start=fetch_start_dt, end=end_date_dt)
    
    if hist.empty:
        # Provide more helpful error message
        if start_date > date.today() or end_date > date.today():
            error_msg = f"Date range includes future dates. Today is {date.today()}. Please use dates on or before today."
        else:
            error_msg = f"No data found for {ticker} in the specified date range ({start_date} to {end_date}). This may be because:\n" \
                       f"  - The stock was not trading during this period\n" \
                       f"  - The dates fall on weekends/holidays\n" \
                       f"  - The ticker symbol is incorrect\n" \
                       f"  - Today is {date.today()}, ensure your dates are not in the future"
        print(error_msg)
        raise ValueError(error_msg)
    
    # Validate that we got data
    if len(hist) == 0:
        error_msg = f"Failed to fetch data for {ticker}. The API returned an empty dataset."
        print(error_msg)
        raise ValueError(error_msg)
    
    # Check that we got data within the requested range
    hist_dates = [idx.date() for idx in hist.index]
    min_hist_date = min(hist_dates)
    max_hist_date = max(hist_dates)
    
    if min_hist_date > end_date or max_hist_date < start_date:
        error_msg = f"Fetched data for {ticker} is outside the requested range. Got {min_hist_date} to {max_hist_date}, requested {start_date} to {end_date}."
        print(error_msg)
        raise ValueError(error_msg)
    
    print(f"Successfully fetched {len(hist)} records from {min_hist_date} to {max_hist_date}")
    
    # Insert data into database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    records_inserted = 0
    for idx, row in hist.iterrows():
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
    
    # Final validation - check that we now have data for the requested range
    prices_df = get_daily_prices(db_path, ticker, start_date, end_date)
    if prices_df.empty:
        error_msg = f"After fetching, no data found for {ticker} in range {start_date} to {end_date}."
        print(error_msg)
        raise ValueError(error_msg)
    
    # Check if we have reasonable coverage (accounting for non-trading days)
    actual_dates = [idx.date() for idx in prices_df.index]
    actual_start = min(actual_dates)
    actual_end = max(actual_dates)
    
    # Allow up to 3 days difference to account for weekends/holidays at boundaries
    start_diff = (actual_start - start_date).days
    end_diff = (end_date - actual_end).days
    
    if start_diff > 3 or end_diff > 3:
        print(f"Note: Data coverage is {actual_start} to {actual_end}, requested {start_date} to {end_date}")
        print("This may be due to weekends/holidays at the date boundaries.")
    
    return records_inserted


def get_daily_prices(db_path: str, ticker: str, start_date: date, end_date: Optional[date] = None) -> pd.DataFrame:
    """Get daily prices from the database for the specified date range."""
    if end_date is None:
        end_date = date.today()
    
    conn = sqlite3.connect(db_path)
    
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


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI) for a price series.
    
    Args:
        prices: Series of closing prices
        period: RSI period (default 14)
        
    Returns:
        Series of RSI values
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def get_best_rsi_stock(db_path: str, tickers: list, start_date: date, end_date: date, lookback_days: int = 14) -> str:
    """
    Get the stock with the best (lowest) RSI value, indicating oversold condition (good entry).
    
    Args:
        db_path: Path to database
        tickers: List of ticker symbols to compare (ONLY these will be considered)
        start_date: Start date for calculation (not used, kept for compatibility)
        end_date: End date for calculation (the date we want RSI for)
        lookback_days: Number of days to look back for RSI calculation
        
    Returns:
        Ticker symbol with the lowest RSI (best entry point) from the provided tickers list
    """
    if not tickers:
        return None
    
    # Ensure tickers are uppercase and clean
    tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    
    if not tickers:
        return None
    
    best_ticker = None
    best_rsi = float('inf')
    
    # Calculate RSI for each ticker (ONLY from the provided list)
    for ticker in tickers:
        try:
            # Get price data with lookback for RSI calculation
            # We need enough data before end_date to calculate RSI
            lookback_start = end_date - timedelta(days=lookback_days + 30)  # Extra buffer for weekends/holidays
            prices_df = get_daily_prices(db_path, ticker, lookback_start, end_date)
            
            if prices_df.empty or len(prices_df) < lookback_days:
                continue
            
            # Calculate RSI
            rsi = calculate_rsi(prices_df['close'], period=lookback_days)
            
            # Get the most recent RSI value (for the end_date)
            if not rsi.empty:
                # Filter RSI to only include values up to end_date
                rsi_filtered = rsi[rsi.index.date <= end_date]
                if not rsi_filtered.empty:
                    latest_rsi = rsi_filtered.iloc[-1]
                    if pd.notna(latest_rsi) and latest_rsi < best_rsi:
                        best_rsi = latest_rsi
                        best_ticker = ticker
        except Exception as e:
            print(f"Warning: Could not calculate RSI for {ticker}: {e}")
            continue
    
    if best_ticker is None:
        # If no RSI could be calculated, return the first ticker from the provided list
        # This ensures we only return a ticker that was in the input list
        return tickers[0] if tickers else None
    
    # Double-check that the selected ticker is in the provided list (safety check)
    if best_ticker not in tickers:
        # This should never happen, but if it does, fallback to first ticker
        return tickers[0] if tickers else None
    
    return best_ticker

