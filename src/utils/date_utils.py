import re
from datetime import datetime, timedelta
from typing import Optional

class DateUtils:
    @staticmethod
    def parse_relative_date(date_str: str) -> str:
        """Parse relative date strings and convert to standard format"""
        if not date_str:
            return datetime.now().strftime('%Y.%m.%d.')
            
        now = datetime.now()
        date_str = date_str.strip()
        
        try:
            # Absolute date patterns
            if match := re.search(r'\d{4}\.\d{1,2}\.\d{1,2}\.?', date_str):
                return match.group(0).rstrip('.') + '.'
            if match := re.search(r'\d{1,2}\.\d{1,2}\.\d{1,2}\.?', date_str):
                return match.group(0).rstrip('.') + '.'
            
            # Korean relative dates
            if '일 전' in date_str or '일전' in date_str:
                days = int(re.search(r'(\d+)일\s*전', date_str).group(1))
                return (now - timedelta(days=days)).strftime('%Y.%m.%d.')
            
            if '시간 전' in date_str or '시간전' in date_str:
                hours = int(re.search(r'(\d+)시간\s*전', date_str).group(1))
                return (now - timedelta(hours=hours)).strftime('%Y.%m.%d.')
            
            if '분 전' in date_str or '분전' in date_str:
                minutes = int(re.search(r'(\d+)분\s*전', date_str).group(1))
                return (now - timedelta(minutes=minutes)).strftime('%Y.%m.%d.')
            
            # English relative dates
            if match := re.search(r'(\d+)\s*hours?\s*ago', date_str, re.IGNORECASE):
                hours = int(match.group(1))
                return (now - timedelta(hours=hours)).strftime('%Y.%m.%d.')
            
            if match := re.search(r'(\d+)\s*days?\s*ago', date_str, re.IGNORECASE):
                days = int(match.group(1))
                return (now - timedelta(days=days)).strftime('%Y.%m.%d.')
            
            if match := re.search(r'(\d+)\s*minutes?\s*ago', date_str, re.IGNORECASE):
                minutes = int(match.group(1))
                return (now - timedelta(minutes=minutes)).strftime('%Y.%m.%d.')
                
        except (ValueError, AttributeError):
            pass
        
        return now.strftime('%Y.%m.%d.')
    
    @staticmethod
    def parse_rss_date(date_str: str) -> str:
        """Parse RSS date formats to standard format"""
        if not date_str:
            return datetime.now().strftime('%Y.%m.%d.')
        
        formats = [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S',
            '%d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y.%m.%d.')
            except ValueError:
                continue
        
        return DateUtils.parse_relative_date(date_str)
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp for file naming"""
        return datetime.now().strftime('%Y-%m-%d %H시 %M분 %S초')