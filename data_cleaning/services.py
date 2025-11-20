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

    def get_preview_data(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        Get paginated preview of the DataFrame.

        Args:
            page: Page number (1-indexed)
            page_size: Number of rows per page

        Returns:
            Dictionary with paginated data and metadata
        """
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Get the page data
        page_data = self.df.iloc[start_idx:end_idx]

        # Convert to list of dictionaries, replacing NaN/inf with None for JSON serialization
        # First replace inf and -inf with NaN, then replace all NaN with None
        page_data_clean = page_data.replace([np.inf, -np.inf], np.nan)

        # Convert to dict and replace NaN with None
        # Using orient='records' and then manually replacing NaN ensures JSON compatibility
        import json
        records_json = page_data_clean.to_json(orient='records', date_format='iso')
        records = json.loads(records_json)

        # Get column info
        columns = []
        for col in self.df.columns:
            columns.append({
                'name': col,
                'type': str(self.df[col].dtype),
                'non_null_count': int(self.df[col].count()),
                'null_count': int(self.df[col].isnull().sum()),
                'unique_count': int(self.df[col].nunique())
            })

        total_pages = (len(self.df) + page_size - 1) // page_size

        return {
            'data': records,
            'columns': columns,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_rows': len(self.df),
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        }

    def remove_columns(self, columns: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Remove specified columns from the DataFrame.

        Args:
            columns: List of column names to remove

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()
        removed = []
        not_found = []

        for col in columns:
            if col in df_modified.columns:
                df_modified = df_modified.drop(columns=[col])
                removed.append(col)
            else:
                not_found.append(col)

        report = {
            'operation': 'remove_columns',
            'removed_columns': removed,
            'not_found_columns': not_found,
            'columns_before': len(self.df.columns),
            'columns_after': len(df_modified.columns)
        }

        return df_modified, report

    def add_column(self, column_name: str, default_value: Any = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Add a new column to the DataFrame.

        Args:
            column_name: Name of the new column
            default_value: Default value for the column

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()

        if column_name in df_modified.columns:
            return df_modified, {
                'operation': 'add_column',
                'success': False,
                'error': f"Column '{column_name}' already exists"
            }

        df_modified[column_name] = default_value

        report = {
            'operation': 'add_column',
            'success': True,
            'column_name': column_name,
            'default_value': default_value,
            'columns_after': len(df_modified.columns)
        }

        return df_modified, report

    def rename_column(self, old_name: str, new_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Rename a column in the DataFrame.

        Args:
            old_name: Current column name
            new_name: New column name

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()

        if old_name not in df_modified.columns:
            return df_modified, {
                'operation': 'rename_column',
                'success': False,
                'error': f"Column '{old_name}' not found"
            }

        if new_name in df_modified.columns:
            return df_modified, {
                'operation': 'rename_column',
                'success': False,
                'error': f"Column '{new_name}' already exists"
            }

        df_modified = df_modified.rename(columns={old_name: new_name})

        report = {
            'operation': 'rename_column',
            'success': True,
            'old_name': old_name,
            'new_name': new_name
        }

        return df_modified, report

    def remove_duplicates(self, subset: List[str] = None, keep: str = 'first') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Remove duplicate rows from the DataFrame.

        Args:
            subset: List of columns to consider for identifying duplicates (None = all columns)
            keep: Which duplicates to keep ('first', 'last', or False to remove all)

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()
        rows_before = len(df_modified)

        # Check if subset columns exist
        if subset:
            missing_cols = [col for col in subset if col not in df_modified.columns]
            if missing_cols:
                return df_modified, {
                    'operation': 'remove_duplicates',
                    'success': False,
                    'error': f"Columns not found: {missing_cols}"
                }

        df_modified = df_modified.drop_duplicates(subset=subset, keep=keep)
        rows_after = len(df_modified)
        duplicates_removed = rows_before - rows_after

        report = {
            'operation': 'remove_duplicates',
            'success': True,
            'rows_before': rows_before,
            'rows_after': rows_after,
            'duplicates_removed': duplicates_removed,
            'subset_columns': subset if subset else 'all columns',
            'keep_strategy': keep
        }

        return df_modified, report

    def handle_missing_values(
        self,
        strategy: str,
        columns: List[str] = None,
        fill_value: Any = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing values in the DataFrame.

        Args:
            strategy: 'drop_rows', 'drop_columns', 'fill_mean', 'fill_median', 'fill_mode', 'fill_value', 'forward_fill', 'backward_fill'
            columns: List of columns to apply the strategy to (None = all columns)
            fill_value: Custom value to fill (only used with 'fill_value' strategy)

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()
        changes = {}

        target_columns = columns if columns else list(df_modified.columns)

        # Validate columns
        missing_cols = [col for col in target_columns if col not in df_modified.columns]
        if missing_cols:
            return df_modified, {
                'operation': 'handle_missing_values',
                'success': False,
                'error': f"Columns not found: {missing_cols}"
            }

        rows_before = len(df_modified)

        if strategy == 'drop_rows':
            df_modified = df_modified.dropna(subset=target_columns)
            changes['rows_dropped'] = rows_before - len(df_modified)

        elif strategy == 'drop_columns':
            df_modified = df_modified.drop(columns=target_columns)
            changes['columns_dropped'] = target_columns

        elif strategy == 'fill_mean':
            for col in target_columns:
                if df_modified[col].dtype in ['float64', 'int64']:
                    mean_val = df_modified[col].mean()
                    null_count = df_modified[col].isnull().sum()
                    df_modified[col].fillna(mean_val, inplace=True)
                    changes[col] = f"Filled {null_count} values with mean: {mean_val:.2f}"

        elif strategy == 'fill_median':
            for col in target_columns:
                if df_modified[col].dtype in ['float64', 'int64']:
                    median_val = df_modified[col].median()
                    null_count = df_modified[col].isnull().sum()
                    df_modified[col].fillna(median_val, inplace=True)
                    changes[col] = f"Filled {null_count} values with median: {median_val:.2f}"

        elif strategy == 'fill_mode':
            for col in target_columns:
                if len(df_modified[col].mode()) > 0:
                    mode_val = df_modified[col].mode()[0]
                    null_count = df_modified[col].isnull().sum()
                    df_modified[col].fillna(mode_val, inplace=True)
                    changes[col] = f"Filled {null_count} values with mode: {mode_val}"

        elif strategy == 'fill_value':
            for col in target_columns:
                null_count = df_modified[col].isnull().sum()
                df_modified[col].fillna(fill_value, inplace=True)
                changes[col] = f"Filled {null_count} values with: {fill_value}"

        elif strategy == 'forward_fill':
            for col in target_columns:
                null_count = df_modified[col].isnull().sum()
                df_modified[col].fillna(method='ffill', inplace=True)
                changes[col] = f"Forward filled {null_count} values"

        elif strategy == 'backward_fill':
            for col in target_columns:
                null_count = df_modified[col].isnull().sum()
                df_modified[col].fillna(method='bfill', inplace=True)
                changes[col] = f"Backward filled {null_count} values"

        else:
            return df_modified, {
                'operation': 'handle_missing_values',
                'success': False,
                'error': f"Unknown strategy: {strategy}"
            }

        report = {
            'operation': 'handle_missing_values',
            'success': True,
            'strategy': strategy,
            'rows_before': rows_before,
            'rows_after': len(df_modified),
            'changes': changes
        }

        return df_modified, report

    def find_replace(
        self,
        column: str,
        find_value: Any,
        replace_value: Any,
        use_regex: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Find and replace values in a column.

        Args:
            column: Column name to perform find/replace
            find_value: Value to find
            replace_value: Value to replace with
            use_regex: Whether to use regex for finding

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()

        if column not in df_modified.columns:
            return df_modified, {
                'operation': 'find_replace',
                'success': False,
                'error': f"Column '{column}' not found"
            }

        # Count replacements
        if use_regex:
            matches = df_modified[column].astype(str).str.contains(str(find_value), regex=True, na=False).sum()
            df_modified[column] = df_modified[column].astype(str).str.replace(str(find_value), str(replace_value), regex=True)
        else:
            matches = (df_modified[column] == find_value).sum()
            df_modified[column] = df_modified[column].replace(find_value, replace_value)

        report = {
            'operation': 'find_replace',
            'success': True,
            'column': column,
            'find_value': str(find_value),
            'replace_value': str(replace_value),
            'replacements_made': int(matches),
            'use_regex': use_regex
        }

        return df_modified, report

    def standardize_data(
        self,
        columns: List[str],
        operations: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Standardize data in specified columns.

        Args:
            columns: List of column names to standardize
            operations: List of operations ('trim', 'lowercase', 'uppercase', 'title_case', 'remove_special_chars')

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()
        changes = {}

        # Validate columns
        missing_cols = [col for col in columns if col not in df_modified.columns]
        if missing_cols:
            return df_modified, {
                'operation': 'standardize_data',
                'success': False,
                'error': f"Columns not found: {missing_cols}"
            }

        for col in columns:
            col_changes = []

            # Convert to string for text operations
            df_modified[col] = df_modified[col].astype(str)

            if 'trim' in operations:
                df_modified[col] = df_modified[col].str.strip()
                col_changes.append('trimmed whitespace')

            if 'lowercase' in operations:
                df_modified[col] = df_modified[col].str.lower()
                col_changes.append('converted to lowercase')

            if 'uppercase' in operations:
                df_modified[col] = df_modified[col].str.upper()
                col_changes.append('converted to uppercase')

            if 'title_case' in operations:
                df_modified[col] = df_modified[col].str.title()
                col_changes.append('converted to title case')

            if 'remove_special_chars' in operations:
                df_modified[col] = df_modified[col].str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
                col_changes.append('removed special characters')

            changes[col] = ', '.join(col_changes)

        report = {
            'operation': 'standardize_data',
            'success': True,
            'columns': columns,
            'operations': operations,
            'changes': changes
        }

        return df_modified, report

    def create_variable(
        self,
        new_column: str,
        expression: str = None,
        source_columns: List[str] = None,
        operation: str = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Create a new variable/column based on existing columns.

        Args:
            new_column: Name of the new column to create
            expression: Python expression to evaluate (e.g., "col1 + col2")
            source_columns: List of source columns for simple operations
            operation: Simple operation ('sum', 'mean', 'concat', 'multiply')

        Returns:
            Tuple of (modified DataFrame, operation report)
        """
        df_modified = self.df.copy()

        if new_column in df_modified.columns:
            return df_modified, {
                'operation': 'create_variable',
                'success': False,
                'error': f"Column '{new_column}' already exists"
            }

        try:
            if expression:
                # Evaluate expression (be careful with security in production!)
                df_modified[new_column] = df_modified.eval(expression)
                method = f"expression: {expression}"

            elif source_columns and operation:
                # Validate source columns
                missing_cols = [col for col in source_columns if col not in df_modified.columns]
                if missing_cols:
                    return df_modified, {
                        'operation': 'create_variable',
                        'success': False,
                        'error': f"Source columns not found: {missing_cols}"
                    }

                if operation == 'sum':
                    df_modified[new_column] = df_modified[source_columns].sum(axis=1)
                elif operation == 'mean':
                    df_modified[new_column] = df_modified[source_columns].mean(axis=1)
                elif operation == 'concat':
                    df_modified[new_column] = df_modified[source_columns].astype(str).agg(' '.join, axis=1)
                elif operation == 'multiply':
                    df_modified[new_column] = df_modified[source_columns].prod(axis=1)
                else:
                    return df_modified, {
                        'operation': 'create_variable',
                        'success': False,
                        'error': f"Unknown operation: {operation}"
                    }

                method = f"{operation} of {source_columns}"

            else:
                return df_modified, {
                    'operation': 'create_variable',
                    'success': False,
                    'error': "Either expression or (source_columns + operation) must be provided"
                }

            report = {
                'operation': 'create_variable',
                'success': True,
                'new_column': new_column,
                'method': method,
                'columns_after': len(df_modified.columns)
            }

            return df_modified, report

        except Exception as e:
            return df_modified, {
                'operation': 'create_variable',
                'success': False,
                'error': str(e)
            }