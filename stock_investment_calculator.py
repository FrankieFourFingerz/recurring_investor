#!/usr/bin/env python3
"""
Stock Investment Calculator - CLI interface using strategy pattern
"""

import argparse
import sys
import logging
from datetime import date, datetime
import pandas as pd
import matplotlib.pyplot as plt
from strategies import get_strategy, STRATEGIES


class StockInvestmentCalculator:
    """Calculator that uses investment strategies."""
    
    def __init__(self, db_path: str = "stock_prices.db"):
        """Initialize the calculator with database path."""
        self.db_path = db_path
    
    def calculate(self, strategy_id: str, ticker: str, params: dict) -> pd.DataFrame:
        """
        Calculate investment growth using the specified strategy.
        
        Args:
            strategy_id: ID of the strategy to use
            ticker: Stock ticker symbol
            params: Strategy-specific parameters
            
        Returns:
            DataFrame with investment results
        """
        strategy = get_strategy(strategy_id)
        return strategy.calculate(self.db_path, ticker, params)
    
    def plot_investment_growth(self, results_df: pd.DataFrame, ticker: str):
        """
        Plot principal invested vs total account value over time.
        Displays the plot interactively and waits for user to close it.
        
        Args:
            results_df: DataFrame with investment growth data
            ticker: Stock ticker symbol
        """
        if results_df.empty:
            print("No data to plot.")
            return
        
        # Convert Date column to datetime for plotting
        dates = pd.to_datetime(results_df['Date'])
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(dates, results_df['Principal Invested'], label='Principal Invested', linewidth=2, color='#2c3e50')
        plt.plot(dates, results_df['Total Account'], label='Total Account Value', linewidth=2, color='#27ae60')
        
        # Formatting
        plt.title(f'Investment Growth: {ticker}', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Value ($)', fontsize=12)
        plt.legend(loc='best', fontsize=11)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        
        # Display the plot interactively
        print("\nDisplaying plot... Close the plot window to continue.")
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Calculate investment growth for a stock using various strategies'
    )
    
    # Strategy selection
    parser.add_argument(
        '--strategy',
        type=str,
        default='simple_recurring',
        choices=list(STRATEGIES.keys()),
        help=f'Investment strategy to use (default: simple_recurring). Available: {", ".join(STRATEGIES.keys())}'
    )
    
    # Common parameters
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('start_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('daily_investment', type=float, help='Daily investment amount in dollars')
    parser.add_argument('--end_date', type=str, default=None, help='End date (YYYY-MM-DD). Defaults to today.')
    parser.add_argument('--db', type=str, default='stock_prices.db', help='Database file path (default: stock_prices.db)')
    parser.add_argument('--output', type=str, default=None, help='Output CSV file path (optional)')
    parser.add_argument('--no-plot', action='store_true', help='Skip displaying the plot')
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    except ValueError:
        print(f"Error: Invalid start_date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Error: Invalid end_date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize calculator
    calculator = StockInvestmentCalculator(db_path=args.db)
    
    # Get strategy and prepare parameters
    strategy = get_strategy(args.strategy)
    
    # Build parameters dict based on strategy
    params = {
        'start_date': start_date,
        'end_date': end_date,
        'daily_investment': args.daily_investment
    }
    
    # Calculate investment growth
    try:
        results_df = calculator.calculate(args.strategy, args.ticker, params)
        
        # Display results
        print("\n" + "="*80)
        print(f"Investment Growth Analysis for {args.ticker}")
        print(f"Strategy: {strategy.name}")
        print(f"Start Date: {start_date}, End Date: {end_date or date.today()}")
        print(f"Daily Investment: ${args.daily_investment:.2f}")
        print("="*80 + "\n")
        
        # Set pandas display options for better formatting
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        print(results_df.to_string(index=False))
        
        # Save to CSV if requested
        if args.output:
            results_df.to_csv(args.output, index=False)
            print(f"\nResults saved to {args.output}")
        
        # Print summary
        if not results_df.empty:
            final_row = results_df.iloc[-1]
            print(f"\nSummary:")
            print(f"  Total Invested: ${final_row['Total Account'] - final_row['Profit/Loss']:.2f}")
            print(f"  Final Account Value: ${final_row['Total Account']:.2f}")
            print(f"  Total Profit/Loss: ${final_row['Profit/Loss']:.2f}")
            print(f"  Return Percentage: {(final_row['Profit/Loss'] / (final_row['Total Account'] - final_row['Profit/Loss']) * 100):.2f}%")
        
        # Generate plot if not disabled
        if not args.no_plot:
            calculator.plot_investment_growth(results_df, args.ticker)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
