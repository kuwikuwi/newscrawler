import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent.parent
    RESULT_DIR = BASE_DIR / 'result'
    
    # Request configuration
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    RSS_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # Crawler settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 5
    RETRY_DELAY = 2
    
    # Google News settings
    GOOGLE_RSS_BASE_URL = 'https://news.google.com/rss'
    GOOGLE_SEARCH_PARAMS = {
        'hl': 'ko',
        'gl': 'KR',
        'ceid': 'KR:ko'
    }
    
    # Naver News settings
    NAVER_BASE_URL = 'https://search.naver.com/search.naver'
    NAVER_SEARCH_PARAMS = {
        'where': 'news',
        'sm': 'tab_jum',
        'sort': '0'
    }
    
    # Time range mappings
    TIME_RANGE_MAP = {
        '1': ('1h', '1시간'),
        '2': ('1d', '1일'),
        '3': ('1w', '1주'),
        '4': ('1m', '1개월'),
        '5': ('1y', '1년')
    }
    
    # Export settings
    EXCEL_COLUMNS = ['title', 'link', 'source', 'date', 'content']
    
    # Environment variables
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    
    @classmethod
    def ensure_result_dir(cls):
        cls.RESULT_DIR.mkdir(exist_ok=True)
        return cls.RESULT_DIR