# MACD EMA Trailing Stop Strategy

## Overview

The MACD EMA Trailing Stop Strategy combines MACD (Moving Average Convergence Divergence) and EMA (Exponential Moving Average) indicators with a profit protection mechanism. It buys when both technical conditions are met and sells when profit drops below a threshold to protect gains.

## Strategy Rules

### Buy Rules (All Must Be Satisfied)

1. **Stock price is above 50 EMA**: The current stock price must be above the 50-period Exponential Moving Average.
   - **Exception**: If the stock is new and 50 EMA is not available yet (insufficient historical data), this rule is skipped and only rule 2 is used for buying.

2. **MACD value is above signal value**: The MACD line must be above the Signal line, indicating bullish momentum.

3. **Daily investment**: Each day the above conditions are true, invest the daily investment amount provided in the input parameters.

### Sell Rules

1. **Profit protection**: Sell all stocks if the overall profit falls below 10% of the previous known high.
   - The "previous known high" is the highest profit achieved since the last sell (or since the start if no sell has occurred yet).

2. **Update high after sell**: Once sold, set the latest high profit to the portfolio value (profit) it was on the day it was sold. This becomes the new "last known high" until a new high in profit happens.

## Input Parameters

1. **Stock ticker**: The stock symbol to invest in (e.g., AAPL, MSFT, GOOGL)
2. **Start date**: The date to begin the investment period
3. **End date**: The date to end the investment period
4. **Daily investment**: The amount to invest each trading day when buy conditions are met

## Technical Indicators

### MACD (Moving Average Convergence Divergence)
- **MACD Line**: 12-period EMA - 26-period EMA
- **Signal Line**: 9-period EMA of the MACD Line
- **Histogram**: MACD Line - Signal Line
- **Buy Signal**: MACD Line > Signal Line

### EMA (Exponential Moving Average)
- **50-period EMA**: Used as a trend filter
- **Buy Signal**: Current price > 50 EMA

## Strategy Logic Flow

1. **Initialization**: Start with no positions, tracking highest profit and last known high.

2. **Daily Evaluation**:
   - Check if MACD > Signal
   - Check if price > 50 EMA (or skip if EMA unavailable)
   - If both conditions met → Buy daily investment amount
   - Calculate current profit
   - Update highest profit if new high reached

3. **Sell Check**:
   - Compare current profit to reference high (last known high if exists, otherwise highest profit)
   - If profit < 90% of reference high → Sell all shares
   - Set last known high to profit at time of sale
   - Reset highest profit to new last known high

4. **Repeat**: Continue daily evaluation until end date.

## Example Scenario

- Day 1-10: MACD > Signal and price > 50 EMA → Buying daily
- Day 11: Profit reaches $1000 (new high)
- Day 12-20: Continue buying, profit grows to $1200 (new high)
- Day 21: Profit drops to $1080 (10% below $1200) → Sell all shares
- Day 21: Set last known high to $1200
- Day 22-30: MACD conditions not met → Waiting
- Day 31: MACD > Signal and price > 50 EMA → Start buying again
- Day 32: Profit reaches $1100 (new high, but below previous $1200)
- Day 33: Profit drops to $1080 (10% below $1200, the last known high) → Sell all shares

## Advantages

- **Trend Following**: Uses MACD to identify momentum and EMA to confirm trend direction
- **Profit Protection**: Automatically sells when profit drops to protect gains
- **Adaptive**: Works with new stocks that don't have enough data for EMA calculation yet
- **Risk Management**: Trailing stop mechanism helps lock in profits

## Considerations

- The strategy may sell during temporary dips even if the trend continues upward
- For new stocks without 50 EMA data, the strategy relies solely on MACD signals initially
- The 10% drop threshold is fixed and may not suit all market conditions

