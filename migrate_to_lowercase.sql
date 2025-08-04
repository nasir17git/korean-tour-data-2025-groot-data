-- 소문자 스키마 마이그레이션 스크립트 (PostgreSQL 표준)
-- Supabase SQL Editor에서 실행하세요

-- 1. 기존 테이블 삭제 (데이터 손실 주의!)
DROP TABLE IF EXISTS greentour_areabased CASCADE;
DROP TABLE IF EXISTS barrier_free_areabased CASCADE;
DROP TABLE IF EXISTS base_tour_areabased CASCADE;
DROP TABLE IF EXISTS sync_logs CASCADE;

-- 2. 생태관광 데이터 테이블 (소문자)
CREATE TABLE greentour_areabased (
    id SERIAL PRIMARY KEY,
    contentid VARCHAR(100) NOT NULL,
    areacode VARCHAR(10),
    sigungucode VARCHAR(10),
    title VARCHAR(500),
    addr VARCHAR(1000),
    tel VARCHAR(50),
    telname VARCHAR(200),
    mainimage TEXT,
    summary TEXT,
    createdtime VARCHAR(20),
    modifiedtime VARCHAR(20),
    cpyrhtdivcd VARCHAR(20),
    data_hash VARCHAR(64) NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contentid)
);

-- 3. 무장애 여행 데이터 테이블 (소문자)
CREATE TABLE barrier_free_areabased (
    id SERIAL PRIMARY KEY,
    contentid VARCHAR(100) NOT NULL,
    contenttypeid VARCHAR(10),
    areacode VARCHAR(10),
    sigungucode VARCHAR(10),
    cat1 VARCHAR(10),
    cat2 VARCHAR(10), 
    cat3 VARCHAR(20),
    title VARCHAR(500),
    addr1 VARCHAR(500),
    addr2 VARCHAR(500),
    tel VARCHAR(50),
    firstimage TEXT,
    firstimage2 TEXT,
    mapx DECIMAL(20,10),
    mapy DECIMAL(20,10),
    mlevel INTEGER,
    zipcode VARCHAR(10),
    createdtime VARCHAR(20),
    modifiedtime VARCHAR(20),
    cpyrhtdivcd VARCHAR(20),
    -- 무장애 관련 분류 시스템
    lclssystm1 VARCHAR(10),
    lclssystm2 VARCHAR(10),
    lclssystm3 VARCHAR(20),
    ldongregn_cd VARCHAR(10),
    ldongsigngu_cd VARCHAR(10),
    data_hash VARCHAR(64) NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contentid)
);

-- 4. 중심 관광지 데이터 테이블 (소문자)
CREATE TABLE base_tour_areabased (
    id SERIAL PRIMARY KEY,
    hubtatscode VARCHAR(100) NOT NULL,
    baseym VARCHAR(10),
    areacd VARCHAR(10),
    areanm VARCHAR(100),
    signgucd VARCHAR(10),
    signgunm VARCHAR(100),
    hubtatsname VARCHAR(500),
    hubctgrylclsnm VARCHAR(100),
    hubctgrymclsnm VARCHAR(100),
    hubrank INTEGER,
    mapx DECIMAL(20,10),
    mapy DECIMAL(20,10),
    data_hash VARCHAR(64) NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(hubtatscode, baseym)
);

-- 5. 동기화 로그 테이블
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    api_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    sync_date DATE NOT NULL,
    total_items INTEGER DEFAULT 0,
    new_items INTEGER DEFAULT 0,
    updated_items INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'PARTIAL'
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_seconds INTEGER
);

-- 6. 인덱스 생성
-- 생태관광 인덱스
CREATE INDEX idx_greentour_contentid ON greentour_areabased(contentid);
CREATE INDEX idx_greentour_area ON greentour_areabased(areacode, sigungucode);
CREATE INDEX idx_greentour_hash ON greentour_areabased(data_hash);
CREATE INDEX idx_greentour_updated ON greentour_areabased(updated_at);

-- 무장애 여행 인덱스  
CREATE INDEX idx_barrier_free_contentid ON barrier_free_areabased(contentid);
CREATE INDEX idx_barrier_free_area ON barrier_free_areabased(areacode, sigungucode);
CREATE INDEX idx_barrier_free_category ON barrier_free_areabased(cat1, cat2, cat3);
CREATE INDEX idx_barrier_free_hash ON barrier_free_areabased(data_hash);
CREATE INDEX idx_barrier_free_updated ON barrier_free_areabased(updated_at);

-- 중심 관광지 인덱스
CREATE INDEX idx_base_tour_hub_cd ON base_tour_areabased(hubtatscode);
CREATE INDEX idx_base_tour_area ON base_tour_areabased(areacd, signgucd);
CREATE INDEX idx_base_tour_base_ym ON base_tour_areabased(baseym);
CREATE INDEX idx_base_tour_hash ON base_tour_areabased(data_hash);
CREATE INDEX idx_base_tour_updated ON base_tour_areabased(updated_at);

-- 동기화 로그 인덱스
CREATE INDEX idx_sync_logs_api_date ON sync_logs(api_type, sync_date);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);
CREATE INDEX idx_sync_logs_table ON sync_logs(table_name);

-- 7. RLS 정책 설정
-- 생태관광 테이블 RLS
ALTER TABLE greentour_areabased ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all operations for anon users" ON greentour_areabased
    FOR ALL USING (true);

-- 무장애 여행 테이블 RLS
ALTER TABLE barrier_free_areabased ENABLE ROW LEVEL SECURITY;  
CREATE POLICY "Enable all operations for anon users" ON barrier_free_areabased
    FOR ALL USING (true);

-- 중심 관광지 테이블 RLS
ALTER TABLE base_tour_areabased ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all operations for anon users" ON base_tour_areabased
    FOR ALL USING (true);

-- 동기화 로그 테이블 RLS
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all operations for anon users" ON sync_logs
    FOR ALL USING (true);

-- 8. 테이블 생성 확인
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('greentour_areabased', 'barrier_free_areabased', 'base_tour_areabased', 'sync_logs')
ORDER BY tablename;

-- 완료 메시지
SELECT '소문자 스키마 마이그레이션 완료! (총 4개 테이블)' as status;
