from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import pandas as pd
import re
from urllib.parse import quote, urlparse, unquote
import urllib3
import os
import time
import random

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
< 개선된 Google News RSS 크롤러 >
- RSS 피드를 사용하여 429 오류 방지
- 다중 RSS 소스 활용
- 더 나은 에러 처리 및 재시도 메커니즘
- 한국어/영어 지원
'''

class GoogleNewsRSSCrawler:
    def __init__(self, result_path='C:/Users/kibae/Desktop/google_news_crawling/result'):
        self.result_path = result_path
        self.results = []
        
        # 안정적인 헤더 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    def parse_rss_date(self, date_str):
        """RSS 날짜를 한국 형식으로 변환"""
        try:
            # RSS 표준 날짜 형식: 'Mon, 30 May 2025 10:30:00 GMT'
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y.%m.%d.')
                except ValueError:
                    continue
                    
        except Exception as e:
            print(f"날짜 파싱 오류: {e} - 입력: {date_str}")
        
        return datetime.now().strftime('%Y.%m.%d.')

    def extract_source_from_title(self, title):
        """제목에서 출처 추출"""
        # Google News는 종종 "제목 - 출처" 형식 사용
        separators = [' - ', ' — ', ' | ', ' · ']
        
        for sep in separators:
            if sep in title:
                parts = title.rsplit(sep, 1)
                if len(parts) == 2 and len(parts[1]) < 50:
                    return parts[1].strip(), parts[0].strip()
        
        return None, title

    def extract_source_from_url(self, url):
        """URL에서 출처 추출"""
        try:
            # Google 리다이렉트 URL 처리
            if 'google.com' in url and 'url=' in url:
                match = re.search(r'url=([^&]+)', url)
                if match:
                    url = unquote(match.group(1))
            
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 도메인을 출처명으로 변환
            source_mapping = {
                'chosun.com': 'CHOSUN',
                'donga.com': '동아일보',
                'joongang.co.kr': '중앙일보',
                'hankyung.com': '한국경제',
                'mt.co.kr': '머니투데이',
                'ytn.co.kr': 'YTN',
                'sbs.co.kr': 'SBS',
                'mbc.co.kr': 'MBC',
                'kbs.co.kr': 'KBS',
                'reuters.com': 'Reuters',
                'bloomberg.com': 'Bloomberg',
                'cnn.com': 'CNN',
                'bbc.com': 'BBC'
            }
            
            return source_mapping.get(domain, domain.split('.')[0].upper())
            
        except Exception:
            return "Unknown"

    def get_real_url(self, google_url):
        """Google 리다이렉트 URL에서 실제 URL 추출"""
        try:
            if 'google.com' in google_url:
                # HEAD 요청으로 리다이렉트 따라가기
                response = requests.head(
                    google_url, 
                    allow_redirects=True, 
                    timeout=10, 
                    verify=False,
                    headers=self.headers
                )
                return response.url
            return google_url
        except Exception:
            return google_url

    def fetch_rss_feed(self, rss_url, max_retries=3):
        """RSS 피드 가져오기 (재시도 메커니즘 포함)"""
        for attempt in range(max_retries):
            try:
                # 랜덤 지연으로 봇 탐지 방지
                time.sleep(random.uniform(1, 3))
                
                response = requests.get(
                    rss_url, 
                    headers=self.headers, 
                    timeout=30, 
                    verify=False
                )
                
                if response.status_code == 200:
                    return response.content
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"429 오류 발생. {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"RSS 요청 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
        
        return None

    def crawl_rss_feeds(self, query, max_items=100, time_range='week', language='ko'):
        """다중 RSS 피드에서 뉴스 수집"""
        print(f"검색어: '{query}'")
        print(f"언어: {language}")
        print(f"시간 범위: {time_range}")
        print(f"최대 수집 개수: {max_items}")
        
        # 시간 필터링을 위한 cutoff 날짜 계산
        time_filter_days = {
            'day': 1,
            'week': 7,
            'month': 30,
            'year': 365
        }
        
        filter_days = time_filter_days.get(time_range)
        cutoff_date = datetime.now() - timedelta(days=filter_days) if filter_days else None
        
        encoded_query = quote(query)
        
        # 다양한 RSS 피드 URL 생성
        rss_urls = []
        
        if language == 'ko':
            # 한국어 RSS 피드
            rss_urls.extend([
                f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko",
                f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR",
                f"https://news.google.com/rss/search?q={encoded_query}+site:chosun.com&hl=ko",
                f"https://news.google.com/rss/search?q={encoded_query}+site:donga.com&hl=ko",
                f"https://news.google.com/rss/search?q={encoded_query}+site:joongang.co.kr&hl=ko"
            ])
        else:
            # 영어 RSS 피드
            rss_urls.extend([
                f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en",
                f"https://news.google.com/rss/search?q={encoded_query}&hl=en",
                f"https://news.google.com/rss/search?q={encoded_query}+site:reuters.com&hl=en",
                f"https://news.google.com/rss/search?q={encoded_query}+site:bloomberg.com&hl=en",
                f"https://news.google.com/rss/search?q={encoded_query}+site:cnn.com&hl=en"
            ])
        
        items_found = 0
        processed_titles = set()  # 중복 제거용
        
        for i, rss_url in enumerate(rss_urls):
            if items_found >= max_items:
                break
                
            print(f"\n[{i+1}/{len(rss_urls)}] RSS 피드 처리 중...")
            print(f"URL: {rss_url[:80]}...")
            
            content = self.fetch_rss_feed(rss_url)
            if not content:
                continue
            
            try:
                soup = BeautifulSoup(content, 'xml')
                items = soup.find_all('item')
                
                if not items:
                    print("RSS 아이템을 찾을 수 없습니다.")
                    continue
                
                print(f"발견된 아이템: {len(items)}개")
                
                for item in items:
                    if items_found >= max_items:
                        break
                    
                    title_tag = item.find('title')
                    link_tag = item.find('link')
                    pub_date_tag = item.find('pubDate')
                    source_tag = item.find('source')
                    description_tag = item.find('description')
                    
                    if not title_tag or not link_tag:
                        continue
                    
                    title_raw = title_tag.text.strip()
                    link_raw = link_tag.text.strip()
                    
                    # 중복 제거
                    if title_raw in processed_titles:
                        continue
                    processed_titles.add(title_raw)
                    
                    # 날짜 처리 및 필터링
                    if pub_date_tag:
                        date_parsed = self.parse_rss_date(pub_date_tag.text)
                        
                        # 시간 범위 필터링
                        if cutoff_date:
                            try:
                                item_date = datetime.strptime(date_parsed, '%Y.%m.%d.')
                                if item_date < cutoff_date:
                                    continue
                            except:
                                pass
                    else:
                        date_parsed = datetime.now().strftime('%Y.%m.%d.')
                    
                    # 출처 추출
                    source_name = None
                    cleaned_title = title_raw
                    
                    # 1순위: source 태그
                    if source_tag:
                        source_name = source_tag.text.strip()
                    
                    # 2순위: 제목에서 추출
                    if not source_name:
                        source_from_title, cleaned_title = self.extract_source_from_title(title_raw)
                        if source_from_title:
                            source_name = source_from_title
                    
                    # 3순위: URL에서 추출
                    if not source_name:
                        source_name = self.extract_source_from_url(link_raw)
                    
                    # 실제 URL 가져오기
                    real_url = self.get_real_url(link_raw)
                    
                    # 요약 추출
                    summary = ""
                    if description_tag:
                        summary = re.sub('<[^<]+?>', '', description_tag.text).strip()
                        summary = summary[:200] + "..." if len(summary) > 200 else summary
                    
                    # 결과 저장
                    self.results.append({
                        '검색 키워드': query,
                        '제목': cleaned_title,
                        'URL': real_url,
                        '날짜': date_parsed,
                        '출처': source_name,
                        '요약': summary
                    })
                    
                    items_found += 1
                
                print(f"수집된 아이템: {items_found}개")
                
            except Exception as e:
                print(f"RSS 파싱 오류: {e}")
                continue
        
        return items_found

    def save_to_excel(self, query):
        """결과를 Excel 파일로 저장"""
        if not self.results:
            print("저장할 데이터가 없습니다.")
            return None
        
        # DataFrame 생성
        df = pd.DataFrame(self.results)
        
        # 중복 제거
        df = df.drop_duplicates(subset=['제목'], keep='first')
        
        # 디렉토리 생성
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        
        # 파일명 생성
        now = datetime.now()
        filename = f"{now.strftime('%Y-%m-%d %H시 %M분 %S초')} {query}_RSS.xlsx"
        filepath = os.path.join(self.result_path, filename)
        
        # Excel 저장
        df.to_excel(filepath, sheet_name='뉴스검색결과', index=False)
        
        print(f"\n✅ 저장 완료: {filepath}")
        print(f"총 {len(df)}개 기사 저장 (중복 제거 후)")
        
        # 미리보기 출력
        print("\n📰 검색 결과 미리보기:")
        print("="*80)
        for i, row in df.head(5).iterrows():
            print(f"{i+1}. {row['제목'][:60]}...")
            print(f"   📅 {row['날짜']} | 📰 {row['출처']}")
            if row['요약']:
                print(f"   💬 {row['요약'][:80]}...")
            print()
        
        return df

    def crawl(self, query, max_pages=5, time_range='week', language='ko'):
        """메인 크롤링 함수"""
        print("="*60)
        print("🔍 Google News RSS 크롤러 시작")
        print("="*60)
        
        # 결과 초기화
        self.results.clear()
        
        # 최대 아이템 수 계산 (페이지당 약 10개)
        max_items = int(max_pages) * 10
        
        # RSS 크롤링 실행
        items_found = self.crawl_rss_feeds(query, max_items, time_range, language)
        
        if items_found == 0:
            print("\n❌ 검색 결과가 없습니다.")
            print("다른 검색어를 시도해보세요.")
            return None
        
        # Excel 저장
        df = self.save_to_excel(query)
        return df


def main():
    print("="*60)
    print("🚀 Google News RSS 크롤러 (429 오류 방지)")
    print("="*60)
    
    # 사용자 입력
    query = input("🔍 검색어를 입력하세요: ")
    
    max_pages = input("📄 최대 페이지 수 (기본값: 5): ") or "5"
    
    print("\n⏰ 시간 범위를 선택하세요:")
    print("1. 하루")
    print("2. 일주일")
    print("3. 한달") 
    print("4. 1년")
    print("5. 전체")
    
    time_choice = input("선택 (기본값: 2): ") or "2"
    time_map = {'1': 'day', '2': 'week', '3': 'month', '4': 'year', '5': 'all'}
    time_range = time_map.get(time_choice, 'week')
    
    print("\n🌐 언어를 선택하세요:")
    print("1. 한국어")
    print("2. 영어")
    
    lang_choice = input("선택 (기본값: 1): ") or "1"
    language = 'ko' if lang_choice == '1' else 'en'
    
    # 크롤러 실행
    crawler = GoogleNewsRSSCrawler()
    result = crawler.crawl(query, max_pages, time_range, language)
    
    if result is not None:
        print("\n🎉 크롤링이 성공적으로 완료되었습니다!")
    else:
        print("\n😞 크롤링 중 문제가 발생했습니다.")


if __name__ == "__main__":
    main()