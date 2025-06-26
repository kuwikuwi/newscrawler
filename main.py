#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
통합 뉴스 크롤러
Google News와 Naver News에서 뉴스를 수집하는 통합 프로그램
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.crawlers import GoogleNewsCrawler, NaverNewsCrawler
from src.config import Config

def get_user_input():
    """사용자 입력을 받아 크롤링 설정을 반환"""
    print("=" * 50)
    print("    통합 뉴스 크롤러")
    print("=" * 50)
    
    # 검색어 입력
    query = input("검색어를 입력하세요: ").strip()
    if not query:
        print("검색어를 입력해야 합니다.")
        return None
    
    # 뉴스 소스 선택
    print("\n뉴스 소스를 선택하세요:")
    print("1. Google News")
    print("2. Naver News")
    print("3. 둘 다")
    
    source_choice = input("선택 (1-3): ").strip()
    
    sources = []
    if source_choice == '1':
        sources = ['google']
    elif source_choice == '2':
        sources = ['naver']
    elif source_choice == '3':
        sources = ['google', 'naver']
    else:
        print("잘못된 선택입니다. Google News로 진행합니다.")
        sources = ['google']
    
    # 최대 페이지 수
    try:
        max_pages = int(input("최대 페이지 수 (기본값 5): ") or "5")
        max_pages = max(1, min(max_pages, 20))  # 1-20 범위로 제한
    except ValueError:
        max_pages = 5
    
    # 정렬 옵션 (Naver용)
    sort_option = '0'  # 기본값: 관련성
    if 'naver' in sources:
        print("\n정렬 방식을 선택하세요 (Naver News):")
        print("1. 관련성순")
        print("2. 최신순")
        
        sort_choice = input("선택 (1-2, 기본값 1): ").strip()
        sort_option = '1' if sort_choice == '2' else '0'
    
    # 시간 범위 (Google용)
    time_range = '1d'  # 기본값: 1일
    if 'google' in sources:
        print("\n시간 범위를 선택하세요 (Google News):")
        print("1. 1시간")
        print("2. 1일")
        print("3. 1주")
        print("4. 1개월")
        
        time_choice = input("선택 (1-4, 기본값 2): ").strip()
        time_map = {'1': '1h', '2': '1d', '3': '1w', '4': '1m'}
        time_range = time_map.get(time_choice, '1d')
    
    return {
        'query': query,
        'sources': sources,
        'max_pages': max_pages,
        'sort': sort_option,
        'time_range': time_range
    }

def run_crawler(crawler, query, **kwargs):
    """크롤러 실행"""
    try:
        print(f"\n{crawler.get_source_name()} 크롤링 시작...")
        results = crawler.crawl(query, **kwargs)
        
        if results:
            filename = crawler.save_results(query)
            print(f"✅ {len(results)}개 기사 수집 완료")
            print(f"📁 저장 위치: {filename}")
            return True
        else:
            print("❌ 수집된 기사가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 크롤링 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    try:
        # 사용자 입력 받기
        config = get_user_input()
        if not config:
            return
        
        print(f"\n🔍 검색어: {config['query']}")
        print(f"📰 소스: {', '.join(config['sources']).upper()}")
        print(f"📄 최대 페이지: {config['max_pages']}")
        
        # 결과 디렉토리 생성
        Config.ensure_result_dir()
        
        success_count = 0
        
        # Google News 크롤링
        if 'google' in config['sources']:
            google_crawler = GoogleNewsCrawler()
            if run_crawler(
                google_crawler, 
                config['query'],
                max_pages=config['max_pages'],
                time_range=config['time_range']
            ):
                success_count += 1
        
        # Naver News 크롤링
        if 'naver' in config['sources']:
            naver_crawler = NaverNewsCrawler()
            if run_crawler(
                naver_crawler,
                config['query'],
                max_pages=config['max_pages'],
                sort=config['sort']
            ):
                success_count += 1
        
        # 결과 요약
        print("\n" + "=" * 50)
        if success_count > 0:
            print("🎉 크롤링이 성공적으로 완료되었습니다!")
            print(f"📊 {success_count}개 소스에서 데이터 수집 완료")
        else:
            print("⚠️  크롤링 중 문제가 발생했습니다.")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()