# 한국관광공사_무장애 여행 정보
# https://www.data.go.kr/data/15101897/openapi.do

import requests
import json
from settings.config import API_CONFIGS, COMMON_PARAMS, fetch_all_pages

class BarrierFreeAPI:
    def __init__(self):
        self.config = API_CONFIGS["barrier_free"]
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
            "1": ("지역코드조회", "/areaCode2"),
            "2": ("서비스분류코드조회", "/categoryCode2"),
            "3": ("분류체계 코드조회", "/lclsSystmCode2"),
            "4": ("법정동코드조회", "/ldongCode2"),
            "5": ("지역기반 관광정보조회", "/areaBasedList2"),
            "6": ("무장애 여행정보 동기화 목록 조회", "/areaBasedSyncList2")
        }
    
    def get_optional_params(self, endpoint_id):
        optional_params = {
            "1": {},  # 지역코드조회
            "2": {    # 서비스분류코드조회 - 새로 추가된 엔드포인트
                # "contentTypeId": "12",  # 관광타입 (12:관광지, 14:문화시설, 15:축제공연행사, 25:여행코스, 28:레포츠, 32:숙박, 38:쇼핑, 39:음식점)
                # "cat1": "",             # 대분류 코드 (선택사항)
                # "cat2": "",             # 중분류 코드 (cat1 필수)
                # "cat3": ""              # 소분류 코드 (cat1, cat2 필수)
            },
            "3": {    # 분류체계 코드조회
                "arrange": "C",
                "areaCode": "35",
                "lclsSystmListYn": "Y"  # 새로 추가된 파라미터
            },
            "4": {
                "lDongRegnCd": "35",
                "lDongListYn": "Y"
            },  # 법정동코드조회
            "5": {    # 지역기반 관광정보조회
                "arrange": "C",
                "areaCode": "35"
            },
            "6": {    # 무장애 여행정보 동기화 목록 조회
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
