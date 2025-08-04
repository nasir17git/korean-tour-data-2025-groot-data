# 한국관광공사_기초지자체 중심 관광지 정보
# https://www.data.go.kr/data/15128559/openapi.do

import requests
import json
import time
from settings.config import API_CONFIGS, COMMON_PARAMS

class BaseTourAPI:
    def __init__(self):
        self.config = API_CONFIGS["base_tour"]
        self.base_url = self.config["base_url"]
        
    def get_common_params(self):
        params = COMMON_PARAMS.copy()
        params.update({
            "MobileApp": self.config["app_name"],
            "serviceKey": self.config["service_key"],
            "baseYm": "202503",
            "areaCd": "47"
        })
        return params
    
    def get_endpoints(self):
        return {
            "1": ("지역기반 중심 관광지 정보 목록 조회", "/areaBasedList1")
        }
    
    def get_signgu_list(self):
        """경상북도 시군구 코드 목록"""
        return [
            "47111", "47113", "47130", "47150", "47170", "47190", "47210",
            "47230", "47250", "47280", "47290", "47730", "47750", "47760", 
            "47770", "47820", "47830", "47840", "47850", "47900", "47920",
            "47930", "47940"
        ]
    
    def fetch_signgu_data(self, signgu_code, endpoint_path, base_params):
        """특정 시군구의 모든 페이지 데이터 수집"""
        all_items = []
        page_no = 1
        max_pages = 50
        
        while page_no <= max_pages:
            params = base_params.copy()
            params["signguCd"] = signgu_code
            params["pageNo"] = str(page_no)
            
            url = self.base_url + endpoint_path
            
            try:
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    print(f"[경고] 시군구 {signgu_code} 페이지 {page_no} HTTP {response.status_code} 오류")
                    break
                    
                data = response.json()
                
                # 응답 구조 확인
                response_body = data.get("response", {}).get("body", {})
                total_count = response_body.get("totalCount", 0)
                items = response_body.get("items", {})
                
                # items가 없거나 빈 경우 종료
                if not items:
                    break
                    
                # item 추출
                if isinstance(items, dict):
                    item_list = items.get("item", [])
                else:
                    item_list = items
                    
                if not isinstance(item_list, list):
                    item_list = [item_list] if item_list else []
                    
                if not item_list:
                    break
                    
                all_items.extend(item_list)
                
                # 첫 페이지에서 총 개수 확인하여 페이징 여부 판단
                if page_no == 1:
                    if total_count <= 100:
                        # 100개 이하면 페이징 불필요
                        print(f"[{signgu_code}] 데이터 항목 수: {len(item_list)} (전체)")
                        break
                    else:
                        print(f"[{signgu_code}] 페이지 {page_no}: {len(item_list)}개 수집 (총 {len(all_items)}개, 전체 {total_count}개)")
                else:
                    print(f"[{signgu_code}] 페이지 {page_no}: {len(item_list)}개 수집 (총 {len(all_items)}개)")
                
                # 전체 데이터를 다 가져왔는지 확인
                if len(all_items) >= total_count:
                    print(f"[{signgu_code}] 완료: 전체 {total_count}개 데이터 수집 완료")
                    break
                    
                # 다음 페이지로
                page_no += 1
                
                # API 호출 간격
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[경고] 시군구 {signgu_code} 페이지 {page_no} 처리 실패: {str(e)}")
                break
        
        return all_items
    
    def call_api(self, endpoint_id):
        endpoints = self.get_endpoints()
        if endpoint_id not in endpoints:
            return None, f"잘못된 엔드포인트 ID: {endpoint_id}"
            
        desc, endpoint_path = endpoints[endpoint_id]
        base_params = self.get_common_params()
        signgu_list = self.get_signgu_list()
        
        all_items = []
        
        for signgu in signgu_list:
            signgu_items = self.fetch_signgu_data(signgu, endpoint_path, base_params)
            all_items.extend(signgu_items)
        
        # 통합 결과 반환
        result = {
            "areaCd": base_params["areaCd"],
            "totalCount": len(all_items),
            "items": all_items
        }
        
        print(f"\n[전체 완료] 총 {len(all_items)}개 데이터 수집 완료")
        
        return result, None
