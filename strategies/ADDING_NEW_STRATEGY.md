# Guide: Adding a New Investment Strategy

This guide explains how to create and integrate a new investment strategy into the system.

## Overview

The strategy system uses a plugin architecture where each strategy is a Python class that inherits from the base `Strategy` class. Strategies define their own input parameters, and the web application automatically generates UI fields based on these definitions.

## Required Interface

All strategies must inherit from `Strategy` and implement the following:

### 1. Properties

#### `name` (property)
- **Type**: `str`
- **Description**: Display name of the strategy (shown in UI dropdown)
- **Example**: `"My Custom Strategy"`

#### `description` (property)
- **Type**: `str`
- **Description**: Brief description of what the strategy does (shown as info in UI)
- **Example**: `"Invests based on moving average crossover signals"`

#### `input_parameters` (property)
- **Type**: `List[Dict[str, Any]]`
- **Description**: List of parameter definitions that define the strategy's inputs
- **Returns**: List of dictionaries, each defining one input parameter

### 2. Methods

#### `calculate(db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame`
- **Description**: Main calculation method that implements the strategy logic
- **Parameters**:
  - `db_path`: Path to the SQLite database file
  - `ticker`: Stock ticker (legacy parameter, typically ignored - use `params` instead)
  - `params`: Dictionary of input parameters (keys match `input_parameters` names)
- **Returns**: `pd.DataFrame` with required columns (see Output Format below)

## Step-by-Step Guide

### Step 1: Create Strategy File

Create a new Python file in the `strategies/` directory:

```python
# strategies/my_custom_strategy.py
#!/usr/bin/env python3
"""
My Custom Strategy: Description of what it does.
"""

from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import fetch_and_update_prices, get_daily_prices


class MyCustomStrategy(Strategy):
    """Your strategy description here."""
    
    @property
    def name(self) -> str:
        return "My Custom Strategy"
    
    @property
    def description(self) -> str:
        return "Brief description of what this strategy does"
    
    @property
    def input_parameters(self) -> List[Dict[str, Any]]:
        return [
            # Define your parameters here
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        # Implement your strategy logic here
        pass
```

### Step 2: Define Input Parameters

Each parameter in `input_parameters` is a dictionary with the following structure:

#### Required Fields
- `name`: Parameter key (used in `params` dictionary)
- `label`: Display label in the UI
- `type`: One of `'text'`, `'number'`, `'date'`, or `'select'`
- `default`: Default value
- `required`: `True` or `False` (whether validation requires a value)

#### Optional Fields
- `help`: Help text shown in UI tooltip
- `min`: Minimum value (for `'number'` type)
- `max`: Maximum value (for `'number'` type)
- `step`: Step size (for `'number'` type, default: 1.0)
- `options`: List of options (for `'select'` type)

#### Parameter Type Examples

**Text Parameter:**
```python
{
    'name': 'ticker',
    'label': 'Stock Ticker',
    'type': 'text',
    'default': 'AAPL',
    'required': True,
    'help': 'Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)'
}
```

**Number Parameter:**
```python
{
    'name': 'daily_investment',
    'label': 'Daily Investment ($)',
    'type': 'number',
    'default': 100.0,
    'required': True,
    'min': 0.01,
    'max': 10000.0,
    'step': 1.0,
    'help': 'Amount to invest each trading day'
}
```

**Date Parameter:**
```python
{
    'name': 'start_date',
    'label': 'Start Date',
    'type': 'date',
    'default': date(2024, 1, 1),
    'required': True,
    'help': 'Start date for the investment period'
}
```

**Select Parameter:**
```python
{
    'name': 'indicator_type',
    'label': 'Indicator Type',
    'type': 'select',
    'default': 'SMA',
    'required': True,
    'options': ['SMA', 'EMA', 'RSI'],
    'help': 'Type of technical indicator to use'
}
```

### Step 3: Implement the `calculate` Method

The `calculate` method should:

1. Extract parameters from `params` dictionary
2. Fetch/update stock price data using `investment_lib` functions
3. Implement your strategy logic
4. Return a DataFrame with the required columns

#### Available Library Functions

