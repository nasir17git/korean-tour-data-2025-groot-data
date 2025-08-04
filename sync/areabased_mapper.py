#!/usr/bin/env python3
from sync.hash_utils import calculate_data_hash

class AreaBasedMapper:
    """areaBasedList 데이터를 DB 테이블 구조로 매핑 (소문자)"""
    
    @staticmethod
    def get_table_name(api_type):
        """API 타입별 테이블명 반환"""
        table_map = {
            "greentour": "greentour_areabased",
            "barrier_free": "barrier_free_areabased", 
            "base_tour": "base_tour_areabased"
        }
        return table_map.get(api_type)
    
    @staticmethod
    def get_key_field(api_type):
        """API 타입별 키 필드명 반환 (소문자)"""
        if api_type == "base_tour":
            return ["hubtatscode", "baseym"]  # 복합 키
        else:
            return "contentid"
    
    @staticmethod
    def map_greentour_data(item):
        """생태관광 areaBasedList 데이터 매핑 (소문자 컬럼명)"""
        try:
            return {
                'contentid': str(item.get('contentid', '')),
                'areacode': item.get('areacode'),
                'sigungucode': item.get('sigungucode'),
                'title': item.get('title'),
                'addr': item.get('addr'),
                'tel': item.get('tel'),
                'telname': item.get('telname'),
                'mainimage': item.get('mainimage'),
                'summary': item.get('summary'),
                'createdtime': item.get('createdtime'),
                'modifiedtime': item.get('modifiedtime'),
                'cpyrhtdivcd': item.get('cpyrhtDivCd'),  # API는 카멜케이스, DB는 소문자
                'data_hash': calculate_data_hash(item),
                'raw_data': item
            }
        except Exception as e:
            print(f"⚠️  생태관광 데이터 매핑 실패: {str(e)}")
            return None
    
    @staticmethod
    def map_barrier_free_data(item):
        """무장애 여행 areaBasedList 데이터 매핑 (소문자 컬럼명)"""
        try:
            return {
                'contentid': str(item.get('contentid', '')),
                'contenttypeid': item.get('contenttypeid'),
                'areacode': item.get('areacode'),
                'sigungucode': item.get('sigungucode'),
                'cat1': item.get('cat1'),
                'cat2': item.get('cat2'),
                'cat3': item.get('cat3'),
                'title': item.get('title'),
                'addr1': item.get('addr1'),
                'addr2': item.get('addr2'),
                'tel': item.get('tel'),
                'firstimage': item.get('firstimage'),
                'firstimage2': item.get('firstimage2'),
                'mapx': float(item.get('mapx', 0)) if item.get('mapx') else None,
                'mapy': float(item.get('mapy', 0)) if item.get('mapy') else None,
                'mlevel': int(item.get('mlevel', 0)) if item.get('mlevel') else None,
                'zipcode': item.get('zipcode'),
                'createdtime': item.get('createdtime'),
                'modifiedtime': item.get('modifiedtime'),
                'cpyrhtdivcd': item.get('cpyrhtDivCd'),  # API는 카멜케이스, DB는 소문자
                'lclssystm1': item.get('lclsSystm1'),    # API는 카멜케이스, DB는 소문자
                'lclssystm2': item.get('lclsSystm2'),
                'lclssystm3': item.get('lclsSystm3'),
                'ldongregn_cd': item.get('lDongRegnCd'),  # API는 카멜케이스, DB는 소문자
                'ldongsigngu_cd': item.get('lDongSignguCd'),
                'data_hash': calculate_data_hash(item),
                'raw_data': item
            }
        except Exception as e:
            print(f"⚠️  무장애 여행 데이터 매핑 실패: {str(e)}")
            return None
    
    @staticmethod
    def map_base_tour_data(item):
        """중심 관광지 areaBasedList 데이터 매핑 (소문자 컬럼명)"""
        try:
            return {
                'hubtatscode': str(item.get('hubTatsCd', '')),    # API는 카멜케이스, DB는 소문자
                'baseym': item.get('baseYm'),                     # API는 카멜케이스, DB는 소문자
                'areacd': item.get('areaCd'),
                'areanm': item.get('areaNm'),
                'signgucd': item.get('signguCd'),
                'signgunm': item.get('signguNm'),
                'hubtatsname': item.get('hubTatsNm'),
                'hubctgrylclsnm': item.get('hubCtgryLclsNm'),
                'hubctgrymclsnm': item.get('hubCtgryMclsNm'),
                'hubrank': int(item.get('hubRank', 0)) if item.get('hubRank') else None,
                'mapx': float(item.get('mapX', 0)) if item.get('mapX') else None,
                'mapy': float(item.get('mapY', 0)) if item.get('mapY') else None,
                'data_hash': calculate_data_hash(item),
                'raw_data': item
            }
        except Exception as e:
            print(f"⚠️  중심 관광지 데이터 매핑 실패: {str(e)}")
            return None
    
    @staticmethod
    def map_item_data(api_type, item):
        """API 타입별 데이터 매핑 통합 메서드"""
        if api_type == "greentour":
            return AreaBasedMapper.map_greentour_data(item)
        elif api_type == "barrier_free":
            return AreaBasedMapper.map_barrier_free_data(item)
        elif api_type == "base_tour":
            return AreaBasedMapper.map_base_tour_data(item)
        else:
            print(f"❌ 알 수 없는 API 타입: {api_type}")
            return None
