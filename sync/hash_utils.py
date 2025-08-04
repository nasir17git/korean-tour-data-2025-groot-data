#!/usr/bin/env python3
import hashlib
import json

def calculate_data_hash(data):
    """데이터의 해시값 계산"""
    try:
        # 정렬된 JSON 문자열로 변환하여 일관된 해시 생성
        normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode()).hexdigest()
    except Exception as e:
        print(f"⚠️  해시 계산 실패: {str(e)}")
        # 실패 시 빈 문자열의 해시 반환
        return hashlib.sha256("".encode()).hexdigest()
