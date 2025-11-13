# Stock Investment Calculator

A Python tool for calculating and visualizing investment growth using dollar-cost averaging (DCA) strategy. This script tracks daily investments in a stock and calculates the growth of your portfolio over time.

## Features

- **Web Application**: Interactive Streamlit web interface with real-time calculations
- **Interactive Charts**: Plotly-powered charts with hover tooltips showing exact values for any date
- **Database Management**: Automatically stores daily OHLC (Open, High, Low, Close) stock prices in a local SQLite database
- **Smart Data Fetching**: Only fetches missing data from the last available date, reducing API calls
- **Dollar-Cost Averaging**: Calculates investment growth assuming a fixed daily investment amount
- **Fractional Shares**: Supports fractional share purchases when daily investment isn't a multiple of stock price
- **Visualization**: Plots principal invested vs total account value over time
- **Detailed Reporting**: Generates a table with daily investment metrics
- **CSV Export**: Download results for further analysis

## Requirements

- Python 3.10+
- Poetry (for dependency management) or pip

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd spx_invest
```

2. Install dependencies using Poetry:
```bash
poetry install
```

Or install manually:
```bash
pip install -r requirements.txt
```

## Usage

### Web Application (Recommended)

Launch the interactive web application:

```bash
poetry run streamlit run app.py
```

Or with Streamlit installed directly:
```bash
streamlit run app.py
```

The web app provides:
- **Interactive Input Form**: Easy-to-use sidebar with date pickers and input fields
- **Interactive Charts**: Hover over any point to see exact values for that date
- **Summary Metrics**: Quick overview cards showing key statistics
- **Detailed Table**: Day-by-day investment breakdown
- **CSV Export**: Download results for further analysis

### Command Line Interface

Calculate investment growth for a stock with daily investments:

```bash
poetry run python stock_investment_calculator.py <TICKER> <START_DATE> <DAILY_INVESTMENT>
```

**Example:**
```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100
```

### With End Date

Specify an end date for the calculation:

```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100 --end_date 2024-12-31
```

### Save Results to CSV

Export the results table to a CSV file:

```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100 --output results.csv
```

### Custom Database Path

Use a custom database file:

```bash
poetry run python stock_investment_calculator.py AAPL 2024-01-01 100 --db my_stocks.db
```

### Generate Plot

The script automatically displays an interactive plot showing:
- Principal Invested (cumulative daily investments)
- Total Account Value (current portfolio value)

The plot window will pop up at the end of the calculation. Close the window to exit the script.

## Command Line Arguments

- `ticker` (required): Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
- `start_date` (required): Start date in YYYY-MM-DD format
- `daily_investment` (required): Daily investment amount in dollars
- `--end_date` (optional): End date in YYYY-MM-DD format (defaults to today)
- `--db` (optional): Database file path (defaults to `stock_prices.db`)
- `--output` (optional): CSV output file path
- `--no-plot` (optional): Skip displaying the interactive plot

## Output

The script generates:

1. **Console Table**: A detailed table showing:
   - Date
   - Investment $ (daily investment amount)
   - Stocks Bought (fractional shares purchased)
   - Stocks (cumulative total shares)
   - Total Account (current portfolio value)
   - Profit/Loss (profit or loss for that day)

2. **Summary Statistics**: 
   - Total Invested
   - Final Account Value
   - Total Profit/Loss
   - Return Percentage

3. **Interactive Plot**: A visualization window comparing principal invested vs total account value over time (closes when you close the window)

## How It Works

1. **Database Check**: The script checks the local SQLite database for existing price data
2. **Data Fetching**: If data is missing, it fetches daily OHLC data from yfinance API
3. **Investment Calculation**: For each trading day:
   - Calculates fractional shares that can be purchased with the daily investment
   - Updates cumulative shares and total invested
   - Calculates current portfolio value and profit/loss
4. **Visualization**: Generates a plot comparing the growth of principal vs portfolio value

## Database Schema

The script uses a SQLite database with the following schema:

```sql
CREATE TABLE daily_prices (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (ticker, date)
)
```

## Examples

### Example 1: Calculate AAPL investment growth
```bash
poetry run python stock_investment_calculator.py AAPL 2023-01-01 50
```

### Example 2: Calculate with specific date range and save results
```bash
poetry run python stock_investment_calculator.py MSFT 2023-06-01 75 --end_date 2023-12-31 --output msft_results.csv
```

### Example 3: Use custom database
```bash
poetry run python stock_investment_calculator.py GOOGL 2024-01-01 100 --db tech_stocks.db
```

## Notes

- The script uses the **close price** for calculating shares purchased each day
- Only **trading days** are included in calculations (weekends and holidays are skipped)
- Fractional shares are supported, allowing any daily investment amount
- The database persists data between runs, so subsequent runs are faster
- Data is fetched from yfinance, which provides free stock market data

## License

This project is open source and available for personal use.

## Contributing

Feel free to submit issues or pull requests for improvements.

