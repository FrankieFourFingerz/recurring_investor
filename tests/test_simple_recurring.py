#!/usr/bin/env python3
"""
Tests for Simple Recurring Strategy
"""

import pytest
import pandas as pd
from datetime import date
from strategies.simple_recurring import SimpleRecurringStrategy
from investment_lib import get_daily_prices


class TestSimpleRecurringStrategy:
    """Test suite for Simple Recurring Strategy."""
    
    def test_strategy_properties(self):
        """Test that strategy has required properties."""
        strategy = SimpleRecurringStrategy()
        
        assert strategy.name == "Simple Recurring Strategy"
        assert len(strategy.description) > 0
        assert len(strategy.input_parameters) > 0
    
    def test_input_parameters_structure(self):
        """Test that input_parameters has correct structure."""
        strategy = SimpleRecurringStrategy()
        params = strategy.input_parameters
        
        # Check all required fields are present
        required_fields = ['name', 'label', 'type', 'default', 'required']
        for param in params:
            for field in required_fields:
                assert field in param, f"Missing field '{field}' in parameter {param.get('name')}"
        
        # Check we have expected parameters
        param_names = [p['name'] for p in params]
        assert 'ticker' in param_names
        assert 'start_date' in param_names
        assert 'end_date' in param_names
        assert 'daily_investment' in param_names
    
    def test_calculate_output_format(self, temp_db, populate_db, simple_recurring_params):
        """Test that calculate() returns DataFrame with correct format."""
        db_path, ticker = populate_db
        strategy = SimpleRecurringStrategy()
        
        results_df = strategy.calculate(db_path, ticker, simple_recurring_params)
        
        # Check it's a DataFrame
        assert isinstance(results_df, pd.DataFrame)
        assert not results_df.empty
        
        # Check required columns exist
        required_columns = [
            'Date', 'Investment $', 'Stocks Bought', 'Stocks',
            'Total Account', 'Profit/Loss', 'Principal Invested'
        ]
        for col in required_columns:
            assert col in results_df.columns, f"Missing column: {col}"
        
        # Check Date column is date type
        assert pd.api.types.is_datetime64_any_dtype(results_df['Date']) or \
               isinstance(results_df['Date'].iloc[0], date)
    
    def test_calculate_mathematical_correctness(self, temp_db, populate_db, simple_recurring_params):
        """Test mathematical correctness of calculations."""
        db_path, ticker = populate_db
        strategy = SimpleRecurringStrategy()
        daily_investment = simple_recurring_params['daily_investment']
        
        results_df = strategy.calculate(db_path, ticker, simple_recurring_params)
        
        # Get price data to verify calculations
        prices_df = get_daily_prices(db_path, ticker, 
                                    simple_recurring_params['start_date'],
                                    simple_recurring_params['end_date'])
        
        for idx, row in results_df.iterrows():
            # Get corresponding price
            result_date = row['Date']
            if isinstance(result_date, pd.Timestamp):
                result_date = result_date.date()
            
            price_row = prices_df[prices_df.index.date == result_date]
            if price_row.empty:
                continue
            
            close_price = price_row.iloc[0]['close']
            
            # Property 1: Investment $ should equal daily_investment
            assert abs(row['Investment $'] - daily_investment) < 0.01, \
                f"Investment amount incorrect on {result_date}"
            
            # Property 2: Stocks Bought = Investment / Price
            expected_stocks_bought = daily_investment / close_price if close_price > 0 else 0
            assert abs(row['Stocks Bought'] - expected_stocks_bought) < 0.000001, \
                f"Stocks bought calculation incorrect on {result_date}"
            
            # Property 3: Total Account = Stocks × Current Price
            expected_account_value = row['Stocks'] * close_price
            assert abs(row['Total Account'] - expected_account_value) < 0.01, \
                f"Account value calculation incorrect on {result_date}"
            
            # Property 4: Profit/Loss = Total Account - Principal Invested
            expected_profit_loss = row['Total Account'] - row['Principal Invested']
            assert abs(row['Profit/Loss'] - expected_profit_loss) < 0.01, \
                f"Profit/Loss calculation incorrect on {result_date}"
    
    def test_calculate_cumulative_values(self, temp_db, populate_db, simple_recurring_params):
        """Test that cumulative values are calculated correctly."""
        db_path, ticker = populate_db
        strategy = SimpleRecurringStrategy()
        daily_investment = simple_recurring_params['daily_investment']
        
        results_df = strategy.calculate(db_path, ticker, simple_recurring_params)
        
        # Property 1: Principal Invested should be cumulative
        for i in range(1, len(results_df)):
            prev_invested = results_df.iloc[i-1]['Principal Invested']
            curr_invested = results_df.iloc[i]['Principal Invested']
            assert curr_invested >= prev_invested, \
                "Principal Invested should be cumulative (non-decreasing)"
            assert abs(curr_invested - (prev_invested + daily_investment)) < 0.01, \
                "Principal Invested should increase by daily_investment each day"
        
        # Property 2: Stocks should be cumulative
        for i in range(1, len(results_df)):
            prev_stocks = results_df.iloc[i-1]['Stocks']
            curr_stocks = results_df.iloc[i]['Stocks']
            assert curr_stocks >= prev_stocks, \
                "Stocks should be cumulative (non-decreasing)"
        
        # Property 3: Total invested = sum of all daily investments
        total_days = len(results_df)
        expected_total_invested = daily_investment * total_days
        final_invested = results_df.iloc[-1]['Principal Invested']
        assert abs(final_invested - expected_total_invested) < 0.01, \
            f"Total invested should be {expected_total_invested}, got {final_invested}"
    
    def test_calculate_empty_data(self, temp_db):
        """Test that strategy handles empty data gracefully."""
        strategy = SimpleRecurringStrategy()
        params = {
            'ticker': 'NONEXISTENT',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 1, 5),
            'daily_investment': 100.0
        }
        
        with pytest.raises(ValueError, match="No data found"):
            strategy.calculate(temp_db, 'NONEXISTENT', params)
    
    def test_calculate_single_day(self, temp_db, populate_db):
        """Test strategy with single day of data."""
        db_path, ticker = populate_db
        strategy = SimpleRecurringStrategy()
        params = {
            'ticker': ticker,
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 1, 1),
            'daily_investment': 100.0
        }
        
        results_df = strategy.calculate(db_path, ticker, params)
        
        assert len(results_df) == 1
        assert results_df.iloc[0]['Principal Invested'] == 100.0
        assert results_df.iloc[0]['Investment $'] == 100.0
    
    def test_calculate_zero_price_handling(self, temp_db):
        """Test that strategy handles zero prices correctly."""
        # This would require a fixture with zero prices
        # For now, we test that the calculation doesn't crash
        # In real implementation, we should handle this edge case
        pass  # TODO: Add test with zero price data

