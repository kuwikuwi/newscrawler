#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.crawlers import GoogleNewsCrawler
from src.config import Config

def test_network():
    print("Testing network connectivity...")
    Config.ensure_result_dir()
    
    crawler = GoogleNewsCrawler()
    print("Testing Google News crawler...")
    
    try:
        results = crawler.crawl("test", max_pages=1)
        if results:
            print(f"✅ Success: Found {len(results)} articles")
            return True
        else:
            print("⚠️ No results found, but no network errors")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_network()
    sys.exit(0 if success else 1)