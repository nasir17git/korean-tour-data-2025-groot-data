#!/usr/bin/env python3
import json
import os
from datetime import datetime
from batch.supabase_areabased import SupabaseAreaBasedHandler
from sync.areabased_mapper import AreaBasedMapper

class AreaBasedSynchronizer:
    def __init__(self):
        self.supabase = SupabaseAreaBasedHandler()
        self.mapper = AreaBasedMapper()
    
    def sync_from_file(self, file_path, api_type):
        """파일에서 데이터를 읽어 DB에 동기화"""
        start_time = datetime.now()
        
        try:
            print(f"🔄 {api_type} 동기화 시작: {file_path}")
            
            # Supabase 연결 테스트
            if not self.supabase.test_connection():
                return False
            
            # 파일 읽기
            print("📖 파일 읽는 중...")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 데이터 추출
            items = self.extract_items(data, api_type)
            
            if not items:
                print(f"❌ {file_path}에서 데이터를 찾을 수 없습니다.")
                return False
            
            print(f"📊 추출된 데이터: {len(items)}개")
            
            # 데이터 매핑
            print("🔄 데이터 매핑 중...")
            mapped_items = []
            failed_count = 0
            
            for i, item in enumerate(items):
                mapped_item = self.mapper.map_item_data(api_type, item)
                if mapped_item:
                    mapped_items.append(mapped_item)
                else:
                    failed_count += 1
                
                # 진행 상황 표시 (100개마다)
                if (i + 1) % 100 == 0:
                    print(f"  📝 매핑 진행: {i + 1}/{len(items)}")
            
            if failed_count > 0:
                print(f"⚠️  매핑 실패: {failed_count}개")
            
            print(f"✅ 매핑 완료: {len(mapped_items)}개")
            
            # DB 동기화
            table_name = self.mapper.get_table_name(api_type)
            stats = self.process_data_changes(table_name, api_type, mapped_items)
            
            # 실행 시간 계산
            execution_time = (datetime.now() - start_time).total_seconds()
            stats['execution_time'] = int(execution_time)
            stats['success'] = True
            
            # 로그 기록
            self.supabase.log_sync_result(api_type, table_name, stats)
            
            print(f"🎉 {api_type} 동기화 완료!")
            print(f"   📊 총 {stats['total']}개 중 신규 {stats['new']}개, 업데이트 {stats['updated']}개")
            print(f"   ⏱️  실행 시간: {execution_time:.2f}초")
            
            return True
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            print(f"❌ {api_type} 동기화 실패: {error_msg}")
            
            # 실패 로그 기록
            try:
                table_name = self.mapper.get_table_name(api_type)
                error_stats = {
                    'total': 0,
                    'new': 0,
                    'updated': 0,
                    'execution_time': int(execution_time),
                    'success': False,
                    'error_message': error_msg
                }
                self.supabase.log_sync_result(api_type, table_name, error_stats)
            except:
                pass
            
            return False
    
    def extract_items(self, data, api_type):
        """API 타입별 데이터 추출"""
        try:
            if api_type == "base_tour":
                # base_tour는 직접 items 배열
                return data.get('items', [])
            else:
                # greentour, barrier_free는 response.body.items.item 구조
                if 'response' in data and 'body' in data['response']:
                    body = data['response']['body']
                    if 'items' in body and 'item' in body['items']:
                        items = body['items']['item']
                        return items if isinstance(items, list) else [items]
            return []
        except Exception as e:
            print(f"❌ 데이터 추출 실패: {str(e)}")
            return []
    
    def process_data_changes(self, table_name, api_type, new_items):
        """데이터 변경사항 처리"""
        print(f"🔄 DB 동기화 시작: {table_name}")
        
        stats = {'total': len(new_items), 'new': 0, 'updated': 0}
        
        # 키 필드 결정
        key_field = self.mapper.get_key_field(api_type)
        
        # 기존 데이터 조회
        print("📋 기존 데이터 조회 중...")
        existing_data = self.supabase.get_existing_data(table_name, key_field)
        
        # 복합 키 처리
        if isinstance(key_field, list):
            # 복합 키인 경우 (base_tour)
            existing_dict = {}
            for item in existing_data:
                composite_key = "_".join([str(item[field]) for field in key_field])
                existing_dict[composite_key] = item
        else:
            # 단일 키인 경우 (greentour, barrier_free)
            existing_dict = {str(item[key_field]): item for item in existing_data}
        
        print(f"📊 기존 데이터: {len(existing_dict)}개")
        
        # 신규/업데이트 처리
        print("🔄 데이터 변경사항 처리 중...")
        
        for i, item in enumerate(new_items):
            try:
                # 키 값 생성
                if isinstance(key_field, list):
                    # 복합 키인 경우
                    key_value = "_".join([str(item[field]) for field in key_field])
                else:
                    # 단일 키인 경우
                    key_value = str(item[key_field])
                
                if key_value in existing_dict:
                    # 기존 데이터와 해시 비교
                    if existing_dict[key_value]['data_hash'] != item['data_hash']:
                        self.supabase.update_record(table_name, existing_dict[key_value]['id'], item)
                        stats['updated'] += 1
                else:
                    # 신규 데이터
                    self.supabase.insert_record(table_name, item)
                    stats['new'] += 1
                
                # 진행 상황 표시 (100개마다)
                if (i + 1) % 100 == 0:
                    print(f"  💾 처리 진행: {i + 1}/{len(new_items)} (신규: {stats['new']}, 업데이트: {stats['updated']})")
                    
            except Exception as e:
                print(f"⚠️  데이터 처리 실패 ({key_value}): {str(e)}")
                continue
        
        print(f"✅ 데이터 처리 완료: 신규 {stats['new']}개, 업데이트 {stats['updated']}개")
        return stats
    
    def get_file_info(self, file_path):
        """파일 정보 조회"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'exists': True
            }
        except Exception as e:
            print(f"⚠️  파일 정보 조회 실패: {str(e)}")
            return None
