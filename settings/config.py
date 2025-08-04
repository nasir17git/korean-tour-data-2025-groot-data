import os
from dotenv import load_dotenv
import requests
import time

# .env 파일 로드
load_dotenv()

# 환경 변수
SUPABASE_BASE_URL = os.getenv('SUPABASE_BASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
DATA_KEY_ENCODING = os.getenv('DATA_KEY_ENCODING')
DATA_KEY_DECODING = os.getenv('DATA_KEY_DECODING')

# API 공통 파라미터
COMMON_PARAMS = {
    "numOfRows": "100",
    "pageNo": "1",
    "MobileOS": "ETC",
    "_type": "json"
}

def fetch_all_pages(base_url, endpoint_path, base_params, max_pages=50):
    """
    모든 페이지의 데이터를 가져오는 공통 함수
    
    Args:
        base_url (str): API 기본 URL
        endpoint_path (str): 엔드포인트 경로
        base_params (dict): 기본 파라미터
        max_pages (int): 최대 페이지 수 (무한루프 방지)
        
    Returns:
        tuple: (all_items: list, error: str)
    """
    all_items = []
    page_no = 1
    
    while page_no <= max_pages:
        params = base_params.copy()
        params["pageNo"] = str(page_no)
        
        url = base_url + endpoint_path
        
        try:
            print(f"[페이지 {page_no}] 요청 중...")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return all_items, f"HTTP {response.status_code} 오류 (페이지 {page_no})"
                
            data = response.json()
            
            # 응답 구조 확인
            response_body = data.get("response", {}).get("body", {})
            total_count = response_body.get("totalCount", 0)
            items = response_body.get("items", {})
            
            # items가 없거나 빈 경우 종료
            if not items:
                print(f"[페이지 {page_no}] 데이터 없음, 종료")
                break
                
            # item 추출
            if isinstance(items, dict):
                item_list = items.get("item", [])
            else:
                item_list = items
                
            if not isinstance(item_list, list):
                item_list = [item_list] if item_list else []
                
            if not item_list:
                print(f"[페이지 {page_no}] 아이템 없음, 종료")
                break
                
            all_items.extend(item_list)
            print(f"[페이지 {page_no}] {len(item_list)}개 수집 (총 {len(all_items)}개)")
            
            # 전체 데이터를 다 가져왔는지 확인
            if len(all_items) >= total_count:
                print(f"[완료] 전체 {total_count}개 데이터 수집 완료")
                break
                
            # 다음 페이지로
            page_no += 1
            
            # API 호출 간격 (과도한 요청 방지)
            time.sleep(0.1)
            
        except Exception as e:
            return all_items, f"페이지 {page_no} 처리 실패: {str(e)}"
    
    return all_items, None

# API 별 기본 설정
API_CONFIGS = {
    "greentour": {
        "base_url": "https://apis.data.go.kr/B551011/GreenTourService1",
        "app_name": "MyEcotourApp",
        "service_key": DATA_KEY_DECODING
    },
    "barrier_free": {
        "base_url": "https://apis.data.go.kr/B551011/KorWithService2", 
        "app_name": "BarrierFreeApp",
        "service_key": DATA_KEY_DECODING
    },
    "base_tour": {
        "base_url": "https://apis.data.go.kr/B551011/LocgoHubTarService1",
        "app_name": "MyBaseTourApp", 
        "service_key": DATA_KEY_DECODING
    }
}
