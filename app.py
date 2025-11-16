#!/usr/bin/env python3
"""
Streamlit Web App for Stock Investment Calculator
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, datetime
from strategies import get_strategy, STRATEGIES
from stock_investment_calculator import StockInvestmentCalculator

# Page configuration
st.set_page_config(
    page_title="Stock Investment Calculator",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Stock Investment Calculator")
st.markdown("Calculate and visualize your investment growth using different strategies")

# Sidebar
with st.sidebar:
    st.header("Calculator")
    # Navigation: choose main section
    main_section = st.radio("Sections", ["Calculator", "Help"], index=0)
    
    help_topic = None
    selected_strategy_for_help = None
    if main_section == "Help":
        st.header("Help")
        help_topic = st.radio("Topics", ["How to use this calculator", "Available strategies"], index=0)
        if help_topic == "Available strategies":
            # Let user pick a strategy to view details; content renders on main page
            strategy_name_map = {sid: get_strategy(sid).name for sid in STRATEGIES.keys()}
            selected_strategy_for_help = st.selectbox(
                "Strategy",
                options=list(STRATEGIES.keys()),
                format_func=lambda x: strategy_name_map[x]
            )

# Main content routing
if 'main_section' not in locals():
    main_section = "Calculator"

if main_section == "Calculator":
    # Strategy selection
    strategy_options = {strategy_id: get_strategy(strategy_id).name for strategy_id in STRATEGIES.keys()}
    selected_strategy_id = st.selectbox(
        "Investment Strategy",
        options=list(STRATEGIES.keys()),
        format_func=lambda x: strategy_options[x],
        help="Select the investment strategy to use"
    )
    
    # Get the selected strategy
    strategy = get_strategy(selected_strategy_id)
    
    # Display strategy description
    st.info(f"**{strategy.name}**: {strategy.description}")
    
    st.divider()
    st.header("Strategy Parameters")
    
    # Dynamically create input fields based on strategy
    params = {}
    param_definitions = strategy.input_parameters

    # Helper: render a single parameter inside a provided container (column)
    def render_param(container, param_def):
        param_name = param_def['name']
        param_label = param_def['label']
        param_type = param_def['type']
        param_default = param_def.get('default')
        param_required = param_def.get('required', True)
        param_help = param_def.get('help', '')
        
        if param_type == 'text':
            value = container.text_input(
                param_label,
                value=param_default if param_default else '',
                help=param_help,
                key=f"param_{param_name}"
            )
            params[param_name] = value
        elif param_type == 'number':
            param_min = param_def.get('min')
            param_max = param_def.get('max')
            param_step = param_def.get('step', 1.0)
            min_val = float(param_min) if param_min is not None else None
            max_val = float(param_max) if param_max is not None else None
            default_val = float(param_default) if param_default is not None else 0.0
            step_val = float(param_step) if param_step is not None else 1.0
            value = container.number_input(
                param_label,
                min_value=min_val,
                max_value=max_val,
                value=default_val,
                step=step_val,
                help=param_help
            )
            params[param_name] = value
        elif param_type == 'date':
            value = container.date_input(
                param_label,
                value=param_default if param_default else date.today(),
                help=param_help
            )
            params[param_name] = value
        elif param_type == 'select':
            options = param_def.get('options', [])
            value = container.selectbox(
                param_label,
                options=options,
                index=0 if param_default and param_default in options else 0,
                help=param_help
            )
            params[param_name] = value

    # Small fields logic: dates and money fields get compact columns; others full width
    def is_small_field(p):
        # Any date field is small
        if p.get('type') == 'date':
            return True
        # Any number field is small (limit visual width to ~20 chars via columns)
        if p.get('type') == 'number':
            return True
        # Otherwise not small
        return False

    small_buffer = []
    for p in param_definitions:
        if is_small_field(p):
            small_buffer.append(p)
            # Render a row when we have 4 small fields
            if len(small_buffer) == 4:
                cols = st.columns(4)
                for col, sp in zip(cols, small_buffer):
                    render_param(col, sp)
                small_buffer = []
        else:
            # Flush any buffered small fields before rendering a full-width field
            if small_buffer:
                cols = st.columns(len(small_buffer))
                for col, sp in zip(cols, small_buffer):
                    render_param(col, sp)
                small_buffer = []
            # Render large field full width
            render_param(st, p)

    # Flush remaining small fields
    if small_buffer:
        cols = st.columns(len(small_buffer))
        for col, sp in zip(cols, small_buffer):
            render_param(col, sp)

    calculate_button = st.button("Calculate", type="primary", width='stretch')
    
    # Main content area
    if calculate_button:
        # Validate required parameters
        validation_errors = []
        for param_def in param_definitions:
            if param_def.get('required', True):
                param_name = param_def['name']
                if param_name not in params or params[param_name] is None or params[param_name] == '':
                    validation_errors.append(f"{param_def['label']} is required")
        
        # Additional validations
        if 'start_date' in params and 'end_date' in params:
            if params['start_date'] >= params['end_date']:
                validation_errors.append("Start date must be before end date")
            if params['start_date'] > date.today():
                validation_errors.append(f"Start date ({params['start_date']}) cannot be in the future")
            if params['end_date'] > date.today():
                validation_errors.append(f"End date ({params['end_date']}) cannot be in the future. Today is {date.today()}")
        
        # Validate ticker/stock_list based on strategy
        if 'ticker' in params:
            ticker_value = params['ticker'].strip().upper() if params['ticker'] else ''
            if not ticker_value:
                validation_errors.append("Stock Ticker is required")
        
        if 'stock_list' in params:
            stock_list_value = params['stock_list'].strip() if params['stock_list'] else ''
            if not stock_list_value:
                validation_errors.append("Stock List is required")
            else:
                parsed_stocks = [s.strip().upper() for s in stock_list_value.split(',') if s.strip()]
                st.info(f"📋 Using stock list: **{', '.join(parsed_stocks)}**")
        
        if validation_errors:
            for error in validation_errors:
                st.error(error)
        else:
            # Initialize calculator
            calculator = StockInvestmentCalculator(db_path="stock_prices.db") # Default db_path
            
            # Get ticker for display (from params, strategy-specific)
            display_ticker = params.get('ticker', params.get('stock_list', 'N/A')).strip().upper()
            if ',' in display_ticker:
                tickers = [s.strip().upper() for s in display_ticker.split(',') if s.strip()]
                display_ticker = f"{tickers[0]}" if len(tickers) == 1 else f"{', '.join(tickers[:3])}{'...' if len(tickers) > 3 else ''}"
            
            # Show progress
            with st.spinner(f"Calculating investment growth using {strategy.name}..."):
                try:
                    # Calculate investment growth (ticker parameter is now optional, strategies use params)
                    results_df = calculator.calculate(selected_strategy_id, display_ticker, params)
                    
                    if results_df.empty:
                        st.warning(f"No data found in the specified date range.")
                    else:
                        # Display summary metrics
                        final_row = results_df.iloc[-1]
                        total_invested = final_row['Total Account'] - final_row['Profit/Loss']
                        final_value = final_row['Total Account']
                        profit_loss = final_row['Profit/Loss']
                        return_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
                        
                        # Summary cards
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Invested", f"${total_invested:,.2f}")
                        with col2:
                            st.metric("Final Value", f"${final_value:,.2f}")
                        with col3:
                            st.metric("Profit/Loss", f"${profit_loss:,.2f}", 
                                     delta=f"{return_pct:.2f}%")
                        with col4:
                            st.metric("Total Shares", f"{final_row['Stocks']:.4f}")
                        
                        st.divider()
                        
                        # Interactive Plotly chart
                        st.subheader("Investment Growth Visualization")
                        
                        # Prepare data for plotting
                        dates = pd.to_datetime(results_df['Date'])
                        
                        # Create interactive plot with Plotly
                        fig = go.Figure()
                        
                        # Add Principal Invested line
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=results_df['Principal Invested'],
                            mode='lines+markers',
                            name='Principal Invested',
                            line=dict(color='#2c3e50', width=2),
                            marker=dict(size=4),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                         'Date: %{x|%Y-%m-%d}<br>' +
                                         'Value: $%{y:,.2f}<br>' +
                                         '<extra></extra>'
                        ))
                        
                        # Add Total Account Value line
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=results_df['Total Account'],
                            mode='lines+markers',
                            name='Total Account Value',
                            line=dict(color='#27ae60', width=2),
                            marker=dict(size=4),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                         'Date: %{x|%Y-%m-%d}<br>' +
                                         'Value: $%{y:,.2f}<br>' +
                                         '<extra></extra>'
                        ))
                        
                        # Add markers for stock switches (if Current Stock column exists)
                        if 'Current Stock' in results_df.columns:
                            # Find dates where stock changes (exclude first row as it's not a switch)
                            stock_changes = results_df['Current Stock'] != results_df['Current Stock'].shift()
                            # Filter out the first row (index 0) as it's the initial selection, not a switch
                            stock_changes.iloc[0] = False
                            switch_dates = dates[stock_changes]
                            switch_values = results_df['Total Account'][stock_changes]
                            switch_stocks = results_df['Current Stock'][stock_changes]
                            
                            if len(switch_dates) > 0:
                                # Convert dates to list for Plotly
                                switch_dates_list = switch_dates.tolist()
                                
                                # Add vertical lines and markers for stock switches
                                for switch_date, switch_value, switch_stock in zip(switch_dates_list, switch_values, switch_stocks):
                                    # Add vertical line using shape
                                    fig.add_shape(
                                        type="line",
                                        x0=switch_date,
                                        x1=switch_date,
                                        y0=0,
                                        y1=1,
                                        yref="paper",
                                        line=dict(
                                            color="#e74c3c",
                                            width=2,
                                            dash="dash"
                                        ),
                                        opacity=0.5
                                    )
                                    
                                    # Add annotation for the switch
                                    fig.add_annotation(
                                        x=switch_date,
                                        y=switch_value,
                                        text=switch_stock,
                                        showarrow=True,
                                        arrowhead=2,
                                        arrowsize=1,
                                        arrowwidth=2,
                                        arrowcolor="#e74c3c",
                                        ax=0,
                                        ay=-30,
                                        bgcolor="rgba(231, 76, 60, 0.8)",
                                        bordercolor="#e74c3c",
                                        borderwidth=1,
                                        font=dict(color="white", size=10)
                                    )
                                
                                # Add markers at switch points
                                fig.add_trace(go.Scatter(
                                    x=switch_dates_list,
                                    y=switch_values,
                                    mode='markers',
                                    name='Stock Switch',
                                    marker=dict(
                                        symbol='triangle-up',
                                        size=12,
                                        color='#e74c3c',
                                        line=dict(width=2, color='white')
                                    ),
                                    hovertemplate='<b>Stock Switch</b><br>' +
                                                 'Date: %{x|%Y-%m-%d}<br>' +
                                                 'New Stock: %{customdata}<br>' +
                                                 'Value: $%{y:,.2f}<br>' +
                                                 '<extra></extra>',
                                    customdata=switch_stocks
                                ))
                        
                        # Update layout
                        # Get display name for title
                        title_ticker = params.get('ticker', params.get('stock_list', 'Stocks')).strip().upper()
                        if ',' in title_ticker:
                            tickers = [s.strip().upper() for s in title_ticker.split(',') if s.strip()]
                            title_ticker = f"{len(tickers)} Stocks" if len(tickers) > 1 else tickers[0]
                        
                        fig.update_layout(
                            title=dict(
                                text=f'Investment Growth: {title_ticker} ({strategy.name})',
                                font=dict(size=20, color='#2c3e50'),
                                x=0.5,
                                xanchor='center'
                            ),
                            xaxis=dict(
                                title='Date',
                                showgrid=True,
                                gridcolor='rgba(0,0,0,0.1)'
                            ),
                            yaxis=dict(
                                title='Value ($)',
                                showgrid=True,
                                gridcolor='rgba(0,0,0,0.1)',
                                tickformat='$,.0f'
                            ),
                            hovermode='x unified',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            height=500,
                            template='plotly_white',
                            margin=dict(l=50, r=50, t=80, b=50)
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        st.divider()
                        
                        # Display detailed table
                        st.subheader("Detailed Investment Table")
                        
                        # Format the dataframe for display (exclude Principal Invested from table since it's in the chart)
                        # Include Current Stock if it exists in the results
                        base_columns = ['Date', 'Investment $', 'Stocks Bought', 'Stocks', 'Total Account', 'Profit/Loss']
                        if 'Current Stock' in results_df.columns:
                            base_columns.insert(1, 'Current Stock')  # Insert after Date
                        
                        display_df = results_df[base_columns].copy()
                        
                        # Format columns for better display
                        display_df['Investment $'] = display_df['Investment $'].apply(lambda x: f"${x:,.2f}")
                        display_df['Stocks Bought'] = display_df['Stocks Bought'].apply(lambda x: f"{x:.6f}")
                        display_df['Stocks'] = display_df['Stocks'].apply(lambda x: f"{x:.6f}")
                        display_df['Total Account'] = display_df['Total Account'].apply(lambda x: f"${x:,.2f}")
                        display_df['Profit/Loss'] = display_df['Profit/Loss'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(
                            display_df,
                            width='stretch',
                            hide_index=True
                        )
                        
                        # Download button for CSV
                        csv = results_df.to_csv(index=False)
                        # Get filename prefix from ticker or stock_list
                        file_prefix = params.get('ticker', params.get('stock_list', 'stocks')).strip().upper().replace(',', '_').replace(' ', '')
                        st.download_button(
                            label="Download Results as CSV",
                            data=csv,
                            file_name=f"{file_prefix}_{selected_strategy_id}_{params.get('start_date', 'start')}_{params.get('end_date', 'end')}.csv",
                            mime="text/csv"
                        )
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)

else:
    # Help content on main page
    if help_topic == "How to use this calculator":
        st.header("How to use this calculator")
        st.markdown(
            "**Steps:**\n"
            "1. Select an investment strategy from the dropdown.\n"
            "2. Enter the strategy-specific parameters.\n"
            "3. Click 'Calculate' to compute results and show the chart & table.\n\n"
            "**Features:**\n"
            "- Multiple strategies\n"
            "- Interactive charts\n"
            "- Summary metrics\n"
            "- Detailed table & CSV export\n"
        )
    elif help_topic == "Available strategies":
        st.header("Available Strategies")
        if selected_strategy_for_help:
            s = get_strategy(selected_strategy_for_help)
            st.subheader(s.name)
            st.markdown(f"**ID**: `{selected_strategy_for_help}`")
            st.markdown(f"**Description**: {s.description}")
            st.markdown("**Parameters**:")
            for param_def in s.input_parameters:
                required = "Required" if param_def.get('required', True) else "Optional"
                st.markdown(f"- `{param_def['name']}` ({param_def['type']}, {required}): {param_def.get('help', 'No description')}")
        else:
            st.info("Select a strategy from the sidebar to view details.")
