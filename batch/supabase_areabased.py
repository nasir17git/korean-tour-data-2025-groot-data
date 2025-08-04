#!/usr/bin/env python3
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from sync.areabased_mapper import AreaBasedMapper

class SupabaseAreaBasedHandler:
    def __init__(self):
        # 환경 변수 로드
        load_dotenv()
        
        # Supabase 클라이언트 생성
        self.client = create_client(
            os.getenv("SUPABASE_BASE_URL"),
            os.getenv("SUPABASE_API_KEY")
        )
        self.mapper = AreaBasedMapper()
    
    def get_existing_data(self, table_name, key_field):
        """기존 데이터 조회"""
        try:
            if isinstance(key_field, list):
                # 복합 키인 경우 모든 키 필드와 data_hash 조회
                select_fields = "id, " + ", ".join(key_field) + ", data_hash"
            else:
                # 단일 키인 경우
                select_fields = f"id, {key_field}, data_hash"
            
            response = self.client.table(table_name)\
                .select(select_fields)\
                .execute()
            return response.data
        except Exception as e:
            print(f"❌ 기존 데이터 조회 실패: {str(e)}")
            return []
    
    def insert_record(self, table_name, data):
        """신규 레코드 삽입"""
        try:
            response = self.client.table(table_name).insert(data).execute()
            return response.data
        except Exception as e:
            print(f"❌ 레코드 삽입 실패: {str(e)}")
            raise e
    
    def update_record(self, table_name, record_id, data):
        """기존 레코드 업데이트"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            response = self.client.table(table_name)\
                .update(data)\
                .eq("id", record_id)\
                .execute()
            return response.data
        except Exception as e:
            print(f"❌ 레코드 업데이트 실패: {str(e)}")
            raise e
    
    def batch_upsert(self, table_name, data_list, batch_size=100):
        """배치 업서트"""
        try:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                self.client.table(table_name).upsert(batch).execute()
                print(f"  📦 배치 {i//batch_size + 1}: {len(batch)}개 처리")
        except Exception as e:
            print(f"❌ 배치 업서트 실패: {str(e)}")
            raise e
    
    def log_sync_result(self, api_type, table_name, stats):
        """동기화 결과 로그"""
        try:
            log_data = {
                'api_type': api_type,
                'table_name': table_name,
                'sync_date': datetime.now().date().isoformat(),
                'total_items': stats.get('total', 0),
                'new_items': stats.get('new', 0),
                'updated_items': stats.get('updated', 0),
                'status': 'SUCCESS' if stats.get('success', True) else 'FAILED',
                'error_message': stats.get('error_message'),
                'completed_at': datetime.now().isoformat(),
                'execution_time_seconds': stats.get('execution_time', 0)
            }
            
            self.client.table('sync_logs').insert(log_data).execute()
            print(f"✅ 동기화 로그 기록 완료")
            
        except Exception as e:
            print(f"⚠️  동기화 로그 기록 실패: {str(e)}")
    
    def get_table_stats(self, table_name):
        """테이블 통계 조회"""
        try:
            response = self.client.table(table_name)\
                .select("id", count="exact")\
                .execute()
            return response.count
        except Exception as e:
            print(f"⚠️  테이블 통계 조회 실패: {str(e)}")
            return 0
    
    def test_connection(self):
        """연결 테스트"""
        try:
            # 간단한 쿼리로 연결 테스트
            response = self.client.table('sync_logs')\
                .select("id")\
                .limit(1)\
                .execute()
            return True
        except Exception as e:
            print(f"❌ Supabase 연결 실패: {str(e)}")
            return False
