# analytics/utils.py

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class PeriodHelper:
    """
    Handle DHIS2-style relative periods
    """
    
    @staticmethod
    def get_period_range(period_type: str):
        """
        Get date range for relative period
        """
        today = datetime.now()
        
        periods = {
            'TODAY': (today, today),
            'YESTERDAY': (today - timedelta(days=1), today - timedelta(days=1)),
            'LAST_7_DAYS': (today - timedelta(days=7), today),
            'LAST_14_DAYS': (today - timedelta(days=14), today),
            'LAST_30_DAYS': (today - timedelta(days=30), today),
            'THIS_MONTH': (today.replace(day=1), today),
            'LAST_MONTH': (
                (today.replace(day=1) - timedelta(days=1)).replace(day=1),
                today.replace(day=1) - timedelta(days=1)
            ),
            'LAST_3_MONTHS': (today - relativedelta(months=3), today),
            'LAST_6_MONTHS': (today - relativedelta(months=6), today),
            'LAST_12_MONTHS': (today - relativedelta(months=12), today),
            'THIS_YEAR': (today.replace(month=1, day=1), today),
            'LAST_YEAR': (
                today.replace(year=today.year-1, month=1, day=1),
                today.replace(year=today.year-1, month=12, day=31)
            ),
        }
        
        return periods.get(period_type, (today, today))