# Investment Strategies

This directory contains different investment strategies that can be used to calculate and visualize investment growth.

## Available Strategies

1. **[Simple Recurring Strategy](./simple_recurring.md)** - Dollar-cost averaging with a single stock
2. **[RSI Swing Strategy](./rsi_swing.md)** - RSI-based stock selection with automatic switching

## How to Use

Each strategy can be used through:
- **Web Application**: Select the strategy from the dropdown in the Streamlit app
- **Command Line**: Use the `--strategy` parameter with the stock investment calculator

## Strategy Architecture

All strategies inherit from the base `Strategy` class and implement:
- `name`: Display name of the strategy
- `description`: Brief description
- `input_parameters`: List of required parameters
- `calculate()`: Main calculation method that returns a DataFrame with investment results

## Adding New Strategies

📖 **See [ADDING_NEW_STRATEGY.md](./ADDING_NEW_STRATEGY.md) for a complete guide on creating new strategies.**

Quick steps:
1. Create a new file in this directory (e.g., `my_strategy.py`)
2. Import `Strategy` from `strategies.base`
3. Implement all required methods (`name`, `description`, `input_parameters`, `calculate`)
4. Register it in `strategies/__init__.py`

The guide includes:
- Complete interface documentation
- Parameter type definitions
- Output format requirements
- Step-by-step instructions
- Complete working examples
- Best practices and troubleshooting

