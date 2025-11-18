# RSI Swing Strategy

## Overview

The **RSI Swing Strategy** is an active trading strategy that uses the Relative Strength Index (RSI) technical indicator to select stocks and automatically switches between stocks when profit drops from its peak. This strategy aims to enter positions when stocks are oversold (low RSI) and exit when profits decline significantly.

## How It Works

1. **Stock Selection**: Chooses the stock with the **lowest RSI** (most oversold) from a provided list
2. **Daily Investment**: Invests a fixed amount each trading day in the selected stock
3. **Profit Monitoring**: Tracks peak profit and monitors for declines
4. **Automatic Switching**: When profit drops by a threshold percentage from peak, sells all positions and switches to a new stock with better RSI

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | Date | Yes | 2024-01-01 | Start date for the investment period |
| `end_date` | Date | Yes | Today | End date for the investment period |
| `daily_investment` | Number | Yes | 100.0 | Amount to invest each trading day (minimum: $0.01) |
| `stock_list` | Text | Yes | AAPL,MSFT,GOOGL,NVDA | Comma-separated list of stock tickers to choose from |
| `rsi_period` | Number | No | 14 | Number of days for RSI calculation (range: 2-50) |
| `profit_drop_threshold` | Number | No | 10.0 | Percentage drop from peak profit to trigger switch (range: 1-50%) |

## RSI (Relative Strength Index) Explained

**RSI** is a momentum oscillator that measures the speed and magnitude of price changes. It ranges from 0 to 100:

- **RSI < 30**: Oversold condition (potential buy signal)
- **RSI 30-70**: Neutral zone
- **RSI > 70**: Overbought condition (potential sell signal)

This strategy selects stocks with the **lowest RSI** (most oversold), indicating they may be undervalued and due for a rebound.

### RSI Calculation

The RSI is calculated using the formula:
```
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss over the period
```

The default period is 14 days, meaning it looks at the last 14 trading days of price changes.

## Investment Logic

### Initial Selection
1. Calculate RSI for all stocks in the list
2. Select the stock with the **lowest RSI** (most oversold)
3. Begin investing daily in that stock

### Daily Operations
1. Calculate current portfolio value (stocks + cash)
2. Calculate current profit: `portfolio_value - total_invested`
3. Update peak profit if current profit is higher
4. Check if profit dropped by threshold: `current_profit < peak_profit × (1 - threshold)`
5. If switching:
   - Sell all positions (convert to cash)
   - Select new stock with best RSI
   - Use all cash + daily investment to buy new stock
6. If not switching:
   - Invest daily amount in current stock

### Switching Logic

