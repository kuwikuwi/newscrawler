# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
import pandas as pd
import re
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
< naver 뉴스 검색시 리스트 크롤링하는 프로그램 > _select사용
- 크롤링 해오는 것 : 링크,제목,신문사,날짜,내용요약본
- 날짜,내용요약본  -> 정제 작업 필요
- 리스트 -> 딕셔너리 -> df -> 엑셀로 저장 
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#각 크롤링 결과 저장하기 위한 리스트 선언 
title_text=[]
link_text=[]
source_text=[]
date_text=[]
contents_text=[]
result={}

#엑셀로 저장하기 위한 변수
RESULT_PATH ='C:/Users/kibae/Desktop/naver_news_crawling/result'  #결과 저장할 경로
now = datetime.now() #파일이름 현 시간으로 저장하기

#날짜 정제화 함수
def date_cleansing(test):
    try:
        #지난 뉴스
        #머니투데이  10면1단  2018.11.05.  네이버뉴스   보내기  
        pattern = '\\d+.(\\d+).(\\d+).'  #정규표현식 
    
        r = re.compile(pattern)
        match = r.search(test).group(0)  # 2018.11.05.
        date_text.append(match)
        now = datetime.now()  #파일이름 현 시간으로 저장하기
        
        # "1일 전", "7시간 전" 등의 패턴 확인
        if '일 전' in test:
            days_ago = int(re.search('(\d+)일 전', test).group(1))
            target_date = now - timedelta(days=days_ago)
            date_text.append(target_date.strftime('%Y.%m.%d.'))
            
        elif '시간 전' in test:
            hours_ago = int(re.search('(\d+)시간 전', test).group(1))
            target_date = now - timedelta(hours=hours_ago)
            date_text.append(target_date.strftime('%Y.%m.%d.'))
            
        elif '분 전' in test:
            minutes_ago = int(re.search('(\d+)분 전', test).group(1))
            target_date = now - timedelta(minutes=minutes_ago)
            date_text.append(target_date.strftime('%Y.%m.%d.'))
            
        else:
            # 기타 형식이나 인식할 수 없는 형식
            date_text.append(now.strftime('%Y.%m.%d.'))
            
    except Exception as e:
        # 오류 발생시 현재 날짜 사용
        print(f"날짜 변환 중 오류 발생: {e} - 입력값: {test}")
        now = datetime.now()
        date_text.append(now.strftime('%Y.%m.%d.'))


#내용 정제화 함수 
def contents_cleansing(contents):
    first_cleansing_contents = re.sub('<dl>.*?</a> </div> </dd> <dd>', '', 
                                      str(contents)).strip()  #앞에 필요없는 부분 제거
    second_cleansing_contents = re.sub('<ul class="relation_lst">.*?</dd>', '', 
                                       first_cleansing_contents).strip()#뒤에 필요없는 부분 제거 (새끼 기사)
    third_cleansing_contents = re.sub('<.+?>', '', second_cleansing_contents).strip()
    contents_text.append(third_cleansing_contents)
    #print(contents_text)
    

def crawler(maxpage,query,sort,s_date,e_date):

    s_from = s_date.replace(".","")
    e_to = e_date.replace(".","")
    page = 1  
    maxpage_t =(int(maxpage)-1)*10+1   # 11= 2페이지 21=3페이지 31=4페이지  ...81=9페이지 , 91=10페이지, 101=11페이지
    
    while page <= maxpage_t:
        url = "https://search.naver.com/search.naver?where=news&query=" + query + "&sort="+sort+"&ds=" + s_date + "&de=" + e_date + "&nso=so%3Ar%2Cp%3Afrom" + s_from + "to" + e_to + "%2Ca%3A&start=" + str(page)
        
        response = requests.get(url, verify=False)
        html = response.text
        # print(html)
        # print(f"[Page {page}] status:", response.status_code)
        # print(f"[Page {page}] HTML 길이:", len(html))
        # print(f"[Page {page}] 'list_news' 포함 여부:", "list_news" in html)
        # # (원한다면 앞 500자만 살펴보기)
        # print(html[:500])  

        #뷰티풀소프의 인자값 지정
        soup = BeautifulSoup(html, 'html.parser')
        blocks = soup.select("ul.list_news > li")
        titles = soup.select(".news_tit")
        sources = soup.select(".info_group > .press")
        dates   = soup.select(".info_group > span.info")
        descs   = soup.select(".news_dsc")

        print(f"[Page {page}] list_news 블록 수      : {len(blocks)}")
        print(f"[Page {page}] .news_tit 수           : {len(titles)}")
        print(f"[Page {page}] 신문사(.press) 수       : {len(sources)}")
        print(f"[Page {page}] 날짜(.info) 수         : {len(dates)}")
        print(f"[Page {page}] 요약(.news_dsc) 수      : {len(descs)}")
 
        #<a>태그에서 제목과 링크주소 추출
        atags = soup.select('.news_tit')
        for atag in atags:
            title_text.append(atag.text)     #제목
            link_text.append(atag['href'])   #링크주소
            
        #신문사 추출
        source_lists = soup.select('.info_group > .press')
        for source_list in source_lists:
            source_text.append(source_list.text)    #신문사
        
        #날짜 추출 
        date_lists = soup.select('.info_group > span.info')
        for date_list in date_lists:
            # 1면 3단 같은 위치 제거
            if date_list.text.find("면") == -1:
                date_text.append(date_cleansing(date_list.text))
        
        #본문요약본
        contents_lists = soup.select('.news_dsc')
        for contents_list in contents_lists:
            contents_cleansing(contents_list) #본문요약 정제화
        

        #모든 리스트 딕셔너리형태로 저장
        result= {"date" : date_text , "title":title_text ,  "source" : source_text ,"contents": contents_text ,"link":link_text }  
        print(page)
        
        df = pd.DataFrame(result)  #df로 변환
        page += 10
    
    
    # 새로 만들 파일이름 지정
    outputFileName = '%s-%s-%s  %s시 %s분 %s초 merging.xlsx' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    df.to_excel(RESULT_PATH+outputFileName,sheet_name='sheet1')
    
    

def main():
    info_main = input("="*50+"\n"+"입력 형식에 맞게 입력해주세요."+"\n"+" 시작하시려면 Enter를 눌러주세요."+"\n"+"="*50)
    
    maxpage = input("최대 크롤링할 페이지 수 입력하시오: ")  
    query = input("검색어 입력: ")  
    sort = input("뉴스 검색 방식 입력(관련도순=0  최신순=1  오래된순=2): ")    #관련도순=0  최신순=1  오래된순=2
    s_date = input("시작날짜 입력(2019.01.04):")  #2019.01.04
    e_date = input("끝날짜 입력(2019.01.05):")   #2019.01.05
    
    crawler(maxpage,query,sort,s_date,e_date) 
    
main()

