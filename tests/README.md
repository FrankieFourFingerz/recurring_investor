# Testing Strategy for Investment Strategies

## Testing Approach

Since strategies depend on real stock market data that changes over time, we use a **mock data approach** with **property-based testing** to ensure correctness.

## Testing Strategy

### 1. **Mock Data Fixtures**
- Create fixed CSV files with known price data
- Use synthetic data that represents realistic scenarios
- Store in `tests/fixtures/` directory
- This ensures tests are deterministic and reproducible

### 2. **Property-Based Testing**
Instead of testing exact values, test **invariants** that must always be true:
- Total invested = sum of all daily investments
- Stocks bought = investment / price (for each day)
- Total stocks = cumulative sum of stocks bought
- Total Account = total stocks × current price
- Profit/Loss = Total Account - Principal Invested
- Principal Invested = cumulative sum of investments

### 3. **Output Format Testing**
- Verify DataFrame has required columns
- Check column types are correct
- Ensure dates are in correct format
- Validate no NaN values in critical columns

### 4. **Edge Cases**
- Empty data
- Single day
- Zero price (division by zero)
- Missing dates
- Invalid date ranges

## Test Structure

```
tests/
├── README.md (this file)
├── conftest.py (pytest fixtures)
├── fixtures/
│   ├── test_prices_3days.csv (simple 3-day price data)
│   └── test_prices_rising.csv (rising price trend)
├── test_simple_recurring.py
└── test_rsi_swing.py
```

## Running Tests

```bash
# Install pytest if not already installed
poetry add --dev pytest pytest-cov

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=strategies --cov-report=html

# Run specific test file
poetry run pytest tests/test_simple_recurring.py
```

## Expected Output Validation

For each strategy test, we validate:

1. **Mathematical Correctness**: All calculations follow the formulas
2. **Data Integrity**: No data loss or corruption
3. **Business Logic**: Strategy-specific rules are followed
4. **Output Format**: DataFrame structure matches specification
5. **Buy/Sell Conditions**: Strategy-specific entry and exit conditions are tested

### Testing Buy/Sell Conditions

Each strategy has specific business logic conditions:

**Simple Recurring Strategy:**
- Buy condition: Invest every trading day (no conditions)
- Sell condition: None (hold indefinitely)

**RSI Swing Strategy:**
- Buy condition: Select stock with lowest RSI from provided list
- Sell condition: When profit drops by 10% (or configured threshold) from peak, switch stocks

Tests verify:
- Buy conditions select the correct stocks
- Sell conditions trigger at the right time
- Stock switching occurs when conditions are met
- Peak profit tracking and reset logic

Since we can't predict exact market values, we focus on **relative correctness** rather than absolute values.

