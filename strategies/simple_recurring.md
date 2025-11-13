# Simple Recurring Strategy

## Overview

The **Simple Recurring Strategy** is a straightforward dollar-cost averaging (DCA) approach that invests a fixed amount in a single stock every trading day. This strategy helps reduce the impact of market volatility by spreading purchases over time.

## How It Works

1. **Daily Investment**: On each trading day, the strategy invests a fixed dollar amount
2. **Fractional Shares**: Purchases fractional shares when the daily investment isn't a multiple of the stock price
3. **Cumulative Tracking**: Tracks total shares owned, total invested, and current portfolio value
4. **Profit Calculation**: Calculates profit/loss as the difference between current portfolio value and total invested

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | Date | Yes | 2024-01-01 | Start date for the investment period |
| `end_date` | Date | Yes | Today | End date for the investment period |
| `daily_investment` | Number | Yes | 100.0 | Amount to invest each trading day (minimum: $0.01) |

## Investment Logic

For each trading day:
1. Get the closing price of the stock
2. Calculate fractional shares: `shares_bought = daily_investment / close_price`
3. Add shares to cumulative total
4. Add daily investment to total invested
5. Calculate portfolio value: `total_shares * current_price`
6. Calculate profit/loss: `portfolio_value - total_invested`

## Output Columns

The strategy returns a DataFrame with the following columns:

- **Date**: Trading date
- **Investment $**: Daily investment amount
- **Stocks Bought**: Fractional shares purchased that day
- **Stocks**: Cumulative total shares owned
- **Total Account**: Current portfolio value (shares × current price)
- **Profit/Loss**: Profit or loss for that day
- **Principal Invested**: Cumulative total invested

## When to Use

This strategy is ideal for:
- **Long-term investors** who want to build a position gradually
- **Risk-averse investors** who prefer consistent, predictable investments
- **Beginners** who want a simple, easy-to-understand strategy
- **Single stock focus** when you have confidence in one particular company

## Advantages

✅ **Simple and predictable**: Easy to understand and implement  
✅ **Reduces timing risk**: Spreads purchases over time  
✅ **Automatic**: No need to time the market  
✅ **Fractional shares**: Works with any investment amount  

## Disadvantages

❌ **No diversification**: Invests in only one stock  
❌ **No exit strategy**: Continues investing regardless of performance  
❌ **No market timing**: Doesn't take advantage of market conditions  

## Example Usage

### Web Application
1. Select "Simple Recurring Strategy" from the dropdown
2. Enter stock ticker: `AAPL`
3. Set start date: `2024-01-01`
4. Set end date: `2024-12-31`
5. Set daily investment: `100`
6. Click "Calculate"

### Command Line
```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100 --end_date 2024-12-31 --strategy simple_recurring
```

## Example Scenario

**Input:**
- Stock: AAPL
- Start Date: January 1, 2024
- End Date: December 31, 2024
- Daily Investment: $100

**What Happens:**
- On each trading day, $100 is invested in AAPL
- Shares are purchased at the closing price
- Total shares accumulate over time
- Portfolio value fluctuates with stock price
- Profit/loss is calculated daily

**Result:**
- Total invested: $25,100 (251 trading days × $100)
- Final portfolio value: Depends on AAPL's performance
- Profit/Loss: Portfolio value - $25,100

## Notes

- Only **trading days** are included (weekends and holidays are skipped)
- Uses **closing price** for all purchases
- Supports **fractional shares** for any investment amount
- No transaction fees are considered in calculations

