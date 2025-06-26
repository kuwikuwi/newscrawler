import re
from typing import Optional

class TextUtils:
    @staticmethod
    def clean_html(content: str) -> str:
        """Remove HTML tags and clean text content"""
        if not content:
            return ""
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', str(content))
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', ' ', content)
        
        # Remove special characters and normalize
        content = content.replace('\xa0', ' ')  # Non-breaking space
        content = content.replace('\u200b', '')  # Zero-width space
        content = content.replace('&quot;', '"')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        
        return content.strip()
    
    @staticmethod
    def extract_text_from_element(element) -> str:
        """Extract clean text from BeautifulSoup element"""
        if element is None:
            return ""
        
        if hasattr(element, 'get_text'):
            return TextUtils.clean_html(element.get_text())
        
        return TextUtils.clean_html(str(element))
    
    @staticmethod
    def normalize_source_name(source: str) -> str:
        """Normalize news source names"""
        if not source:
            return ""
        
        # Common source mappings
        source_map = {
            '연합뉴스': '연합뉴스',
            'Yonhap News': '연합뉴스',
            '조선일보': '조선일보',
            'Chosun': '조선일보',
            '중앙일보': '중앙일보',
            'JoongAng': '중앙일보',
            'KBS': 'KBS',
            'MBC': 'MBC',
            'SBS': 'SBS'
        }
        
        source = source.strip()
        return source_map.get(source, source)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 200) -> str:
        """Truncate text to specified length"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """Extract domain name from URL for source identification"""
        if not url:
            return ""
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        
        # Extract domain
        domain_match = re.match(r'^([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            
            # Remove www
            domain = re.sub(r'^www\.', '', domain)
            
            # Extract main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[-2]
        
        return ""