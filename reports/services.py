"""
Report Generation Service Module

Provides utilities for generating reports and exporting data.
"""

import pandas as pd
from typing import Dict, Any, Tuple
from io import BytesIO
from datetime import datetime


class ReportGenerationService:
    """
    Service class for generating reports from survey data.
    
    Supports:
    - Summary statistics
    - Data export (CSV, Excel, JSON)
    - Report generation
    """
    
    def __init__(self, dataframe: pd.DataFrame, survey_name: str = "Survey"):
        """
        Initialize the service with a DataFrame.
        
        Args:
            dataframe: pandas DataFrame containing survey data
            survey_name: Name of the survey for report headers
        """
        self.df = dataframe
        self.survey_name = survey_name
        self.total_rows = len(dataframe)
        self.total_columns = len(dataframe.columns)
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary report of the survey data.
        
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'survey_name': self.survey_name,
            'generated_at': datetime.now().isoformat(),
            'record_count': self.total_rows,
            'column_count': self.total_columns,
            'columns': list(self.df.columns),
            'data_types': self._get_data_types(),
            'missing_values': self._get_missing_values(),
            'top_values': self._get_top_values(),
            'numeric_summary': self._get_numeric_summary()
        }
        
        return summary
    
    def _get_data_types(self) -> Dict[str, str]:
        """Get data types for all columns."""
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}
    
    def _get_missing_values(self) -> Dict[str, int]:
        """Get count of missing values per column."""
        return {col: int(self.df[col].isnull().sum()) for col in self.df.columns}
    
    def _get_top_values(self, n: int = 5) -> Dict[str, list]:
        """Get top N values for each column."""
        top_values = {}
        
        for column in self.df.columns:
            try:
                top = self.df[column].value_counts().head(n).to_dict()
                top_values[column] = [
                    {'value': k, 'count': int(v)} for k, v in top.items()
                ]
            except:
                top_values[column] = []
        
        return top_values
    
    def _get_numeric_summary(self) -> Dict[str, Dict[str, float]]:
        """Get numeric summary for numeric columns."""
        numeric_summary = {}
        
        for column in self.df.columns:
            try:
                numeric_data = pd.to_numeric(self.df[column], errors='coerce')
                if numeric_data.notna().sum() > 0:
                    numeric_summary[column] = {
                        'count': int(numeric_data.count()),
                        'mean': float(numeric_data.mean()),
                        'median': float(numeric_data.median()),
                        'std': float(numeric_data.std()),
                        'min': float(numeric_data.min()),
                        'max': float(numeric_data.max()),
                        'sum': float(numeric_data.sum())
                    }
            except:
                pass
        
        return numeric_summary
    
    def export_to_csv(self) -> Tuple[BytesIO, str]:
        """
        Export data to CSV format.
        
        Returns:
            Tuple of (BytesIO object, filename)
        """
        output = BytesIO()
        self.df.to_csv(output, index=False)
        output.seek(0)
        
        filename = f"{self.survey_name.replace(' ', '_')}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return output, filename
    
    def export_to_excel(self) -> Tuple[BytesIO, str]:
        """
        Export data to Excel format.
        
        Returns:
            Tuple of (BytesIO object, filename)
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write data sheet
            self.df.to_excel(writer, sheet_name='Data', index=False)
            
            # Write summary sheet
            summary = self.generate_summary()
            summary_df = pd.DataFrame([
                {'Metric': 'Record Count', 'Value': summary['record_count']},
                {'Metric': 'Column Count', 'Value': summary['column_count']},
                {'Metric': 'Generated At', 'Value': summary['generated_at']},
            ])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        filename = f"{self.survey_name.replace(' ', '_')}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return output, filename
    
    def export_to_json(self) -> Tuple[str, str]:
        """
        Export data to JSON format.
        
        Returns:
            Tuple of (JSON string, filename)
        """
        json_data = self.df.to_json(orient='records', indent=2)
        
        filename = f"{self.survey_name.replace(' ', '_')}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return json_data, filename
    
    def generate_filtered_report(
        self,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a report with filtered data.
        
        Args:
            filters: Dictionary of column:value pairs to filter data
            
        Returns:
            Dictionary containing filtered report
        """
        df_filtered = self.df.copy()
        
        if filters:
            for column, value in filters.items():
                if column in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[column] == value]
        
        # Create a new service with filtered data
        filtered_service = ReportGenerationService(df_filtered, self.survey_name)
        
        return {
            'original_records': self.total_rows,
            'filtered_records': len(df_filtered),
            'filters_applied': filters or {},
            'summary': filtered_service.generate_summary()
        }
    
    def generate_crosstab_report(
        self,
        row_column: str,
        col_column: str,
        values_column: str = None,
        aggfunc: str = 'count'
    ) -> Dict[str, Any]:
        """
        Generate a crosstab (pivot table) report.
        
        Args:
            row_column: Column to use for rows
            col_column: Column to use for columns
            values_column: Column to aggregate (optional)
            aggfunc: Aggregation function ('count', 'sum', 'mean', etc.)
            
        Returns:
            Dictionary containing crosstab data
        """
        try:
            if values_column:
                crosstab = pd.crosstab(
                    self.df[row_column],
                    self.df[col_column],
                    values=self.df[values_column],
                    aggfunc=aggfunc
                )
            else:
                crosstab = pd.crosstab(self.df[row_column], self.df[col_column])
            
            return {
                'row_column': row_column,
                'col_column': col_column,
                'values_column': values_column,
                'aggfunc': aggfunc,
                'data': crosstab.to_dict(),
                'shape': crosstab.shape
            }
        except Exception as e:
            return {
                'error': str(e),
                'row_column': row_column,
                'col_column': col_column
            }

