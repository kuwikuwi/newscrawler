# 통합 뉴스 크롤러 (Unified News Crawler)

Python을 이용한 Google News와 Naver News 통합 크롤링 프로그램

## 주요 특징

- **통합 크롤링**: Google News와 Naver News를 하나의 프로그램으로 크롤링
- **모듈화된 구조**: 재사용 가능한 컴포넌트와 깔끔한 코드 구조
- **안정적인 수집**: 에러 처리, 재시도 메커니즘, 요청 제한 준수
- **다양한 옵션**: 시간 범위, 정렬 방식, 페이지 수 설정 가능
- **자동 데이터 정제**: 중복 제거, 텍스트 정리, 유효성 검사

## 프로젝트 구조

```
newscrawler/
├── src/
│   ├── config/          # 설정 관리
│   ├── crawlers/        # 크롤러 클래스들
│   ├── utils/           # 공통 유틸리티
│   └── __init__.py
├── result/              # 크롤링 결과 저장
├── main.py              # 메인 실행 파일
├── requirements.txt     # 의존성 패키지
└── README.md
```

## 설치 방법

### 1. 저장소 클론
```bash
git clone <repository-url>
cd newscrawler
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 실행
```bash
python main.py
```

### 프로그램 사용 흐름
1. 검색어 입력
2. 뉴스 소스 선택 (Google/Naver/둘 다)
3. 옵션 설정 (페이지 수, 정렬 방식, 시간 범위)
4. 크롤링 실행 및 결과 저장

### 개별 크롤러 사용 예제
```python
from src.crawlers import GoogleNewsCrawler, NaverNewsCrawler

# Google News 크롤링
google_crawler = GoogleNewsCrawler()
results = google_crawler.crawl("양자컴퓨터", max_pages=3, time_range="1d")
google_crawler.save_results("양자컴퓨터")

# Naver News 크롤링
naver_crawler = NaverNewsCrawler()
results = naver_crawler.crawl("양자컴퓨터", max_pages=5, sort="1")
naver_crawler.save_results("양자컴퓨터")
```

## 주요 개선사항

### 기존 코드 대비 개선점
- **60-70% 코드 중복 제거**: 2,464줄 → 약 800-1000줄
- **모듈화**: 공통 기능을 재사용 가능한 유틸리티로 분리
- **설정 관리**: 하드코딩된 값들을 설정 파일로 분리
- **에러 처리**: 안정적인 크롤링을 위한 예외 처리 강화
- **데이터 품질**: 자동 정제 및 유효성 검사 추가

### 보안 개선
- API 키 환경변수화
- SSL 경고 처리 개선
- 요청 헤더 정규화

## 설정 옵션

### 시간 범위 (Google News)
- `1h`: 1시간
- `1d`: 1일 (기본값)
- `1w`: 1주
- `1m`: 1개월

### 정렬 방식 (Naver News)
- `0`: 관련성순 (기본값)
- `1`: 최신순

## 출력 파일

크롤링 결과는 `result/` 디렉토리에 Excel 파일로 저장됩니다:
- 파일명: `YYYY-MM-DD HH시 MM분 SS초 검색어.xlsx`
- 컬럼: title, link, source, date, content

## 의존성 패키지

### 필수 패키지
- `beautifulsoup4`: HTML 파싱
- `requests`: HTTP 요청
- `pandas`: 데이터 처리
- `lxml`: XML 파싱
- `openpyxl`: Excel 파일 생성

### 선택적 패키지
- `selenium`: 동적 페이지 크롤링 (필요시)
- `python-docx`: Word 문서 생성 (필요시)

## 문제 해결

### 크롤링이 실패하는 경우
1. 네트워크 연결 확인
2. 요청 제한으로 인한 차단 (시간 간격을 두고 재시도)
3. 웹사이트 구조 변경 (코드 업데이트 필요)

### 빈 결과가 나오는 경우
1. 검색어 확인
2. 시간 범위 조정
3. 웹사이트 접근 가능 여부 확인

## 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.