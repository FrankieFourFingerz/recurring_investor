# MACD Swing Strategy

## Overview

The **MACD Swing Strategy** is an active trading strategy that uses MACD (Moving Average Convergence Divergence) technical indicators to time entry and exit points. It buys a stock when MACD crosses above the signal line (bullish signal) and stops buying when MACD crosses below the signal line (bearish signal). This strategy aims to invest during bullish momentum periods and avoid investing during bearish momentum periods.

## How It Works

1. **Wait for MACD Crossover Up**: Starts in waiting mode, monitoring for MACD to cross above Signal
2. **Start Buying**: When MACD crosses up, begins investing daily
3. **Continue Buying**: Keeps investing daily while MACD remains above Signal
4. **Stop Buying**: When MACD crosses down (below Signal), stops investing and enters waiting mode
5. **Cycle Repeat**: Waits for next MACD crossover up and repeats the cycle

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ticker` | Text | Yes | AAPL | Stock ticker symbol (e.g., AAPL, MSFT, GOOGL) |
| `start_date` | Date | Yes | 2024-01-01 | Start date for the investment period |
| `end_date` | Date | Yes | Today | End date for the investment period |
| `daily_investment` | Number | Yes | 100.0 | Amount to invest each trading day when in buying mode (minimum: $0.01) |
| `macd_fast` | Number | No | 12 | Fast EMA period for MACD calculation (range: 2-50) |
| `macd_slow` | Number | No | 26 | Slow EMA period for MACD calculation (range: 2-100) |
| `macd_signal` | Number | No | 9 | Signal line EMA period for MACD calculation (range: 2-50) |

## MACD (Moving Average Convergence Divergence) Explained

**MACD** is a trend-following momentum indicator that shows the relationship between two exponential moving averages (EMAs) of a stock's price.

### MACD Components

1. **MACD Line**: The difference between the 12-period EMA and 26-period EMA
   - `MACD Line = EMA(12) - EMA(26)`

2. **Signal Line**: A 9-period EMA of the MACD line
   - `Signal Line = EMA(9) of MACD Line`

3. **Histogram**: The difference between MACD and Signal lines
   - `Histogram = MACD Line - Signal Line`

### MACD Crossover Signals

**Bullish Crossover (Buy Signal)**:
- The MACD line crosses **above** the signal line
- Indicates increasing upward momentum
- Signals potential uptrend or reversal from downtrend
- **Triggers buying mode**

**Bearish Crossdown (Stop Signal)**:
- The MACD line crosses **below** the signal line
- Indicates decreasing momentum or potential downtrend
- Signals potential reversal from uptrend
- **Triggers waiting mode (stops buying)**

**Example - Bullish Crossover:**
- Previous day: MACD = 0.5, Signal = 0.6 (MACD below Signal)
- Current day: MACD = 0.7, Signal = 0.65 (MACD above Signal)
- **Crossover detected** → Start buying

**Example - Bearish Crossdown:**
- Previous day: MACD = 0.7, Signal = 0.65 (MACD above Signal)
- Current day: MACD = 0.6, Signal = 0.68 (MACD below Signal)
- **Crossdown detected** → Stop buying

## Investment Logic

### Initial State

The strategy checks the MACD state at the start date:
- **If MACD is above Signal** at start date: Begins buying immediately
- **If MACD is below Signal** at start date: Enters "Waiting for MACD Crossover Up" mode
- Monitors MACD indicator for bullish crossover signal
- Once crossover is detected (or if already above at start), enters buying mode

### Buying Mode

When MACD crosses above Signal (bullish crossover):
1. **Start Buying**: Strategy enters "Buying" mode
2. **Daily Investment**: Invests the specified daily amount each trading day
3. **Cash Management**: Uses any available cash, then adds daily investment
4. **Continue Buying**: Keeps buying daily while MACD remains above Signal
5. **Monitor Crossdown**: Checks each day for MACD crossdown (bearish signal)

### Stop Buying Condition

The strategy stops buying when:
- Currently in buying mode
- MACD crosses below Signal (bearish crossdown)

When crossdown is detected:
1. Strategy enters "Waiting for MACD Crossover Up" mode
2. No daily investment occurs
3. Existing positions are held (not sold)
4. Portfolio value continues to fluctuate with stock price

### Waiting Mode

While waiting for MACD crossover up:
1. **No Buying**: Daily investment is paused
2. **Hold Positions**: Existing stock positions are held (not sold)
3. **MACD Monitoring**: Checks each day for bullish MACD crossover
4. **Crossover Detection**: When MACD crosses above Signal, resume buying

### Resume Buying

When MACD crossover up is detected:
1. Strategy returns to "Buying" mode
2. Uses any available cash + daily investment to buy shares
3. Daily investment resumes

## Output Columns

The strategy returns a DataFrame with the following columns:

- **Date**: Trading date
- **Investment $**: Amount invested that day (0 when in waiting mode)
- **Stocks Bought**: Fractional shares purchased that day
- **Stocks**: Cumulative total shares owned
- **Total Account**: Current portfolio value (cash + stocks × current price)
- **Profit/Loss**: Profit or loss for that day
- **Principal Invested**: Cumulative total invested (only increases during buying mode)
- **Current State**: Either "Buying" or "Waiting for MACD Crossover"

## Strategy Flow Example

```
Scenario A: MACD already above Signal at start
Day 1:     Start date - MACD > Signal
           - Begin "Buying" mode immediately
           - Start investing $100/day

