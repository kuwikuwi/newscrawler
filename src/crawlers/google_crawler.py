import re
from urllib.parse import quote, unquote, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

from .base_crawler import BaseCrawler
from ..config import Config
from ..utils import DateUtils, TextUtils

class GoogleNewsCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.base_rss_url = Config.GOOGLE_RSS_BASE_URL
        
    def get_source_name(self) -> str:
        return "Google News"
    
    def build_rss_url(self, query: str, language: str = 'ko', region: str = 'KR') -> str:
        """Build Google News RSS URL"""
        encoded_query = quote(query)
        
        # RSS search URL
        if language == 'ko':
            url = f"{self.base_rss_url}/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = f"{self.base_rss_url}/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"
            
        return url
    
    def extract_real_url(self, google_url: str) -> str:
        """Extract real URL from Google redirect URL"""
        if not google_url:
            return ""
        
        # Handle different Google URL formats
        if 'google.com/url?q=' in google_url:
            try:
                real_url = google_url.split('google.com/url?q=')[1].split('&')[0]
                return unquote(real_url)
            except:
                pass
        
        if 'news.google.com' in google_url and '/articles/' in google_url:
            # For Google News article URLs, try to extract the original URL
            try:
                response = self.make_request(google_url, use_rss_headers=True)
                if response and response.url != google_url:
                    return response.url
            except:
                pass
        
        return google_url
    
    def extract_source_from_title(self, title: str) -> tuple:
        """Extract source and clean title from title string"""
        if not title:
            return "", ""
        
        # Pattern: "Title - Source"
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        # Pattern: "Title | Source"
        if ' | ' in title:
            parts = title.rsplit(' | ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        return title.strip(), ""
    
    def parse_rss_feed(self, rss_content: str) -> List[Dict[str, Any]]:
        """Parse RSS feed content"""
        try:
            soup = BeautifulSoup(rss_content, 'xml')
            items = soup.find_all('item')
            
            results = []
            for item in items:
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pub_date_elem = item.find('pubDate')
                    description_elem = item.find('description')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    raw_title = TextUtils.extract_text_from_element(title_elem)
                    clean_title, source = self.extract_source_from_title(raw_title)
                    
                    raw_link = TextUtils.extract_text_from_element(link_elem)
                    real_link = self.extract_real_url(raw_link)
                    
                    # Extract source from URL if not found in title
                    if not source:
                        source = TextUtils.extract_domain_from_url(real_link)
                        source = TextUtils.normalize_source_name(source)
                    
                    pub_date = DateUtils.parse_rss_date(
                        TextUtils.extract_text_from_element(pub_date_elem)
                    )
                    
                    content = TextUtils.extract_text_from_element(description_elem)
                    content = TextUtils.truncate_text(content, 300)
                    
                    result = {
                        'title': clean_title,
                        'link': real_link,
                        'source': source,
                        'date': pub_date,
                        'content': content
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error parsing RSS item: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error parsing RSS feed: {e}")
            return []
    
    def crawl_rss(self, query: str, language: str = 'ko', max_results: int = 100) -> List[Dict[str, Any]]:
        """Crawl Google News via RSS"""
        rss_url = self.build_rss_url(query, language)
        print(f"Fetching RSS from: {rss_url}")
        
        response = self.make_request(rss_url, use_rss_headers=True)
        if not response:
            print("Failed to fetch RSS feed")
            return []
        
        results = self.parse_rss_feed(response.text)
        
        # Limit results
        if max_results and len(results) > max_results:
            results = results[:max_results]
        
        print(f"Found {len(results)} articles")
        return results
    
    def crawl_with_time_range(self, query: str, time_range: str = '1d', 
                             language: str = 'ko', max_results: int = 100) -> List[Dict[str, Any]]:
        """Crawl with specific time range"""
        # Add time range to query
        time_query = f"{query} when:{time_range}"
        return self.crawl_rss(time_query, language, max_results)
    
    def crawl(self, query: str, max_pages: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """Main crawling method"""
        language = kwargs.get('language', 'ko')
        time_range = kwargs.get('time_range', '1d')
        max_results = kwargs.get('max_results', 100)
        
        self.clear_results()
        
        if time_range:
            results = self.crawl_with_time_range(query, time_range, language, max_results)
        else:
            results = self.crawl_rss(query, language, max_results)
        
        self.results.extend(results)
        return self.results