From `investment_lib`:
- `fetch_and_update_prices(db_path, ticker, start_date, end_date)`: Fetch and store price data
- `get_daily_prices(db_path, ticker, start_date, end_date)`: Get price DataFrame
- `calculate_rsi(prices_series, period=14)`: Calculate RSI indicator
- `get_best_rsi_stock(db_path, tickers, start_date, end_date, lookback_days=14)`: Find stock with lowest RSI

#### Output Format

The returned DataFrame **must** have these columns:

| Column Name | Type | Description |
|------------|------|-------------|
| `Date` | `date` | Trading date |
| `Investment $` | `float` | Amount invested on this date |
| `Stocks Bought` | `float` | Number of shares purchased |
| `Stocks` | `float` | Total shares owned (cumulative) |
| `Total Account` | `float` | Total account value (shares × current price) |
| `Profit/Loss` | `float` | Profit or loss (Total Account - Principal Invested) |
| `Principal Invested` | `float` | Cumulative amount invested |

**Optional Columns:**
- `Current Stock`: Current stock ticker (for multi-stock strategies)

#### Example Implementation

```python
def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate investment growth for my custom strategy.
    Note: The 'ticker' parameter is typically ignored - use params instead.
    """
    # Extract parameters
    my_ticker = params['ticker'].strip().upper()
    start_date = params['start_date']
    end_date = params['end_date']
    daily_investment = params['daily_investment']
    custom_param = params.get('custom_param', 10.0)  # Optional parameter
    
    # Fetch and get price data
    fetch_and_update_prices(db_path, my_ticker, start_date, end_date)
    prices_df = get_daily_prices(db_path, my_ticker, start_date, end_date)
    
    if prices_df.empty:
        raise ValueError(f"No price data found for {my_ticker} in the specified date range.")
    
    # Initialize tracking variables
    results = []
    total_shares = 0.0
    total_invested = 0.0
    
    # Iterate through each trading day
    for date_idx, row in prices_df.iterrows():
        current_date = date_idx.date()
        current_price = row['close']
        
        # Your strategy logic here
        # Example: Buy shares based on some condition
        shares_bought = daily_investment / current_price
        total_shares += shares_bought
        total_invested += daily_investment
        
        # Calculate account value
        account_value = total_shares * current_price
        profit_loss = account_value - total_invested
        
        # Append row
        results.append({
            'Date': current_date,
            'Investment $': daily_investment,
            'Stocks Bought': shares_bought,
            'Stocks': total_shares,
            'Total Account': account_value,
            'Profit/Loss': profit_loss,
            'Principal Invested': total_invested
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    return results_df
```

### Step 4: Register the Strategy

Add your strategy to `strategies/__init__.py`:

1. **Import your strategy class:**
```python
from strategies.my_custom_strategy import MyCustomStrategy
```

2. **Add to STRATEGIES registry:**
```python
STRATEGIES = {
    'simple_recurring': SimpleRecurringStrategy,
    'rsi_swing': RSISwingStrategy,
    'my_custom': MyCustomStrategy  # Add your strategy here
}
```

The key (`'my_custom'`) is the strategy ID used in the code. It should be lowercase with underscores.

### Step 5: Test Your Strategy

1. **Run the Streamlit app:**
```bash
poetry run streamlit run app.py
```

2. **Select your strategy** from the dropdown
3. **Fill in parameters** and click "Calculate"
4. **Verify the results** match your expectations

## Complete Example

Here's a complete example of a simple strategy:

