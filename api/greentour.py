# 	한국관광공사_생태 관광 정보
# https://www.data.go.kr/data/15101908/openapi.do

import requests
import json
from settings.config import API_CONFIGS, COMMON_PARAMS, fetch_all_pages

class GreenTourAPI:
    def __init__(self):
        self.config = API_CONFIGS["greentour"]
        self.base_url = self.config["base_url"]
        
    def get_common_params(self):
        params = COMMON_PARAMS.copy()
        params.update({
            "MobileApp": self.config["app_name"],
            "serviceKey": self.config["service_key"]
        })
        return params
    
    def get_endpoints(self):
        return {
            "1": ("지역코드조회", "/areaCode1"),
            "2": ("지역기반 생태관광정보 조회", "/areaBasedList1"),
            "3": ("생태관광정보 동기화 관광정보 조회", "/areaBasedSyncList1")
        }
    
    def get_optional_params(self, endpoint_id):
        optional_params = {
            "1": {},
            "2": {
                "arrange": "C",
                "areaCode": "35"
            },
            "3": {
                "arrange": "C", 
                "areaCode": "35"
            }
        }
        return optional_params.get(endpoint_id, {})
    
    def call_api(self, endpoint_id):
        endpoints = self.get_endpoints()
        if endpoint_id not in endpoints:
            return None, f"잘못된 엔드포인트 ID: {endpoint_id}"
            
        desc, endpoint_path = endpoints[endpoint_id]
        
        params = self.get_common_params()
        params.update(self.get_optional_params(endpoint_id))
        
        # 페이징 처리로 모든 데이터 가져오기
        all_items, error = fetch_all_pages(self.base_url, endpoint_path, params)
        
        if error:
            return None, error
            
        # 표준 응답 형태로 반환
        result = {
            "response": {
                "body": {
                    "totalCount": len(all_items),
                    "items": {
                        "item": all_items
                    }
                }
            }
        }
        
        return result, None
