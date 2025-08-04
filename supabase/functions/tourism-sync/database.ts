import { SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { DataMapper } from './data-mapper.ts'

interface SyncStats {
  total: number
  new: number
  updated: number
}

export class DatabaseHandler {
  private supabase: SupabaseClient
  private mapper: DataMapper
  
  constructor(supabase: SupabaseClient) {
    this.supabase = supabase
    this.mapper = new DataMapper()
  }
  
  async syncData(apiType: string, mappedItems: any[]): Promise<SyncStats> {
    const tableName = this.mapper.getTableName(apiType)
    const keyFields = this.mapper.getKeyFields(apiType)
    
    console.log(`🔄 Syncing ${mappedItems.length} items to ${tableName}`)
    
    const stats: SyncStats = {
      total: mappedItems.length,
      new: 0,
      updated: 0
    }
    
    if (mappedItems.length === 0) {
      await this.logSyncResult(apiType, tableName, stats, 'SUCCESS')
      return stats
    }
    
    try {
      // 기존 데이터 조회
      const existingData = await this.getExistingData(tableName, keyFields)
      const existingMap = this.createExistingMap(existingData, keyFields)
      
      console.log(`📊 Found ${existingData.length} existing records`)
      
      // 배치 처리를 위한 배열
      const toInsert: any[] = []
      const toUpdate: any[] = []
      
      // 각 아이템 처리
      for (const item of mappedItems) {
        try {
          const keyValue = this.getKeyValue(item, keyFields)
          const existing = existingMap.get(keyValue)
          
          if (existing) {
            // 해시 비교하여 변경 여부 확인
            if (existing.data_hash !== item.data_hash) {
              toUpdate.push({
                id: existing.id,
                ...item,
                updated_at: new Date().toISOString()
              })
            }
          } else {
            // 신규 데이터
            toInsert.push(item)
          }
        } catch (error) {
          console.warn(`⚠️  Failed to process item:`, error.message)
        }
      }
      
      // 배치 삽입
      if (toInsert.length > 0) {
        await this.batchInsert(tableName, toInsert)
        stats.new = toInsert.length
        console.log(`✅ Inserted ${toInsert.length} new records`)
      }
      
      // 배치 업데이트
      if (toUpdate.length > 0) {
        await this.batchUpdate(tableName, toUpdate)
        stats.updated = toUpdate.length
        console.log(`✅ Updated ${toUpdate.length} records`)
      }
      
      // 동기화 로그 기록
      await this.logSyncResult(apiType, tableName, stats, 'SUCCESS')
      
      return stats
      
    } catch (error) {
      console.error(`❌ Sync failed for ${apiType}:`, error.message)
      await this.logSyncResult(apiType, tableName, stats, 'FAILED', error.message)
      throw error
    }
  }
  
  private async getExistingData(tableName: string, keyFields: string | string[]) {
    const selectFields = Array.isArray(keyFields) 
      ? `id, ${keyFields.join(', ')}, data_hash`
      : `id, ${keyFields}, data_hash`
    
    const { data, error } = await this.supabase
      .from(tableName)
      .select(selectFields)
    
    if (error) {
      throw new Error(`Failed to fetch existing data: ${error.message}`)
    }
    
    return data || []
  }
  
  private createExistingMap(existingData: any[], keyFields: string | string[]): Map<string, any> {
    const map = new Map()
    
    for (const item of existingData) {
      const keyValue = this.getKeyValue(item, keyFields)
      map.set(keyValue, item)
    }
    
    return map
  }
  
  private getKeyValue(item: any, keyFields: string | string[]): string {
    if (Array.isArray(keyFields)) {
      return keyFields.map(field => String(item[field] || '')).join('_')
    } else {
      return String(item[keyFields] || '')
    }
  }
  
  private async batchInsert(tableName: string, items: any[], batchSize = 100) {
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize)
      
      const { error } = await this.supabase
        .from(tableName)
        .insert(batch)
      
      if (error) {
        throw new Error(`Batch insert failed: ${error.message}`)
      }
      
      console.log(`📦 Inserted batch ${Math.floor(i / batchSize) + 1}: ${batch.length} items`)
    }
  }
  
  private async batchUpdate(tableName: string, items: any[], batchSize = 100) {
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize)
      
      // Supabase는 배치 업데이트를 직접 지원하지 않으므로 upsert 사용
      const { error } = await this.supabase
        .from(tableName)
        .upsert(batch, { onConflict: 'id' })
      
      if (error) {
        throw new Error(`Batch update failed: ${error.message}`)
      }
      
      console.log(`📦 Updated batch ${Math.floor(i / batchSize) + 1}: ${batch.length} items`)
    }
  }
  
  private async logSyncResult(
    apiType: string, 
    tableName: string, 
    stats: SyncStats, 
    status: 'SUCCESS' | 'FAILED',
    errorMessage?: string
  ) {
    try {
      const logData = {
        api_type: apiType,
        table_name: tableName,
        sync_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
        total_items: stats.total,
        new_items: stats.new,
        updated_items: stats.updated,
        status,
        error_message: errorMessage || null,
        completed_at: new Date().toISOString(),
        execution_time_seconds: 0 // Edge Function에서는 개별 API 시간 측정 어려움
      }
      
      const { error } = await this.supabase
        .from('sync_logs')
        .insert(logData)
      
      if (error) {
        console.warn('⚠️  Failed to log sync result:', error.message)
      } else {
        console.log(`📝 Sync log recorded for ${apiType}`)
      }
    } catch (error) {
      console.warn('⚠️  Failed to log sync result:', error.message)
    }
  }
  
  // 헬스 체크용 메서드
  async testConnection(): Promise<boolean> {
    try {
      const { data, error } = await this.supabase
        .from('sync_logs')
        .select('id')
        .limit(1)
      
      return !error
    } catch (error) {
      console.error('Database connection test failed:', error.message)
      return false
    }
  }
  
  // 통계 조회용 메서드
  async getRecentSyncStats(days = 7) {
    try {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days)
      
      const { data, error } = await this.supabase
        .from('sync_logs')
        .select('*')
        .gte('sync_date', cutoffDate.toISOString().split('T')[0])
        .order('sync_date', { ascending: false })
      
      if (error) {
        throw new Error(`Failed to fetch sync stats: ${error.message}`)
      }
      
      return data || []
    } catch (error) {
      console.warn('Failed to fetch sync stats:', error.message)
      return []
    }
  }
}
