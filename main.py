#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

from api.greentour import GreenTourAPI
from api.barrier_free import BarrierFreeAPI  
from api.base_tour import BaseTourAPI
from batch.supabase_handler import SupabaseHandler

class TourismCrawler:
    def __init__(self):
        self.apis = {
            "1": ("생태 관광 정보 API", GreenTourAPI()),
            "2": ("무장애 여행 정보 API", BarrierFreeAPI()),
            "3": ("기초지자체 중심 관광지 정보 API", BaseTourAPI())
        }
        self.supabase = SupabaseHandler()
        
    def show_api_menu(self):
        print("=== 관광 데이터 크롤러 ===\n")
        for key, (desc, _) in self.apis.items():
            print(f"{key}. {desc}")
        print()
        
    def show_endpoint_menu(self, api_key):
        if api_key not in self.apis:
            return
            
        desc, api_instance = self.apis[api_key]
        endpoints = api_instance.get_endpoints()
        
        print(f"\n=== {desc} 엔드포인트 ===")
        for key, (endpoint_desc, endpoint_path) in endpoints.items():
            print(f"{key}. {endpoint_desc}({endpoint_path})")
        print()
        
    def save_to_local(self, api_key, endpoint_id, api_type, endpoint_path, data):
        """로컬 data 디렉토리에 JSON 파일 저장"""
        if not os.path.exists("data"):
            os.makedirs("data")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 엔드포인트 경로에서 '/' 제거하여 파일명으로 사용
        endpoint_name = endpoint_path.lstrip('/')
        # API 번호와 엔드포인트 번호를 포함한 파일명 생성
        filename = f"data/{api_key}{api_type}_{endpoint_id}{endpoint_name}_{timestamp}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[로컬 저장 완료] {filename}")
            return True
        except Exception as e:
            print(f"[로컬 저장 실패] {str(e)}")
            return False
            
    def save_to_supabase(self, api_key, endpoint_id, api_type, endpoint_path, data):
        """Supabase DB에 데이터 저장 - areaBasedList 전용 처리 추가"""
        endpoint_name = endpoint_path.lstrip('/')
        
        # areaBasedList 엔드포인트인지 확인
        if "areaBasedList" in endpoint_name:
            return self.save_areabased_to_supabase(api_key, endpoint_id, api_type, data)
        else:
            # 기존 방식 (일반 테이블)
            table_identifier = f"{api_key}{api_type}_{endpoint_id}{endpoint_name}"
            table_data = self.supabase.create_table_data(table_identifier, endpoint_name, data)
            
            if not table_data:
                print("[DB 저장 실패] 변환할 데이터가 없습니다.")
                return False
                
            success, message = self.supabase.save_to_db("tourism_data", table_data)
            print(f"[DB 저장] {message}")
            return success
    
    def save_areabased_to_supabase(self, api_key, endpoint_id, api_type, data):
        """areaBasedList 데이터를 전용 테이블에 저장"""
        try:
            from sync.areabased_sync import AreaBasedSynchronizer
            
            print(f"[areaBasedList DB 저장] {api_type} 데이터 처리 중...")
            
            # API 키를 실제 타입으로 매핑
            api_type_mapping = {
                "1": "greentour",      # 생태관광 API
                "2": "barrier_free",   # 무장애 여행 API  
                "3": "base_tour"       # 중심 관광지 API
            }
            
            actual_api_type = api_type_mapping.get(api_key, api_type)
            
            # 임시 파일 생성하여 동기화 로직 재사용
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name
            
            try:
                # AreaBasedSynchronizer를 사용하여 DB 저장
                synchronizer = AreaBasedSynchronizer()
                success = synchronizer.sync_from_file(temp_file_path, actual_api_type)
                
                if success:
                    print(f"[areaBasedList DB 저장 완료] {actual_api_type}")
                    return True
                else:
                    print(f"[areaBasedList DB 저장 실패] {actual_api_type}")
                    return False
                    
            finally:
                # 임시 파일 정리
                import os
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"[areaBasedList DB 저장 실패] {str(e)}")
            return False
        
    def run_interactive(self):
        """대화형 모드 실행"""
        self.show_api_menu()
        api_key = input("API를 선택하세요: ").strip()
        
        if api_key not in self.apis:
            print("잘못된 API 선택입니다.")
            return
            
        self.show_endpoint_menu(api_key)
        endpoint_id = input("엔드포인트를 선택하세요: ").strip()
        
        # 기본값 설정: 로컬 저장 T, DB 저장 F
        save_local_input = input("로컬 저장하시겠습니까? (T/F, 기본값: T): ").strip().upper()
        save_local = True if save_local_input == '' or save_local_input == 'T' else False
        
        save_db_input = input("DB 저장하시겠습니까? (T/F, 기본값: F): ").strip().upper()
        save_db = True if save_db_input == 'T' else False
        
        print(f"\n[설정] 로컬 저장: {'T' if save_local else 'F'}, DB 저장: {'T' if save_db else 'F'}")
        
        self.execute_crawling(api_key, endpoint_id, save_local, save_db)
        
    def run_cli(self, args):
        """CLI 모드 실행 - 부분 입력 지원"""
        # API 선택
        if len(args) >= 1:
            api_key = args[0]
        else:
            self.show_api_menu()
            api_key = input("API를 선택하세요: ").strip()
        
        if api_key not in self.apis:
            print(f"잘못된 API 번호: {api_key}")
            return
        
        # 엔드포인트 선택
        if len(args) >= 2:
            endpoint_id = args[1]
        else:
            self.show_endpoint_menu(api_key)
            endpoint_id = input("엔드포인트를 선택하세요: ").strip()
        
        # 로컬 저장 선택
        if len(args) >= 3:
            save_local = args[2].upper() == 'T'
        else:
            save_local_input = input("로컬 저장하시겠습니까? (T/F, 기본값: T): ").strip().upper()
            save_local = True if save_local_input == '' or save_local_input == 'T' else False
        
        # DB 저장 선택
        if len(args) >= 4:
            save_db = args[3].upper() == 'T'
        else:
            save_db_input = input("DB 저장하시겠습니까? (T/F, 기본값: F): ").strip().upper()
            save_db = True if save_db_input == 'T' else False
        
        # CLI에서 부분 입력된 경우 설정 확인 표시
        if len(args) < 4:
            print(f"\n[설정] 로컬 저장: {'T' if save_local else 'F'}, DB 저장: {'T' if save_db else 'F'}")
        
        self.execute_crawling(api_key, endpoint_id, save_local, save_db)
        
    def execute_crawling(self, api_key, endpoint_id, save_local, save_db):
        """크롤링 실행"""
        if api_key not in self.apis:
            print(f"잘못된 API 번호: {api_key}")
            return
            
        desc, api_instance = self.apis[api_key]
        endpoints = api_instance.get_endpoints()
        
        if endpoint_id not in endpoints:
            print(f"잘못된 엔드포인트 번호: {endpoint_id}")
            return
            
        endpoint_desc, endpoint_path = endpoints[endpoint_id]
        print(f"\n[실행] {desc} - {endpoint_desc}({endpoint_path})")
        
        # API 호출
        data, error = api_instance.call_api(endpoint_id)
        
        if error:
            print(f"[API 호출 실패] {error}")
            return
            
        print("[API 호출 성공]")
        
        # 데이터 저장
        api_type_map = {"1": "greentour", "2": "barrier_free", "3": "base_tour"}
        api_type = api_type_map[api_key]
        
        if save_local:
            self.save_to_local(api_key, endpoint_id, api_type, endpoint_path, data)
            
        if save_db:
            self.save_to_supabase(api_key, endpoint_id, api_type, endpoint_path, data)

def main():
    crawler = TourismCrawler()
    
    if len(sys.argv) > 1:
        # CLI 모드
        crawler.run_cli(sys.argv[1:])
    else:
        # 대화형 모드
        crawler.run_interactive()

if __name__ == "__main__":
    main()
