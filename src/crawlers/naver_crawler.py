from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base_crawler import BaseCrawler
from ..config import Config
from ..utils import DateUtils, TextUtils

class NaverNewsCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = Config.NAVER_BASE_URL
        
    def get_source_name(self) -> str:
        return "Naver News"
    
    def build_search_url(self, query: str, page: int = 1, sort: str = '0', 
                        start_date: str = '', end_date: str = '') -> str:
        """Build Naver news search URL"""
        params = {
            'where': 'news',
            'query': query,
            'sm': 'tab_opt',
            'sort': sort,  # 0: 관련도순, 1: 최신순, 2: 오래된순
            'photo': '0',
            'field': '0',
            'pd': '3',  # 전체기간
            'ds': start_date,
            'de': end_date,
            'start': (page - 1) * 10 + 1
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        param_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
        return f"{self.base_url}?{param_string}"
    
    def parse_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse Naver search results page"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Updated selector for current Naver structure
            news_items = soup.select('div.news_area')
            if not news_items:
                # Try alternative selectors
                news_items = soup.select('li.bx') or soup.select('div.group_news')
            
            results = []
            for item in news_items:
                try:
                    result = self.extract_article_info(item)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error parsing news item: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error parsing search results: {e}")
            return []
    
    def extract_article_info(self, item) -> Dict[str, Any]:
        """Extract article information from news item element"""
        try:
            # Title and link
            title_elem = (item.select_one('a.news_tit') or 
                         item.select_one('a.tit') or 
                         item.select_one('.tit a'))
            
            if not title_elem:
                return None
            
            title = TextUtils.extract_text_from_element(title_elem)
            link = title_elem.get('href', '')
            
            if not title or not link:
                return None
            
            # Source (news agency)
            source_elem = (item.select_one('.press') or 
                          item.select_one('.cp') or 
                          item.select_one('.info_group .press'))
            
            source = TextUtils.extract_text_from_element(source_elem) if source_elem else ""
            source = TextUtils.normalize_source_name(source)
            
            # Date
            date_elem = (item.select_one('.info_group .info') or 
                        item.select_one('.info') or 
                        item.select_one('.date'))
            
            date_str = TextUtils.extract_text_from_element(date_elem) if date_elem else ""
            date = DateUtils.parse_relative_date(date_str)
            
            # Content summary
            content_elem = (item.select_one('.news_dsc') or 
                           item.select_one('.dsc') or 
                           item.select_one('.api_txt_lines'))
            
            content = TextUtils.extract_text_from_element(content_elem) if content_elem else ""
            content = TextUtils.truncate_text(content, 200)
            
            return {
                'title': title,
                'link': link,
                'source': source,
                'date': date,
                'content': content
            }
            
        except Exception as e:
            print(f"Error extracting article info: {e}")
            return None
    
    def crawl_page(self, query: str, page: int, sort: str = '0', 
                   start_date: str = '', end_date: str = '') -> List[Dict[str, Any]]:
        """Crawl a single page of results"""
        url = self.build_search_url(query, page, sort, start_date, end_date)
        print(f"Crawling page {page}: {url}")
        
        response = self.make_request(url)
        if not response:
            print(f"Failed to fetch page {page}")
            return []
        
        results = self.parse_search_results(response.text)
        print(f"Page {page}: Found {len(results)} articles")
        
        # Add delay between requests
        self.add_random_delay(1.0, 3.0)
        
        return results
    
    def crawl(self, query: str, max_pages: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Main crawling method"""
        sort = kwargs.get('sort', '0')  # 0: 관련성, 1: 최신순
        start_date = kwargs.get('start_date', '')
        end_date = kwargs.get('end_date', '')
        
        self.clear_results()
        
        print(f"Starting Naver news crawl for query: '{query}'")
        print(f"Max pages: {max_pages}, Sort: {sort}")
        
        for page in range(1, max_pages + 1):
            try:
                page_results = self.crawl_page(query, page, sort, start_date, end_date)
                
                if not page_results:
                    print(f"No results found on page {page}, stopping crawl")
                    break
                
                self.results.extend(page_results)
                print(f"Total articles collected: {len(self.results)}")
                
            except Exception as e:
                print(f"Error crawling page {page}: {e}")
                continue
        
        print(f"Naver crawl completed. Total articles: {len(self.results)}")
        return self.results