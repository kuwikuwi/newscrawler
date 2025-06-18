# --- START OF FILE google_news_rss_crawler.py ---

import feedparser
import requests # Still useful for fetching the RSS feed itself with headers
from bs4 import BeautifulSoup # For cleaning HTML content in descriptions
from datetime import datetime, timedelta
import pandas as pd
import os
import re
from urllib.parse import quote
from dateutil import parser as date_parser # For robust date parsing

# Disable SSL warnings - generally not needed for RSS fetching, but good practice from your other script
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
< Google News RSS Feed Crawler >
- Crawls: link, title, source (publisher), published date, content snippet (summary)
- Processes and cleans date and content
- Saves results to Excel file
- More resilient to Google blocking than direct search scraping
'''

# Path to save Excel file
RESULT_PATH = 'C:/Users/kibae/Desktop/google_news_crawling/result'  # Change to your desired path
# Ensure the directory exists
if not os.path.exists(RESULT_PATH):
    try:
        os.makedirs(RESULT_PATH)
        print(f"Created directory: {RESULT_PATH}")
    except OSError as e:
        print(f"Error creating directory {RESULT_PATH}: {e}. Please create it manually.")
        # exit() # Or handle more gracefully

# Date formatting function (RSS usually provides proper date strings)
def format_rss_date(date_string_or_struct):
    """
    Formats a date string or time.struct_time from feedparser into YYYY.MM.DD.
    """
    if not date_string_or_struct:
        return datetime.now().strftime('%Y.%m.%d.')
    try:
        if isinstance(date_string_or_struct, str):
            # Use dateutil.parser for flexibility with various date formats in RSS
            dt_obj = date_parser.parse(date_string_or_struct)
        elif hasattr(date_string_or_struct, 'tm_year'): # Check if it's a time.struct_time
            dt_obj = datetime(*date_string_or_struct[:6])
        else:
            # Fallback or raise error
            print(f"Unknown date type: {type(date_string_or_struct)}. Using current date.")
            return datetime.now().strftime('%Y.%m.%d.')
        return dt_obj.strftime('%Y.%m.%d.')
    except Exception as e:
        print(f"Date conversion error for RSS date: {e} - Input: {date_string_or_struct}")
        return datetime.now().strftime('%Y.%m.%d.')

# Content cleaning function (similar to your original)
def contents_cleansing(html_content):
    if html_content:
        # Use BeautifulSoup to parse HTML and get text
        soup = BeautifulSoup(html_content, 'html.parser')
        cleaned_content = soup.get_text(separator=' ', strip=True)
        # Remove extra whitespace (optional, as get_text with strip=True handles much of this)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
        return cleaned_content
    return ""

def crawler_rss(query, language='en', country_code='US', max_articles_approx=100):
    """
    Crawls Google News RSS feed for a given query.
    Note: RSS feeds typically don't have 'pages'. They return a set of recent articles.
    'max_articles_approx' is just to limit processing if feed is very long, but one fetch gets all.
    """
    # Lists to store crawling results for this run
    title_text_rss = []
    link_text_rss = []
    source_text_rss = []
    date_text_rss = []
    contents_text_rss = []

    encoded_query = quote(query)
    
    # Construct RSS feed URL
    # Example: https://news.google.com/rss/search?q=AI&hl=en-US&gl=US&ceid=US:en
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}-{country_code.upper()}&gl={country_code.upper()}&ceid={country_code.upper()}:{language}"
    
    print(f"Fetching RSS feed from: {rss_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        # Using requests to fetch, as it allows headers and timeout
        response = requests.get(rss_url, headers=headers, timeout=30, verify=True) # verify=True is safer
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        # feedparser can take the response content directly
        feed = feedparser.parse(response.content)

        if feed.bozo: # bozo is 1 if feed is not well-formed
            bozo_exception_type = type(feed.bozo_exception)
            print(f"Warning: Feed may be ill-formed. Bozo bit set. Exception: {feed.bozo_exception} ({bozo_exception_type})")
            # Proceed if entries exist, as feedparser tries its best
            if not feed.entries and bozo_exception_type != feedparser.NonXMLContentType: # NonXMLContentType can happen with redirects to HTML error pages
                 print("No entries found and feed is ill-formed. Aborting this feed.")
                 return pd.DataFrame() # Return empty DataFrame

        print(f"Found {len(feed.entries)} articles in the RSS feed.")

        for entry in feed.entries[:max_articles_approx]:
            title_text_rss.append(entry.get('title', 'N/A'))
            link_text_rss.append(entry.get('link', 'N/A'))
            
            # Source/Publisher
            source_name = 'N/A'
            if 'source' in entry and entry.source:
                source_name = entry.source.get('title', entry.source.get('href', 'N/A'))
            elif 'publisher' in entry: # Some feeds might use 'publisher'
                 source_name = entry.publisher
            source_text_rss.append(source_name)
            
            # Date
            # feedparser provides 'published_parsed' (a time.struct_time) or 'published' (string)
            date_info = entry.get('published_parsed', entry.get('published'))
            date_text_rss.append(format_rss_date(date_info))
            
            # Content Snippet/Summary
            # 'summary' or 'description' can contain the snippet, often with HTML
            content_html = entry.get('summary', entry.get('description', ''))
            contents_text_rss.append(contents_cleansing(content_html))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        return pd.DataFrame() # Return empty DataFrame on error
    except Exception as e:
        print(f"An unexpected error occurred during RSS processing: {e}")
        return pd.DataFrame()

    # Create result dictionary
    result_rss = {
        "title": title_text_rss,
        "link": link_text_rss,
        "source": source_text_rss,
        "date": date_text_rss,
        "contents": contents_text_rss,
    }
    
    df = pd.DataFrame(result_rss)
    
    if not df.empty:
        current_time = datetime.now()
        # Sanitize query for filename
        safe_query = "".join(c if c.isalnum() else "_" for c in query[:30])
        outputFileName = f'{current_time.strftime("%Y-%m-%d_%H%M%S")}_{safe_query}_RSS.xlsx'
        full_output_path = os.path.join(RESULT_PATH, outputFileName)
        
        try:
            df.to_excel(full_output_path, sheet_name='sheet1', index=False)
            print(f"Crawling complete. Results saved to {full_output_path}")
        except Exception as e:
            print(f"Error saving Excel file: {e}")
            print("Data dump:")
            print(df.head())
    else:
        print("No data crawled from RSS feed.")
        
    return df

def main():
    print("="*50)
    print("Google News RSS Feed Crawler")
    print("="*50)
    
    query = input("Search term: ")
    if not query:
        print("Search term cannot be empty.")
        return

    language = input("Language code (e.g., 'en', 'ko', default is 'en'): ") or "en"
    country_code = input(f"Country code for language '{language}' (e.g., 'US' for en-US, 'KR' for ko-KR, default 'US'): ") or "US"
    
    # RSS feeds don't have pages. They return a batch of recent articles.
    # max_articles can be a soft limit if needed, but usually, you process all entries from one feed pull.
    # max_articles_str = input("Approximate maximum articles to process (default 100, feed may have less): ") or "100"
    # try:
    #     max_articles = int(max_articles_str)
    # except ValueError:
    #     print("Invalid number for max articles, defaulting to 100.")
    #     max_articles = 100
            
    print("\nStarting RSS crawler...")
    # For RSS, we don't typically loop pages, so max_articles is just a limiter on the single feed response.
    crawler_rss(query, language, country_code) # max_articles parameter removed for simplicity, as we take all from one feed pull

if __name__ == "__main__":
    # Check for feedparser
    try:
        import feedparser
    except ImportError:
        print("Required package 'feedparser' is not installed.")
        print("Please install it by running: pip install feedparser")
        exit()
    # Check for dateutil
    try:
        from dateutil import parser
    except ImportError:
        print("Required package 'python-dateutil' is not installed.")
        print("Please install it by running: pip install python-dateutil")
        exit()

    main()
# --- END OF FILE google_news_rss_crawler.py ---