from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import pandas as pd
import re
from urllib.parse import quote
import urllib3

# Disable SSL warnings - only use this if you understand the security implications
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
< Google News Search Crawler >
- Crawls: link, title, source, date, content snippet
- Processes and cleans date and content
- Saves results to Excel file
'''

# Lists to store crawling results
title_text = []
link_text = []
source_text = []
date_text = []
contents_text = []
result = {}

# Path to save Excel file
RESULT_PATH = 'C:/Users/kibae/Desktop/google_news_crawling/result'  # Change to your desired path
now = datetime.now()

# Date cleaning function
def date_cleansing(date_str):
    now = datetime.now()
    
    try:
        # Handle relative time formats from Google News
        if 'hour' in date_str or 'hr' in date_str:
            hours_ago = int(re.search(r'(\d+)', date_str).group(1))
            target_date = now - timedelta(hours=hours_ago)
            return target_date.strftime('%Y.%m.%d.')
            
        elif 'day' in date_str:
            days_ago = int(re.search(r'(\d+)', date_str).group(1))
            target_date = now - timedelta(days=days_ago)
            return target_date.strftime('%Y.%m.%d.')
            
        elif 'min' in date_str:
            minutes_ago = int(re.search(r'(\d+)', date_str).group(1))
            target_date = now - timedelta(minutes=minutes_ago)
            return target_date.strftime('%Y.%m.%d.')
            
        elif 'week' in date_str:
            weeks_ago = int(re.search(r'(\d+)', date_str).group(1))
            target_date = now - timedelta(weeks=weeks_ago)
            return target_date.strftime('%Y.%m.%d.')
            
        elif 'month' in date_str:
            # Approximate month as 30 days
            months_ago = int(re.search(r'(\d+)', date_str).group(1))
            target_date = now - timedelta(days=30*months_ago)
            return target_date.strftime('%Y.%m.%d.')
            
        # Try to handle specific date formats (Google often shows date as "Jan 5, 2023")
        else:
            # This regex tries to match formats like "Jan 5, 2023" or "January 5, 2023"
            pattern = r'([A-Za-z]{3,9})\s+(\d{1,2}),\s+(\d{4})'
            match = re.search(pattern, date_str)
            if match:
                month_dict = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month_str = match.group(1).lower()[:3]  # Take first 3 chars of month name
                month = month_dict.get(month_str, 1)  # Default to 1 if not found
                day = int(match.group(2))
                year = int(match.group(3))
                
                return f"{year}.{month:02d}.{day:02d}."
    
    except Exception as e:
        print(f"Date conversion error: {e} - Input: {date_str}")
    
    # Default to current date if parsing fails
    return now.strftime('%Y.%m.%d.')

# Content cleaning function 
def contents_cleansing(contents):
    if contents:
        # Remove HTML tags
        cleaned_content = re.sub('<.+?>', '', str(contents)).strip()
        # Remove extra whitespace
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
        contents_text.append(cleaned_content)
    else:
        contents_text.append("")

def crawler(maxpage, query, time_range=None, language='en'):
    # Clear previous results
    title_text.clear()
    link_text.clear()
    source_text.clear()
    date_text.clear()
    contents_text.clear()
    
    # Encode query for URL
    encoded_query = quote(query)
    
    # Default headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Time range parameter mapping (Google uses 'qdr' parameter)
    time_params = {
        'day': 'd',
        'week': 'w',
        'month': 'm',
        'year': 'y'
    }
    
    time_param = ""
    if time_range in time_params:
        time_param = f"&tbs=qdr:{time_params[time_range]}"
    
    page = 0
    items_per_page = 10
    max_items = int(maxpage) * items_per_page
    
    while page * items_per_page < max_items:
        # Google News search URL
        url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl={language}{time_param}&start={page * items_per_page}"
        
        try:
            # Set verify=False to bypass SSL certificate verification
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            if response.status_code != 200:
                print(f"Failed to fetch page {page+1}. Status code: {response.status_code}")
                break
                
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find news articles (Google's structure may change over time)
            # Try multiple possible selectors for articles
            articles = soup.select('div.SoaBEf') or soup.select('div.xuvV6b') or soup.select('div.v7W49e')
            
            if not articles:
                break
                print(f"No articles found on page {page+1}. Trying alternative selectors...")
                # Try an even broader approach if common selectors fail
                articles = soup.select('a[href^="https://"]')
                if not articles:
                    print("Still no articles found. Google may have changed their HTML structure.")
                    # Debug info
                    print("Page HTML structure (first 500 chars):")
                    print(html[:500])
                    break
            
            for article in articles:
                # Extract title and link - try multiple possible selectors
                title_element = (article.select_one('div.MBeuO') or 
                                article.select_one('h3') or 
                                article.select_one('.DY5T1d') or
                                article)
                
                # For the link, check if the article itself is an <a> tag, otherwise find one
                if article.name == 'a' and 'href' in article.attrs:
                    link_element = article
                else:
                    link_element = article.select_one('a')
                
                # Process title element
                if title_element:
                    # If we're using the article itself as title element (fallback)
                    if title_element == article:
                        # Try to extract the text content or use a default
                        title = title_element.get_text(strip=True)
                        # If title is too long, it's probably not just a title
                        if len(title) > 200:
                            # Try to find the first meaningful text
                            for tag in title_element.find_all(['h3', 'h2', 'b', 'strong']):
                                if tag.get_text(strip=True):
                                    title = tag.get_text(strip=True)
                                    break
                    else:
                        title = title_element.get_text(strip=True)
                    
                    # Clean up title if needed
                    title = title.replace('\n', ' ').strip()
                    title_text.append(title)
                else:
                    # If we can't find a title, create a placeholder
                    title_text.append(f"[Article #{len(title_text) + 1}]")
                
                # Process link element
                if link_element and 'href' in link_element.attrs:
                    link = link_element['href']
                    # Google sometimes includes redirect URLs
                    if link.startswith('/url?'):
                        # Extract the actual URL from Google's redirect
                        import re
                        match = re.search(r'url=([^&]+)', link)
                        if match:
                            from urllib.parse import unquote
                            link = unquote(match.group(1))
                    
                    link_text.append(link)
                else:
                    # Skip this article if we don't have a link
                    continue
                
                # Extract source - try multiple possible selectors
                source_element = article.select_one('div.CEMjEf span') or article.select_one('.vN4Yjc') or article.select_one('.BNeawe.UPmit.AP7Wnd')
                
                # If we found a source element, clean it up
                if source_element:
                    source_name = source_element.text.strip()
                    # Sometimes the source includes time, like "CHOSUNBIZ · 2 hours ago"
                    # So we split on common separators
                    for separator in [' · ', ' - ', ' | ']:
                        if separator in source_name:
                            source_name = source_name.split(separator)[0].strip()
                            break
                    source_text.append(source_name)
                else:
                    # Try to extract from URL if source element not found
                    if link_element and link_element['href']:
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(link_element['href']).netloc
                            # Remove www. if present
                            if domain.startswith('www.'):
                                domain = domain[4:]
                            source_text.append(domain)
                        except:
                            source_text.append("Unknown")
                    else:
                        source_text.append("Unknown")
                
                # Extract date
                date_element = article.select_one('div.OSrXXb span')
                if date_element:
                    date_text.append(date_cleansing(date_element.text.strip()))
                else:
                    date_text.append(datetime.now().strftime('%Y.%m.%d.'))
                
                # Extract content snippet
                content_element = article.select_one('div.GI74Re')
                if content_element:
                    contents_cleansing(content_element.text)
                else:
                    contents_text.append("")
            
            print(f"Processed page {page+1}")
            page += 1
            
            # Add a delay to avoid being blocked
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"Error crawling page {page+1}: {e}")
            break
    
    # Check if we have equal length lists (important before creating DataFrame)
    min_length = min(len(title_text), len(link_text), len(source_text), len(date_text), len(contents_text))
    
    # Create result dictionary with lists trimmed to same length
    result = {
        "contents": contents_text[:min_length],
        "title": title_text[:min_length],
        "link": link_text[:min_length],
        "date": date_text[:min_length],
        "source": source_text[:min_length],
    }
    
    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(result)
    
    # Create directory if it doesn't exist
    import os
    if not os.path.exists(RESULT_PATH):
        os.makedirs(RESULT_PATH)
    
    # Generate output filename
    outputFileName = f'{now.year}-{now.month}-{now.day} {now.hour}시 {now.minute}분 {now.second}초 {query} .xlsx'
    df.to_excel(os.path.join(RESULT_PATH, outputFileName), sheet_name='sheet1')
    print(f"Crawling complete. Results saved to {os.path.join(RESULT_PATH, outputFileName)}")
    
    return df

def debug_html_structure(url):
    """Utility function to analyze the current Google News HTML structure"""
    print("\nDEBUGGING HTML STRUCTURE") 
    print("-" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        if response.status_code != 200:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return
            
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Log potential article containers
        containers = [
            'div.SoaBEf', 'div.xuvV6b', 'div.v7W49e', 'div.DBldde', 'div.Y4pkMc'
        ]
        
        for selector in containers:
            elements = soup.select(selector)
            print(f"Found {len(elements)} elements matching '{selector}'")
            
            if elements and len(elements) > 0:
                print(f"First element structure:")
                print(elements[0].__str__()[:500] + "..." if len(elements[0].__str__()) > 500 else elements[0])
                print("-" * 30)
        
        # Try to find title elements
        print("\nPotential title elements:")
        title_selectors = ['h3', 'h3.zBAuLc', 'div.MBeuO', '.DY5T1d', '.vN4Yjc']
        for selector in title_selectors:
            elements = soup.select(selector)
            print(f"Found {len(elements)} elements matching '{selector}'")
            if elements and len(elements) > 0:
                print(f"First example: {elements[0].text.strip()}")
                
        # Try to find source elements
        print("\nPotential source elements:")
        source_selectors = ['div.CEMjEf span', '.vN4Yjc', '.BNeawe.UPmit.AP7Wnd', '.wEwyrc']
        for selector in source_selectors:
            elements = soup.select(selector)
            print(f"Found {len(elements)} elements matching '{selector}'")
            if elements and len(elements) > 0:
                print(f"First example: {elements[0].text.strip()}")
        
    except Exception as e:
        print(f"Error in debug function: {e}")
    
    print("-" * 50)

def main():
    print("="*50)
    print("Google News Crawler")
    print("="*50)
    
    maxpage = input("Maximum number of pages to crawl: ")
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
    
    debug_mode = input("Run in debug mode? (y/n, default is n): ").lower() == 'y'
    
    if debug_mode:
        encoded_query = quote(query)
        debug_url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl={language}"
        print(f"\nRunning debug analysis on {debug_url}")
        debug_html_structure(debug_url)
        proceed = input("\nProceed with crawling? (y/n, default is y): ").lower() != 'n'
        if not proceed:
            print("Crawling canceled.")
            return
            
    print("\nStarting crawler...")
    crawler(maxpage, query, time_range, language)

if __name__ == "__main__":
    main()