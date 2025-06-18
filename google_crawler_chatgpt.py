import os
from datetime import datetime, timedelta
import pandas as pd
from newsapi import NewsApiClient

# --- 설정 ---
API_KEY     = '8939eb6ba17e43dbb79ec01b7fc5997b'  # 본인 키로 교체
RESULT_PATH = 'C:/Users/kibae/Desktop/google_news_crawling/result'
PAGE_SIZE   = 100  # NewsAPI 최대 100
MAX_PAGES   = 5    # 최대 5 페이지 (500개)

# --- 날짜 포맷터 ---
def iso_to_ymd(iso_str):
    """ISO 8601 → 'YYYY.MM.DD.' 형식"""
    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return dt.strftime('%Y.%m.%d.')

# --- time_range → from/to 계산 ---
def calc_date_range(time_range: str):
    now = datetime.utcnow()
    if time_range == 'day':
        start = now - timedelta(days=1)
    elif time_range == 'week':
        start = now - timedelta(weeks=1)
    elif time_range == 'month':
        start = now - timedelta(days=30)
    elif time_range == 'year':
        start = now - timedelta(days=365)
    else:
        return None, now
    return start, now

# --- 메인 크롤러 ---
def crawler_with_api(query: str,
                     time_range: str = 'all',
                     sources: str = None,
                     domains: str = None,
                     language: str = 'en',
                     sort_by: str = 'publishedAt'):
    newsapi = NewsApiClient(api_key=API_KEY)
    start_dt, end_dt = calc_date_range(time_range)
    from_param = start_dt.strftime('%Y-%m-%dT%H:%M:%S') if start_dt else None
    to_param   = end_dt.strftime('%Y-%m-%dT%H:%M:%S')

    all_articles = []
    for page in range(1, MAX_PAGES + 1):
        resp = newsapi.get_everything(
            q=query,
            sources=sources,
            domains=domains,
            from_param=from_param,
            to=to_param,
            language=language,
            sort_by=sort_by,
            page=page,
            page_size=PAGE_SIZE
        )
        if resp.get('status') != 'ok':
            print("API Error:", resp.get('code'), resp.get('message'))
            break

        articles = resp.get('articles', [])
        if not articles:
            break

        all_articles.extend(articles)
        if len(articles) < PAGE_SIZE:
            break

    # DataFrame 변환
    records = []
    for art in all_articles:
        records.append({
            'title':       art.get('title', '').strip(),
            'url':         art.get('url', ''),
            'source':      art.get('source', {}).get('name', ''),
            'date':        iso_to_ymd(art.get('publishedAt', datetime.utcnow().isoformat())),
            'description': art.get('description') or art.get('content') or ''
        })
    df = pd.DataFrame(records)

    # 결과 저장
    os.makedirs(RESULT_PATH, exist_ok=True)
    now = datetime.now()
    fname = f"{now:%Y-%m-%d %H시 %M분 %S초} {query}.xlsx"
    path  = os.path.join(RESULT_PATH, fname)
    df.to_excel(path, index=False)
    print(f"Crawling complete: {len(df)} articles saved to\n  {path}")
    return df

# --- 명령줄 인터페이스 ---
if __name__ == '__main__':
    print("="*40)
    print(" NewsAPI 기반 뉴스 크롤러 ")
    print("="*40)
    q = input("검색어(q): ").strip()

    print("기간: 1.day  2.week  3.month  4.year  5.all")
    tr = input("선택(기본 all): ").strip()
    tr_map = {'1':'day','2':'week','3':'month','4':'year','5':'all'}
    time_range = tr_map.get(tr, 'all')

    src = input("sources (comma-separated, skip 엔터): ").strip() or None
    dom = input("domains (comma-separated, skip 엔터): ").strip() or None
    lang = input("language (default 'en'): ").strip() or 'en'

    print("정렬: 1.relevancy  2.popularity  3.publishedAt")
    sb = input("선택(기본 3): ").strip()
    sort_map = {'1':'relevancy','2':'popularity','3':'publishedAt'}
    sort_by = sort_map.get(sb, 'publishedAt')

    crawler_with_api(
        query      = q,
        time_range = time_range,
        sources    = src,
        domains    = dom,
        language   = lang,
        sort_by    = sort_by
    )
