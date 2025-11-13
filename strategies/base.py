#!/usr/bin/env python3
"""
Base Strategy class for all investment strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd


class Strategy(ABC):
    """Base class for all investment strategies."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the strategy."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the strategy."""
        pass
    
    @property
    @abstractmethod
    def input_parameters(self) -> List[Dict[str, Any]]:
        """
        Return a list of input parameter definitions.
        Each dict should have:
        - 'name': parameter name (used as key)
        - 'label': display label
        - 'type': 'text', 'number', 'date', 'select'
        - 'default': default value
        - 'required': bool
        - 'help': help text (optional)
        - 'min': minimum value (for numbers, optional)
        - 'max': maximum value (for numbers, optional)
        - 'options': list of options (for select type, optional)
        """
        pass
    
    @abstractmethod
    def calculate(self, db_path: str, ticker: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Calculate investment growth based on the strategy.
        
        Args:
            db_path: Path to the database
            ticker: Stock ticker symbol
            params: Dictionary of input parameters
            
        Returns:
            DataFrame with columns: Date, Investment $, Stocks Bought, Stocks, 
            Total Account, Profit/Loss, Principal Invested
        """
        pass

