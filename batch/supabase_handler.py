import requests
import json
from settings.config import SUPABASE_API_KEY, SUPABASE_BASE_URL

class SupabaseHandler:
    def __init__(self):
        self.api_key = SUPABASE_API_KEY
        self.base_url = SUPABASE_BASE_URL
        
    def save_to_db(self, table_name, data):
        """
        Supabase 테이블에 데이터 저장
        
        Args:
            table_name (str): 저장할 테이블명
            data (dict): 저장할 데이터
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.api_key:
            return False, "Supabase API 키가 설정되지 않았습니다."
            
        if not self.base_url:
            return False, "Supabase Base URL이 설정되지 않았습니다."
            
        url = f"{self.base_url}/rest/v1/{table_name}"
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        try:
            # 데이터가 리스트인 경우 배치 삽입
            if isinstance(data, list):
                response = requests.post(url, headers=headers, json=data)
            else:
                response = requests.post(url, headers=headers, json=[data])
                
            if response.status_code in [200, 201]:
                return True, "데이터베이스 저장 성공"
            else:
                return False, f"데이터베이스 저장 실패: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"데이터베이스 연결 실패: {str(e)}"
    
    def create_table_data(self, api_type, endpoint_name, raw_data):
        """
        API 응답 데이터를 DB 저장용 형태로 변환
        
        Args:
            api_type (str): API 타입 (greentour, barrier_free, base_tour)
            endpoint_name (str): 엔드포인트 이름 (areaCode1, areaBasedList1 등)
            raw_data (dict): 원본 API 응답 데이터
            
        Returns:
            list: DB 저장용 데이터 리스트
        """
        table_data = []
        
        try:
            if api_type == "base_tour":
                # base_tour는 이미 통합된 형태
                items = raw_data.get("items", [])
                for item in items:
                    table_data.append({
                        "api_type": api_type,
                        "endpoint_name": endpoint_name,
                        "data": json.dumps(item, ensure_ascii=False),
                        "created_at": "now()"
                    })
            else:
                # 다른 API들은 표준 구조 가정
                response_body = raw_data.get("response", {}).get("body", {})
                items = response_body.get("items", {}).get("item", [])
                
                if not isinstance(items, list):
                    items = [items] if items else []
                    
                for item in items:
                    table_data.append({
                        "api_type": api_type,
                        "endpoint_name": endpoint_name, 
                        "data": json.dumps(item, ensure_ascii=False),
                        "created_at": "now()"
                    })
                    
        except Exception as e:
            print(f"데이터 변환 실패: {str(e)}")
            
        return table_data
