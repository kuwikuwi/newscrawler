# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests, time, random
import pandas as pd
import re

'''
< Naver 뉴스 검색 크롤러 >
 - 수집 대상 : 제목, 링크, 신문사, 날짜, 요약
 - 결과 → DataFrame → Excel
'''

# 결과 저장용 리스트
title_text, link_text, source_text, date_text, contents_text = [], [], [], [], []

# 엑셀 저장 경로 (폴더 끝에 '/' 포함)
RESULT_PATH = 'C:/Users/kibae/Desktop/naver_news_crawling/result/'

# 날짜 정제 함수
def date_cleansing(raw: str) -> str:
    now = datetime.now()
    try:
        # 절대 날짜 패턴
        if m := re.search(r'\d+\.\d+\.\d+\.', raw):
            return m.group(0)
        # 상대 날짜 처리
        if '일 전' in raw:
            d = int(re.search(r'(\d+)일 전', raw).group(1))
            return (now - timedelta(days=d)).strftime('%Y.%m.%d.')
        if '시간 전' in raw:
            h = int(re.search(r'(\d+)시간 전', raw).group(1))
            return (now - timedelta(hours=h)).strftime('%Y.%m.%d.')
        if '분 전' in raw:
            m = int(re.search(r'(\d+)분 전', raw).group(1))
            return (now - timedelta(minutes=m)).strftime('%Y.%m.%d.')
    except Exception:
        pass
    return now.strftime('%Y.%m.%d.')

# 본문 요약 정제 함수
def contents_cleansing(fragment) -> str:
    text = re.sub('<.+?>', '', str(fragment)).strip()
    return text

def crawler(maxpage: int, query: str, sort: str, s_date: str, e_date: str):
    # 초기화
    title_text.clear()
    link_text.clear()
    source_text.clear()
    date_text.clear()
    contents_text.clear()

    s_from = s_date.replace('.', '')
    e_to   = e_date.replace('.', '')
    page   = 1
    maxpage_t = (int(maxpage) - 1) * 10 + 1

    # 헤더 추가 (필수)
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    while page <= maxpage_t:
        url = (
            f'https://search.naver.com/search.naver?where=news'
            f'&query={query}&sort={sort}'
            f'&ds={s_date}&de={e_date}'
            f'&nso=so%3Ar%2Cp%3Afrom{s_from}to{e_to}%2Ca%3A'
            f'&start={page}'
        )
        resp = requests.get(url, headers=headers, timeout=5, verify=False)
        # print(resp.status_code)  # → 200이어야 정상
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 실제 뉴스 아이템을 감싸는 li 선택
        for box in soup.select('div.group_news ul.list_news > li'):
            a = box.select_one('a.api_txt_lines')
            if not a:
                continue
            title_text.append(a.get_text(strip=True))
            link_text.append(a['href'])

            press = box.select_one('span.press')
            source_text.append(press.get_text(strip=True) if press else '')

            info = box.select_one('span.info')
            date_text.append(date_cleansing(info.get_text()) if info else '')

            snippet = box.select_one('div.dsc_wrap')
            contents_text.append(contents_cleansing(snippet) if snippet else '')

        print(f'▶ 페이지 {page} 완료, 수집된 제목 수: {len(title_text)}')
        page += 10
        time.sleep(random.uniform(1.5, 3.0))

    # DataFrame 생성 및 저장
    df = pd.DataFrame({
        'date'    : date_text,
        'title'   : title_text,
        'source'  : source_text,
        'contents': contents_text,
        'link'    : link_text,
    })
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f'{timestamp}_{query}.xlsx'
    df.to_excel(RESULT_PATH + filename, index=False)
    print(f'✅ 저장 완료: {RESULT_PATH}{filename}')

def main():
    input('='*50 + '\nEnter 키를 누르면 시작합니다.\n' + '='*50)
    maxpage = input('최대 크롤링 페이지 수: ')
    query   = input('검색어: ')
    sort    = input('정렬 방식(관련도=0/최신=1/오래된=2): ')
    s_date  = input('시작 날짜(예: 2019.01.04): ')
    e_date  = input('끝   날짜(예: 2019.01.05): ')
    crawler(maxpage, query, sort, s_date, e_date)

if __name__ == '__main__':
    main()