The strategy switches stocks when:
- Peak profit > 0 (we've had positive returns)
- Current profit < Peak profit × (1 - threshold/100)

**Example:**
- Peak profit: $100
- Threshold: 10%
- Switch trigger: Current profit < $90 (10% drop from $100)

When switching:
1. All positions are sold (converted to cash)
2. New stock is selected based on RSI
3. All cash + daily investment is used to buy shares in new stock
4. Peak profit is reset to current profit (or 0 if negative) - starts fresh with new stock

**Important:** The peak profit resets when switching. This means:
- If you reach $10,000 profit with AAPL, then switch to MSFT at $8,500
- The strategy resets peak profit to $8,500 (or 0 if negative)
- Future switches will use $8,500 as the new reference point
- This allows the strategy to adapt to each new stock's performance independently

## Output Columns

The strategy returns a DataFrame with the following columns:

- **Date**: Trading date
- **Investment $**: Daily investment amount
- **Stocks Bought**: Fractional shares purchased that day
- **Stocks**: Shares owned in current stock
- **Total Account**: Current portfolio value (all stocks + cash)
- **Profit/Loss**: Profit or loss for that day
- **Principal Invested**: Cumulative total invested (new money only)
- **Current Stock**: Which stock is currently being invested in
- **Total Shares (All Stocks)**: Total shares across all stocks owned

## When to Use

This strategy is ideal for:
- **Active traders** who want to take advantage of market swings
- **Diversified approach** across multiple stocks
- **Risk management** with automatic profit protection
- **Technical analysis believers** who trust RSI indicators

## Advantages

✅ **Automatic risk management**: Exits positions when profits decline  
✅ **Diversification**: Spreads risk across multiple stocks  
✅ **Technical analysis**: Uses proven RSI indicator  
✅ **Entry optimization**: Enters at oversold (potentially undervalued) levels  
✅ **Profit protection**: Locks in gains by switching when profits drop  

## Disadvantages

❌ **More complex**: Requires understanding of RSI and technical analysis  
❌ **Transaction costs**: Frequent switching may incur costs (not modeled)  
❌ **Market timing risk**: RSI may not always predict reversals correctly  
❌ **Whipsaw risk**: May switch too frequently in volatile markets  

## Parameter Tuning

### RSI Period
- **Lower (7-10)**: More sensitive, reacts faster to price changes
- **Default (14)**: Balanced sensitivity
- **Higher (20-30)**: Less sensitive, smoother signals

### Profit Drop Threshold
- **Lower (5-7%)**: More aggressive, switches more frequently
- **Default (10%)**: Balanced approach
- **Higher (15-20%)**: Less frequent switching, allows more volatility

## Example Usage

### Web Application
1. Select "RSI Swing Strategy" from the dropdown
2. Enter stock list: `AAPL,MSFT,GOOGL,NVDA`
3. Set start date: `2024-01-01`
4. Set end date: `2024-12-31`
5. Set daily investment: `100`
6. Set RSI period: `14` (optional)
7. Set profit drop threshold: `10` (optional)
8. Click "Calculate"

### Command Line
```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100 \
  --end_date 2024-12-31 \
  --strategy rsi_swing \
  --params '{"stock_list": "AAPL,MSFT,GOOGL,NVDA", "rsi_period": 14, "profit_drop_threshold": 10}'
```

## Example Scenario

**Input:**
- Stock List: AAPL, MSFT, GOOGL, NVDA
- Start Date: January 1, 2024
- End Date: December 31, 2024
- Daily Investment: $100
- RSI Period: 14 days
- Profit Drop Threshold: 10%

**What Happens:**

**Day 1 (Jan 2):**
- Calculate RSI for all 4 stocks
- AAPL has RSI = 25 (lowest, most oversold)
- Select AAPL
- Invest $100 in AAPL

**Days 2-10:**
- Continue investing $100/day in AAPL
- Portfolio grows, profit increases
- Peak profit reaches $50

**Day 11:**
- AAPL price drops
- Current profit: $40 (down from $50 peak)
- Drop: 20% (exceeds 10% threshold)
- **SWITCH TRIGGERED**
- Sell all AAPL positions → get cash
- Calculate RSI for all stocks
- MSFT has RSI = 22 (lowest)
- Select MSFT
- Use all cash + $100 to buy MSFT shares

**Days 12+:**
- Continue investing in MSFT
- Monitor for next switch opportunity

## Technical Details

### RSI Calculation Method
- Uses **Wilder's Smoothing** method (exponential moving average)
- Calculates average gain and average loss over the period
- RSI = 100 - (100 / (1 + RS)) where RS = Avg Gain / Avg Loss

### Stock Selection Algorithm
1. For each stock in the list:
   - Fetch price data with lookback (RSI period + 30 days buffer)
   - Calculate RSI using closing prices
   - Get most recent RSI value
2. Select stock with lowest RSI (most oversold)
3. If RSI cannot be calculated for any stock, fallback to first stock in list

### Cash Management
- When switching: All portfolio value becomes cash
- Cash + daily investment is used to buy new stock
- No cash is held idle (all converted to shares)

## Notes

- **RSI Lookback**: Requires sufficient historical data (RSI period + buffer days)
- **Trading Days Only**: Only invests on trading days (skips weekends/holidays)
- **Fractional Shares**: Supports fractional share purchases
- **No Transaction Fees**: Calculations don't include trading fees
- **Price Source**: Uses closing prices for all calculations
- **Multiple Stocks**: Can handle any number of stocks in the list

## Strategy Performance Considerations

The strategy's performance depends on:
1. **Stock Selection Quality**: Better stocks in the list = better results
2. **RSI Accuracy**: RSI's ability to identify oversold conditions
3. **Threshold Sensitivity**: Balance between protection and whipsaw
4. **Market Conditions**: Works best in trending or mean-reverting markets

## Risk Warnings

⚠️ **Past performance does not guarantee future results**  
⚠️ **RSI is a lagging indicator** - may miss rapid price movements  
⚠️ **Frequent switching** may result in higher transaction costs in real trading  
⚠️ **Strategy assumes** you can always find a stock with good RSI entry point  