```python
#!/usr/bin/env python3
"""
Example Strategy: Invests only on days when price is below 50-day moving average.
"""

from datetime import date
from typing import Dict, List, Any
import pandas as pd
from strategies.base import Strategy
from investment_lib import fetch_and_update_prices, get_daily_prices


class MovingAverageStrategy(Strategy):
    """Invests only when price is below moving average."""
    
    @property
    def name(self) -> str:
        return "Moving Average Strategy"
    
    @property
    def description(self) -> str:
        return "Invests only on days when stock price is below the moving average"
    
    @property
    def input_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'ticker',
                'label': 'Stock Ticker',
                'type': 'text',
                'default': 'AAPL',
                'required': True,
                'help': 'Stock ticker symbol'
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
                'help': 'Amount to invest when condition is met'
            },
            {
                'name': 'ma_period',
                'label': 'Moving Average Period',
                'type': 'number',
                'default': 50,
                'required': False,
                'min': 2,
                'max': 200,
                'help': 'Number of days for moving average calculation'
            }
        ]
    
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Calculate investment growth for moving average strategy."""
        ticker = params['ticker'].strip().upper()
        start_date = params['start_date']
        end_date = params['end_date']
        daily_investment = params['daily_investment']
        ma_period = int(params.get('ma_period', 50))
        
        # Fetch and get price data
        fetch_and_update_prices(db_path, ticker, start_date, end_date)
        prices_df = get_daily_prices(db_path, ticker, start_date, end_date)
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker} in the specified date range.")
        
        # Calculate moving average
        prices_df['ma'] = prices_df['close'].rolling(window=ma_period).mean()
        
        # Initialize tracking
        results = []
        total_shares = 0.0
        total_invested = 0.0
        
        # Iterate through trading days
        for date_idx, row in prices_df.iterrows():
            current_date = date_idx.date()
            current_price = row['close']
            ma_value = row['ma']
            
            # Strategy logic: invest only if price < moving average
            investment_amount = 0.0
            shares_bought = 0.0
            
            if pd.notna(ma_value) and current_price < ma_value:
                investment_amount = daily_investment
                shares_bought = investment_amount / current_price
                total_shares += shares_bought
                total_invested += investment_amount
            
            # Calculate account value
            account_value = total_shares * current_price
            profit_loss = account_value - total_invested
            
            results.append({
                'Date': current_date,
                'Investment $': investment_amount,
                'Stocks Bought': shares_bought,
                'Stocks': total_shares,
                'Total Account': account_value,
                'Profit/Loss': profit_loss,
                'Principal Invested': total_invested
            })
        
        return pd.DataFrame(results)
```

## Best Practices

1. **Parameter Validation**: Always validate and sanitize input parameters
   ```python
   ticker = params['ticker'].strip().upper()
   if not ticker:
       raise ValueError("Ticker cannot be empty")
   ```

2. **Error Handling**: Provide clear error messages
   ```python
   if prices_df.empty:
       raise ValueError(f"No price data found for {ticker} in the specified date range.")
   ```

3. **Use Library Functions**: Reuse functions from `investment_lib` instead of duplicating code

4. **Documentation**: Add docstrings explaining your strategy logic

5. **Handle Edge Cases**: Consider what happens with:
   - Empty data
   - Missing dates
   - Zero or negative prices
   - Insufficient data for indicators

6. **Performance**: For large date ranges, consider optimizing loops and calculations

7. **Testing**: Test with various date ranges and parameter combinations

## Output Column Requirements Summary

Your DataFrame **must** include these columns in this order (or at minimum, these columns must exist):

- `Date`: Trading date
- `Investment $`: Amount invested on this date
- `Stocks Bought`: Shares purchased on this date
- `Stocks`: Cumulative total shares owned
- `Total Account`: Current account value (shares × price)
- `Profit/Loss`: Profit or loss amount
- `Principal Invested`: Cumulative total invested

Optional columns (like `Current Stock`) can be added for multi-stock strategies.

## Troubleshooting

**Strategy doesn't appear in dropdown:**
- Check that you've imported and registered it in `strategies/__init__.py`
- Verify the class name matches the import

**Parameters not showing:**
- Check that `input_parameters` returns a list of dictionaries
- Verify all required fields are present in each parameter dict

**Calculation errors:**
- Ensure you're using `params` dictionary, not the `ticker` parameter
- Check that all required parameters are present in `params`
- Verify DataFrame columns match the required format

**Data not found errors:**
- Ensure you call `fetch_and_update_prices()` before `get_daily_prices()`
- Check that date ranges are valid and not in the future

## Next Steps

After creating your strategy:
1. Test it thoroughly with different parameters
2. Consider adding documentation (create a `my_strategy.md` file)
3. Update `strategies/README.md` to list your new strategy
4. Commit your changes to version control

For more examples, see:
- `strategies/simple_recurring.py` - Simple single-stock strategy
- `strategies/rsi_swing.py` - Complex multi-stock strategy with switching logic

