"""
Indicator Computation Service Module

Provides utilities for computing M&E indicators from survey data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import re


class IndicatorComputationService:
    """
    Service class for computing M&E indicators from survey data.
    
    Supports:
    - Formula-based calculations
    - Filter criteria application
    - Aggregation functions
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the service with a DataFrame.
        
        Args:
            dataframe: pandas DataFrame containing survey data
        """
        self.df = dataframe
        self.total_rows = len(dataframe)
    
    def compute_indicator(
        self,
        indicator_name: str,
        formula: str,
        filter_criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Compute an indicator value based on formula and filters.

        Args:
            indicator_name: Name of the indicator
            formula: Formula string (e.g., "COUNT(column_name)", "SUM(column1) / COUNT(column2)")
            filter_criteria: Dictionary of column:value pairs to filter data

        Returns:
            Dictionary with computed value and metadata
        """
        try:
            # Apply filters if provided
            df_filtered = self.df.copy()

            if filter_criteria:
                for column, value in filter_criteria.items():
                    if column in df_filtered.columns:
                        df_filtered = df_filtered[df_filtered[column] == value]

            # Parse and evaluate formula
            result = self._evaluate_formula(formula, df_filtered)

            # Handle NaN/Inf values
            if pd.isna(result) or np.isinf(result):
                result = None

            return {
                'indicator_name': indicator_name,
                'formula': formula,
                'filter_criteria': filter_criteria or {},
                'value': result,
                'rows_processed': len(df_filtered),
                'total_rows': self.total_rows,
                'status': 'success'
            }

        except Exception as e:
            return {
                'indicator_name': indicator_name,
                'formula': formula,
                'filter_criteria': filter_criteria or {},
                'value': None,
                'error': str(e),
                'status': 'error'
            }
    
    def _evaluate_formula(self, formula: str, df: pd.DataFrame) -> float:
        """
        Evaluate a formula string against the DataFrame.

        Supported functions:
        - COUNT(column): Count non-null values
        - SUM(column): Sum of values
        - AVG(column): Average of values
        - MIN(column): Minimum value
        - MAX(column): Maximum value
        - PERCENTAGE(column, value): Percentage of rows where column == value

        Field names with spaces should be used directly without quotes.
        Example: COUNT(Course Name) or COUNT(Student ID)

        Args:
            formula: Formula string
            df: DataFrame to evaluate against

        Returns:
            Computed value
        """
        # Replace function calls with actual computations
        formula_eval = formula

        # Updated pattern to match field names with spaces and special characters
        # Matches: word characters, spaces, hyphens, underscores, dots
        field_pattern = r'[\w\s\-\.]+'

        # COUNT function
        count_pattern = r'COUNT\((' + field_pattern + r')\)'
        for match in re.finditer(count_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            if column in df.columns:
                count_value = df[column].count()
                formula_eval = formula_eval.replace(match.group(0), str(count_value))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # SUM function
        sum_pattern = r'SUM\((' + field_pattern + r')\)'
        for match in re.finditer(sum_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            if column in df.columns:
                sum_value = pd.to_numeric(df[column], errors='coerce').sum()
                formula_eval = formula_eval.replace(match.group(0), str(sum_value))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # AVG function
        avg_pattern = r'AVG\((' + field_pattern + r')\)'
        for match in re.finditer(avg_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            if column in df.columns:
                avg_value = pd.to_numeric(df[column], errors='coerce').mean()
                formula_eval = formula_eval.replace(match.group(0), str(avg_value))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # MIN function
        min_pattern = r'MIN\((' + field_pattern + r')\)'
        for match in re.finditer(min_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            if column in df.columns:
                min_value = pd.to_numeric(df[column], errors='coerce').min()
                formula_eval = formula_eval.replace(match.group(0), str(min_value))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # MAX function
        max_pattern = r'MAX\((' + field_pattern + r')\)'
        for match in re.finditer(max_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            if column in df.columns:
                max_value = pd.to_numeric(df[column], errors='coerce').max()
                formula_eval = formula_eval.replace(match.group(0), str(max_value))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # PERCENTAGE function - supports field names with spaces
        percentage_pattern = r'PERCENTAGE\((' + field_pattern + r'),\s*[\'"]?([^\)]+?)[\'"]?\)'
        for match in re.finditer(percentage_pattern, formula_eval, re.IGNORECASE):
            column = match.group(1).strip()
            value = match.group(2).strip().strip('\'"')
            if column in df.columns:
                count = (df[column].astype(str) == str(value)).sum()
                percentage = (count / len(df)) * 100 if len(df) > 0 else 0
                formula_eval = formula_eval.replace(match.group(0), str(percentage))
            else:
                raise ValueError(f"Column '{column}' not found in survey data. Available columns: {', '.join(df.columns.tolist())}")

        # Evaluate the formula
        try:
            result = eval(formula_eval)
            return float(result)
        except Exception as e:
            raise ValueError(f"Could not evaluate formula: {formula}. Evaluation error: {str(e)}")
    
    def compute_multiple_indicators(
        self,
        indicators: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compute multiple indicators at once.
        
        Args:
            indicators: List of dicts with 'name', 'formula', and optional 'filter_criteria'
            
        Returns:
            List of computation results
        """
        results = []
        
        for indicator in indicators:
            result = self.compute_indicator(
                indicator_name=indicator.get('name'),
                formula=indicator.get('formula'),
                filter_criteria=indicator.get('filter_criteria')
            )
            results.append(result)
        
        return results
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for all numeric columns.

        Returns:
            Dictionary with statistics for each numeric column
        """
        stats = {}

        def safe_float(value):
            """Convert value to float, handling NaN/Inf values."""
            if pd.isna(value) or np.isinf(value):
                return None
            return float(value)

        for column in self.df.columns:
            try:
                numeric_data = pd.to_numeric(self.df[column], errors='coerce')
                if numeric_data.notna().sum() > 0:
                    stats[column] = {
                        'count': int(numeric_data.count()),
                        'mean': safe_float(numeric_data.mean()),
                        'median': safe_float(numeric_data.median()),
                        'std': safe_float(numeric_data.std()),
                        'min': safe_float(numeric_data.min()),
                        'max': safe_float(numeric_data.max()),
                        'sum': safe_float(numeric_data.sum())
                    }
            except:
                pass

        return stats