Scenario B: MACD below Signal at start
Day 1-5:   Waiting mode
           - No investments
           - Monitor MACD
           - MACD below Signal
           
Day 6:     MACD crosses above Signal (bullish crossover)
           - Enter "Buying" mode
           - Start investing $100/day
           
Day 7-20:  Buying mode
           - Invest $100/day
           - MACD remains above Signal
           - Account grows
           
Day 21:    MACD crosses below Signal (bearish crossdown)
           - Enter "Waiting" mode
           - Stop daily investments
           - Hold existing positions
           
Day 22-30: Waiting mode
           - No new investments
           - Existing positions fluctuate with price
           - Monitor MACD
           
Day 31:    MACD crosses above Signal again
           - Resume "Buying" mode
           - Start investing $100/day again
           
Day 32+:   Continue buying daily...
```

## When to Use

This strategy is ideal for:
- **Active traders** who want to protect profits during downturns
- **Momentum investors** who believe in technical indicators
- **Risk management focused** investors who want automatic stop-loss behavior
- **Single stock focus** with technical analysis

## Advantages

✅ **Technical Entry**: Uses MACD crossover to identify potential uptrends
✅ **Automatic Exit**: Stops buying when momentum turns bearish
✅ **Trend Following**: Invests during bullish momentum, avoids investing during bearish momentum
✅ **Position Preservation**: Holds positions during waiting periods (doesn't sell)

## Limitations

⚠️ **False Signals**: MACD crossovers can produce false signals in sideways markets
⚠️ **Whipsaw Risk**: May start/stop buying frequently in choppy markets
⚠️ **Timing Risk**: May miss some gains if crossover occurs after significant price movement
⚠️ **Single Stock**: Focuses on one stock, lacks diversification
⚠️ **No Selling**: Positions are held during waiting periods, so losses can continue

## Tips for Best Results

1. **Choose Trending Stocks**: Works best with stocks that have clear, sustained trends
2. **MACD Periods**: Standard periods (12, 26, 9) work well for most stocks, but can be adjusted:
   - Faster periods (8, 17, 9) for more sensitive signals
   - Slower periods (19, 39, 9) for fewer, more reliable signals
3. **Timeframe**: Works better over longer periods where trends are more reliable
4. **Market Conditions**: Performs best in trending markets rather than choppy/sideways markets
5. **Combine with Other Analysis**: Consider using with other indicators for confirmation

## Technical Details

### MACD Calculation

The MACD is calculated using exponential moving averages (EMAs):

1. **Fast EMA**: 12-period EMA of closing prices
2. **Slow EMA**: 26-period EMA of closing prices
3. **MACD Line**: Fast EMA - Slow EMA
4. **Signal Line**: 9-period EMA of MACD Line

### Crossover Detection

**Bullish Crossover (Buy Signal)**:
- Previous day: `MACD[t-1] <= Signal[t-1]`
- Current day: `MACD[t] > Signal[t]`
- Indicates MACD line crossed above signal line → Start buying

**Bearish Crossdown (Stop Signal)**:
- Previous day: `MACD[t-1] >= Signal[t-1]`
- Current day: `MACD[t] < Signal[t]`
- Indicates MACD line crossed below signal line → Stop buying

## Comparison with Other Strategies

| Feature | Simple Recurring | RSI Swing | MACD Swing |
|---------|-----------------|-----------|------------|
| **Entry Signal** | None (always buy) | Lowest RSI | MACD Crossover |
| **Exit Signal** | None (hold) | Profit drop | Account drop from peak |
| **Re-entry** | N/A | Automatic (RSI) | MACD Crossover |
| **Stock Selection** | Single stock | Multiple stocks | Single stock |
| **Complexity** | Low | Medium | Medium |

## Example Scenarios

### Scenario 1: Strong Trending Market

- Days 1-5: Waiting mode, MACD below Signal
- Day 6: MACD crosses above Signal
- **Action**: Start buying $100/day
- Days 7-25: Buying mode, MACD stays above Signal
- **Result**: Accumulated significant position during uptrend
- Day 26: MACD crosses below Signal
- **Action**: Stop buying, hold positions
- Days 27-30: Waiting mode, positions fluctuate with price
- Day 31: MACD crosses above Signal again
- **Action**: Resume buying

### Scenario 2: Choppy/Sideways Market

- Days 1-5: Waiting mode
- Day 6: MACD crossover (false signal)
- **Action**: Start buying
- Day 8: MACD crossdown (quick reversal)
- **Action**: Stop buying
- Day 10: MACD crossover again
- **Risk**: Frequent start/stop in choppy markets may reduce effectiveness

## Notes

- The strategy requires sufficient historical data for MACD calculation (at least 26+ days)
- MACD crossovers are more reliable in trending markets
- Positions are **held** during waiting periods (not sold), so account value continues to change
- Principal Invested only increases during buying mode, not during waiting periods
- The strategy checks MACD state at start date: if MACD > Signal, starts buying immediately; otherwise waits for crossover
- Multiple buy/sell cycles can occur within the investment period

