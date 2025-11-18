#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for strategy tests
"""

import pytest
import pandas as pd
import sqlite3
import os
from pathlib import Path
from datetime import date, timedelta

# Get the tests directory
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database for testing."""
    db_path = tmp_path / "test_stock_prices.db"
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
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
    """)
    conn.commit()
    conn.close()
    
    yield str(db_path)
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_prices_df():
    """Create a sample price DataFrame for testing."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
    # Remove weekends (keep only weekdays)
    dates = dates[dates.weekday < 5]
    
    # Create simple price data: $100, $102, $104, $103, $105
    prices = [100.0, 102.0, 104.0, 103.0, 105.0][:len(dates)]
    
    df = pd.DataFrame({
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': [1000000] * len(dates)
    }, index=dates)
    
    return df


@pytest.fixture
def populate_db(temp_db, sample_prices_df):
    """Populate the test database with sample price data."""
    conn = sqlite3.connect(temp_db)
    
    ticker = "TEST"
    for date_idx, row in sample_prices_df.iterrows():
        conn.execute("""
            INSERT OR REPLACE INTO daily_prices 
            (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            date_idx.date(),
            row['open'],
            row['high'],
            row['low'],
            row['close'],
            row['volume']
        ))
    
    conn.commit()
    conn.close()
    
    return temp_db, ticker


@pytest.fixture
def simple_recurring_params():
    """Default parameters for Simple Recurring Strategy tests."""
    return {
        'ticker': 'TEST',
        'start_date': date(2024, 1, 1),
        'end_date': date(2024, 1, 5),
        'daily_investment': 100.0
    }


@pytest.fixture
def mock_fetch_and_update(monkeypatch):
    """Mock fetch_and_update_prices to skip actual API calls in tests."""
    def mock_fetch(db_path, ticker, start_date, end_date):
        # Just return 0 (no records inserted) since we assume data is already in DB
        return 0
    
    # Patch in both investment_lib and strategies modules
    monkeypatch.setattr('investment_lib.fetch_and_update_prices', mock_fetch)
    monkeypatch.setattr('strategies.simple_recurring.simple_recurring.fetch_and_update_prices', mock_fetch)
    monkeypatch.setattr('strategies.rsi_swing.rsi_swing.fetch_and_update_prices', mock_fetch)
    monkeypatch.setattr('strategies.macd_swing.macd_swing.fetch_and_update_prices', mock_fetch)
    return mock_fetch

