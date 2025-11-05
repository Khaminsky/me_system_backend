"""
Data Cleaning Service Module

Provides utilities for data validation, cleaning, and quality assessment.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple


class DataCleaningService:
    """
    Service class for handling data validation and cleaning operations.
    
    Accepts pandas DataFrames and provides methods for:
    - Checking missing values
    - Detecting invalid data types
    - Counting unique and null entries
    - Generating quality reports
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the service with a DataFrame.
        
        Args:
            dataframe: pandas DataFrame to process
        """
        self.df = dataframe
        self.total_rows = len(dataframe)
        self.total_columns = len(dataframe.columns)
    
    def check_missing_values(self) -> Dict[str, Any]:
        """
        Check for missing values in each column.
        
        Returns:
            Dictionary with missing value statistics per column
        """
        missing_data = {}
        
        for column in self.df.columns:
            missing_count = self.df[column].isnull().sum()
            missing_percentage = (missing_count / self.total_rows) * 100
            
            missing_data[column] = {
                'missing_count': int(missing_count),
                'missing_percentage': round(missing_percentage, 2),
                'non_null_count': int(self.total_rows - missing_count)
            }
        
        return missing_data
    
    def detect_invalid_data_types(self) -> Dict[str, Any]:
        """
        Detect and report data type information for each column.
        
        Returns:
            Dictionary with data type information per column
        """
        type_info = {}
        
        for column in self.df.columns:
            dtype = str(self.df[column].dtype)
            
            # Try to infer if column should be numeric
            try:
                pd.to_numeric(self.df[column], errors='coerce')
                inferred_type = 'numeric'
            except:
                inferred_type = 'string'
            
            # Count non-numeric values if column is supposed to be numeric
            if inferred_type == 'numeric':
                non_numeric_count = self.df[column].apply(
                    lambda x: not isinstance(x, (int, float, np.integer, np.floating)) 
                    and pd.notna(x)
                ).sum()
            else:
                non_numeric_count = 0
            
            type_info[column] = {
                'detected_type': dtype,
                'inferred_type': inferred_type,
                'non_numeric_count': int(non_numeric_count),
                'unique_values': int(self.df[column].nunique())
            }
        
        return type_info
    
    def count_unique_and_null(self) -> Dict[str, Any]:
        """
        Count unique and null entries for each column.
        
        Returns:
            Dictionary with unique and null counts per column
        """
        unique_null_data = {}
        
        for column in self.df.columns:
            unique_count = self.df[column].nunique()
            null_count = self.df[column].isnull().sum()
            
            unique_null_data[column] = {
                'unique_count': int(unique_count),
                'null_count': int(null_count),
                'duplicate_count': int(self.total_rows - unique_count - null_count)
            }
        
        return unique_null_data
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report.
        
        Returns:
            Dictionary containing complete quality assessment
        """
        missing_values = self.check_missing_values()
        data_types = self.detect_invalid_data_types()
        unique_null = self.count_unique_and_null()
        
        # Calculate overall quality score
        total_cells = self.total_rows * self.total_columns
        missing_cells = sum(
            data['missing_count'] for data in missing_values.values()
        )
        quality_score = round(
            ((total_cells - missing_cells) / total_cells) * 100, 2
        )
        
        # Identify problematic columns
        problematic_columns = []
        for column in self.df.columns:
            missing_pct = missing_values[column]['missing_percentage']
            if missing_pct > 20:  # More than 20% missing
                problematic_columns.append({
                    'column': column,
                    'issue': 'high_missing_values',
                    'percentage': missing_pct
                })
        
        report = {
            'summary': {
                'total_rows': self.total_rows,
                'total_columns': self.total_columns,
                'total_cells': total_cells,
                'missing_cells': int(missing_cells),
                'quality_score': quality_score,
                'quality_status': 'Good' if quality_score >= 80 else 'Fair' if quality_score >= 60 else 'Poor'
            },
            'missing_values': missing_values,
            'data_types': data_types,
            'unique_and_null': unique_null,
            'problematic_columns': problematic_columns,
            'recommendations': self._generate_recommendations(
                missing_values, data_types, quality_score
            )
        }
        
        return report
    
    def _generate_recommendations(
        self, 
        missing_values: Dict, 
        data_types: Dict,
        quality_score: float
    ) -> List[str]:
        """
        Generate recommendations based on data quality assessment.
        
        Args:
            missing_values: Missing values report
            data_types: Data types report
            quality_score: Overall quality score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for high missing values
        for column, data in missing_values.items():
            if data['missing_percentage'] > 50:
                recommendations.append(
                    f"Column '{column}' has {data['missing_percentage']}% missing values. "
                    "Consider removing or imputing this column."
                )
            elif data['missing_percentage'] > 20:
                recommendations.append(
                    f"Column '{column}' has {data['missing_percentage']}% missing values. "
                    "Consider imputation strategies."
                )
        
        # Check for data type mismatches
        for column, data in data_types.items():
            if data['non_numeric_count'] > 0 and data['inferred_type'] == 'numeric':
                recommendations.append(
                    f"Column '{column}' has {data['non_numeric_count']} non-numeric values. "
                    "Verify data type consistency."
                )
        
        # Overall quality recommendations
        if quality_score < 60:
            recommendations.append(
                "Overall data quality is poor. Consider comprehensive data cleaning."
            )
        elif quality_score < 80:
            recommendations.append(
                "Overall data quality is fair. Some cleaning recommended."
            )
        
        if not recommendations:
            recommendations.append("Data quality is good. Minimal cleaning needed.")
        
        return recommendations
    
    def clean_data(self, strategy: str = 'drop') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Clean the DataFrame based on specified strategy.
        
        Args:
            strategy: 'drop' (remove rows with missing values) or 'fill' (fill with mean/mode)
            
        Returns:
            Tuple of (cleaned DataFrame, cleaning report)
        """
        df_cleaned = self.df.copy()
        cleaning_report = {
            'original_rows': len(df_cleaned),
            'strategy': strategy,
            'changes': {}
        }
        
        if strategy == 'drop':
            df_cleaned = df_cleaned.dropna()
            cleaning_report['rows_removed'] = len(self.df) - len(df_cleaned)
            cleaning_report['changes']['dropped_rows'] = cleaning_report['rows_removed']
        
        elif strategy == 'fill':
            for column in df_cleaned.columns:
                if df_cleaned[column].isnull().sum() > 0:
                    if df_cleaned[column].dtype in ['float64', 'int64']:
                        fill_value = df_cleaned[column].mean()
                        df_cleaned[column].fillna(fill_value, inplace=True)
                        cleaning_report['changes'][column] = f"Filled with mean: {fill_value}"
                    else:
                        fill_value = df_cleaned[column].mode()[0] if len(df_cleaned[column].mode()) > 0 else 'Unknown'
                        df_cleaned[column].fillna(fill_value, inplace=True)
                        cleaning_report['changes'][column] = f"Filled with mode: {fill_value}"
        
        cleaning_report['final_rows'] = len(df_cleaned)
        
        return df_cleaned, cleaning_report

