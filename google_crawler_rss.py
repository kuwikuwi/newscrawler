from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import pandas as pd
import re
from urllib.parse import quote, urlparse
import urllib3
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
< Google News RSS Feed Crawler >
- Uses Google News RSS feed to avoid 429 errors
- Maintains same output format as original crawler
- Saves results to Excel file
'''

# Lists to store crawling results
query_text = []
title_text = []
link_text = []
source_text = []
date_text = []

# Path to save Excel file
RESULT_PATH = 'C:/Users/kibae/Desktop/google_news_crawling/result'
now = datetime.now()

def parse_rss_date(date_str):
    """Convert RSS date format to Korean format"""
    try:
        # RSS date format: 'Mon, 30 May 2025 10:30:00 GMT'
        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
        return date_obj.strftime('%Y.%m.%d.')
    except:
        try:
            # Try alternative format
            date_obj = datetime.strptime(date_str[:16], '%a, %d %b %Y')
            return date_obj.strftime('%Y.%m.%d.')
        except:
            return datetime.now().strftime('%Y.%m.%d.')

def extract_source_from_title(title):
    """Extract source from title if available"""
    # Google News often includes source in title like "Title - Source"
    if ' - ' in title:
        parts = title.rsplit(' - ', 1)
        if len(parts) == 2 and len(parts[1]) < 50:  # Likely a source name
            return parts[1], parts[0]  # Return source and cleaned title
    return None, title

def extract_source_from_url(url):
    """Extract source from URL"""
    try:
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        # Remove common TLDs
        source = domain.split('.')[0]
        # Capitalize first letter
        return source.capitalize()
    except:
        return "Unknown"

def get_real_url(google_url):
    """Extract real URL from Google's redirect URL"""
    try:
        # Google News RSS often uses redirect URLs
        if 'google.com/rss/articles' in google_url:
            # Try to get the real URL by following redirect
            response = requests.head(google_url, allow_redirects=True, timeout=5, verify=False)
            return response.url
        return google_url
    except:
        return google_url

def crawler(maxitems, query, time_range=None, language='en'):
    """Main crawler function using RSS feed"""
    # Clear previous results
    query_text.clear()
    title_text.clear()
    link_text.clear()
    source_text.clear()
    date_text.clear()
    
    # Convert maxitems to integer
    max_items = int(maxitems) * 10  # Similar to original pages * items_per_page
    
    # Encode query for URL
    encoded_query = quote(query)
    
    # Language mapping for Google News
    language_map = {
        'en': 'en-US',
        'ko': 'ko-KR',
        'ja': 'ja-JP',
        'zh': 'zh-CN',
        'de': 'de-DE',
        'fr': 'fr-FR',
        'es': 'es-ES'
    }
    
    hl = language_map.get(language, 'en-US')
    gl = hl.split('-')[1] if '-' in hl else 'US'
    
    # Time range parameter for RSS
    # Google News RSS doesn't support time range directly, but we can filter later
    time_filter_days = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }
    
    filter_days = time_filter_days.get(time_range, None)
    cutoff_date = datetime.now() - timedelta(days=filter_days) if filter_days else None
    
    # RSS feed URLs to try
    rss_urls = [
        f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{language}",
        f"https://news.google.com/rss/search?q={encoded_query}&hl={language}",
        f"https://news.google.com/rss/search?q={encoded_query}"
    ]
    
    print(f"Searching for: '{query}'")
    if time_range and time_range != 'all':
        print(f"Time range: {time_range}")
    print(f"Language: {language}")
    print(f"Using RSS feed method (no 429 errors)")
    
    items_found = 0
    
    for rss_url in rss_urls:
        if items_found >= max_items:
            break
            
        print(f"\nTrying RSS feed: {rss_url[:50]}...")
        
        try:
            # Headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': f'{language},{language}-{gl};q=0.9,en;q=0.8',
            }
            
            response = requests.get(rss_url, headers=headers, timeout=30, verify=False)
            
            if response.status_code != 200:
                print(f"Failed to fetch RSS feed. Status code: {response.status_code}")
                continue
            
            # Parse RSS feed
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            if not items:
                print("No items found in RSS feed")
                continue
            
            print(f"Found {len(items)} items in RSS feed")
            
            for item in items:
                if items_found >= max_items:
                    break
                
                # Extract basic information
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source_tag = item.find('source')
                
                if not title or not link:
                    continue
                
                title_text_raw = title.text.strip()
                link_text_raw = link.text.strip()
                
                # Parse date
                if pub_date:
                    date_parsed = parse_rss_date(pub_date.text)
                    
                    # Filter by date if time_range is specified
                    if cutoff_date:
                        try:
                            item_date = datetime.strptime(date_parsed, '%Y.%m.%d.')
                            if item_date < cutoff_date:
                                continue  # Skip items older than cutoff
                        except:
                            pass
                else:
                    date_parsed = datetime.now().strftime('%Y.%m.%d.')
                
                # Extract source
                source_name = None
                cleaned_title = title_text_raw
                
                # First try: from source tag
                if source_tag:
                    source_name = source_tag.text.strip()
                
                # Second try: from title
                if not source_name:
                    source_from_title, cleaned_title = extract_source_from_title(title_text_raw)
                    if source_from_title:
                        source_name = source_from_title
                
                # Third try: from URL
                if not source_name:
                    source_name = extract_source_from_url(link_text_raw)
                
                # Get real URL (follow redirects if needed)
                real_url = get_real_url(link_text_raw)
                
                # Append to results
                query_text.append(query)
                title_text.append(cleaned_title)
                link_text.append(real_url)
                date_text.append(date_parsed)
                source_text.append(source_name)
                
                items_found += 1
            
            print(f"Processed {items_found} items so far")
            
        except Exception as e:
            print(f"Error processing RSS feed: {e}")
            continue
    
    if items_found == 0:
        print("\nNo articles found. Trying alternative approach...")
        # Fallback to regular search with very careful parameters
        return crawler_fallback(maxitems, query, time_range, language)
    
    # Create result dictionary
    result = {
        "검색 키워드": query_text,
        "제목": title_text,
        "URL": link_text,
        "날짜": date_text,
        "출처": source_text,
    }
    
    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(result)
    
    # Remove duplicates based on title
    df = df.drop_duplicates(subset=['제목'], keep='first')
    
    # Create directory if it doesn't exist
    if not os.path.exists(RESULT_PATH):
        os.makedirs(RESULT_PATH)
    
    # Generate output filename
    outputFileName = f'{now.year}-{now.month}-{now.day} {now.hour}시 {now.minute}분 {now.second}초 {query}.xlsx'
    output_path = os.path.join(RESULT_PATH, outputFileName)
    
    # Save to Excel
    df.to_excel(output_path, sheet_name='sheet1', index=False)
    print(f"\nCrawling complete. Results saved to {output_path}")
    print(f"Total articles: {len(df)} (after removing duplicates)")
    
    # Preview
    print("\n[Preview of results]")
    for i, row in df.head(5).iterrows():
        print(f"{i+1}. {row['제목'][:60]}...")
        print(f"   Source: {row['출처']}, Date: {row['날짜']}")
    
    return df

def crawler_fallback(maxitems, query, time_range, language):
    """Fallback method using alternative news sources"""
    print("\nUsing fallback method...")
    
    # Try DuckDuckGo news search (no rate limits)
    encoded_query = quote(query)
    ddg_url = f"https://duckduckgo.com/html/?q={encoded_query}+news&iar=news"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(ddg_url, headers=headers, timeout=30, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.select('.result')
            
            for result in results[:int(maxitems) * 10]:
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')
                
                if title_elem and link_elem:
                    query_text.append(query)
                    title_text.append(title_elem.get_text(strip=True))
                    
                    # Extract URL
                    url = link_elem.get('href', '')
                    if not url.startswith('http'):
                        url = 'https://' + link_elem.get_text(strip=True)
                    link_text.append(url)
                    
                    date_text.append(datetime.now().strftime('%Y.%m.%d.'))
                    source_text.append(extract_source_from_url(url))
    except Exception as e:
        print(f"Fallback method error: {e}")
    
    # Create DataFrame and save
    if query_text:
        result = {
            "검색 키워드": query_text,
            "제목": title_text,
            "URL": link_text,
            "날짜": date_text,
            "출처": source_text,
        }
        
        df = pd.DataFrame(result)
        df = df.drop_duplicates(subset=['제목'], keep='first')
        
        if not os.path.exists(RESULT_PATH):
            os.makedirs(RESULT_PATH)
        
        outputFileName = f'{now.year}-{now.month}-{now.day} {now.hour}시 {now.minute}분 {now.second}초 {query}.xlsx'
        output_path = os.path.join(RESULT_PATH, outputFileName)
        df.to_excel(output_path, sheet_name='sheet1', index=False)
        
        print(f"\nFallback complete. Results saved to {output_path}")
        return df
    else:
        print("\nNo results found even with fallback method.")
        return None

def main():
    print("="*50)
    print("Google News RSS Feed Crawler")
    print("="*50)
    
    maxpage = input("Maximum number of pages to crawl (will be converted to items): ")
    query = input("Search term: ")
    
    time_range_options = {
        '1': 'day',
        '2': 'week',
        '3': 'month',
        '4': 'year',
        '5': 'all'
    }
    
    print("\nTime range options:")
    for key, value in time_range_options.items():
        print(f"{key}. {value.capitalize()}")
    
    time_choice = input("Select time range (default is all): ")
    time_range = time_range_options.get(time_choice, 'all')
    
    language = input("Language code (e.g., 'en' for English, 'ko' for Korean, default is 'en'): ") or "en"
    
    print("\nStarting RSS feed crawler...")
    print("Note: RSS feed method avoids 429 errors!")
    
    crawler(maxpage, query, time_range, language)

if __name__ == "__main__":
    main()