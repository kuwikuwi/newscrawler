import requests
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from urllib3.exceptions import InsecureRequestWarning
import urllib3

from ..config import Config
from ..utils import DateUtils, TextUtils, FileUtils

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

class BaseCrawler(ABC):
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.headers.update(Config.DEFAULT_HEADERS)
        
        # Configure session with better network handling
        adapter = requests.adapters.HTTPAdapter(
            max_retries=urllib3.util.retry.Retry(
                total=Config.MAX_RETRIES,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504, 429]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def make_request(self, url: str, params: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, use_rss_headers: bool = False) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        if use_rss_headers:
            request_headers = {**Config.RSS_HEADERS, **(headers or {})}
        else:
            request_headers = {**Config.DEFAULT_HEADERS, **(headers or {})}
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    params=params,
                    headers=request_headers,
                    timeout=Config.REQUEST_TIMEOUT,
                    verify=False
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.ConnectionError as e:
                print(f"Network connection failed (attempt {attempt + 1}/{Config.MAX_RETRIES}): {e}")
                print("Tip: Check your internet connection or try using a VPN")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (2 ** attempt))
                else:
                    print(f"Connection failed after {Config.MAX_RETRIES} attempts for URL: {url}")
                    return None
            except requests.exceptions.Timeout as e:
                print(f"Request timeout (attempt {attempt + 1}/{Config.MAX_RETRIES}): {e}")
                print("Tip: The server is taking too long to respond, retrying...")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (2 ** attempt))
                else:
                    print(f"Timeout after {Config.MAX_RETRIES} attempts for URL: {url}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{Config.MAX_RETRIES}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (2 ** attempt))
                else:
                    print(f"Max retries exceeded for URL: {url}")
                    return None
        
        return None
    
    def add_random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Add random delay to avoid being blocked"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def clean_and_validate_results(self) -> List[Dict[str, Any]]:
        """Clean and validate collected results"""
        return FileUtils.validate_data(self.results)
    
    def save_results(self, query: str) -> str:
        """Save results to Excel file"""
        if not self.results:
            raise ValueError("No results to save")
        
        clean_results = self.clean_and_validate_results()
        if not clean_results:
            raise ValueError("No valid results after cleaning")
        
        result_dir = Config.ensure_result_dir()
        return FileUtils.save_to_excel(clean_results, query, result_dir)
    
    def get_results_count(self) -> int:
        """Get number of collected results"""
        return len(self.results)
    
    def clear_results(self):
        """Clear collected results"""
        self.results.clear()
    
    @abstractmethod
    def crawl(self, query: str, max_pages: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Main crawling method - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the news source - must be implemented by subclasses"""
        pass