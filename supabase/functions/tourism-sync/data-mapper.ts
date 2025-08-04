import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"

export class DataMapper {
  async mapData(apiType: string, rawData: any) {
    try {
      const items = this.extractItems(apiType, rawData)
      
      // 배열 검증
      if (!Array.isArray(items)) {
        console.warn(`⚠️  Extracted items is not an array for ${apiType}:`, typeof items)
        return []
      }
      
      console.log(`📊 Processing ${items.length} items for ${apiType}`)
      
      const mappedItems = []
      for (const item of items) {
        try {
          if (!item || typeof item !== 'object') {
            console.warn(`⚠️  Invalid item in ${apiType}:`, item)
            continue
          }
          
          const mapped = this.mapItem(apiType, item)
          if (mapped) {
            mapped.data_hash = await this.calculateHash(item)
            mapped.raw_data = item
            mappedItems.push(mapped)
          }
        } catch (error) {
          console.warn(`⚠️  Failed to map item in ${apiType}:`, error.message)
          // 개별 아이템 실패는 전체를 중단하지 않음
        }
      }
      
      console.log(`✅ Successfully mapped ${mappedItems.length}/${items.length} items for ${apiType}`)
      return mappedItems
      
    } catch (error) {
      console.error(`❌ Data mapping failed for ${apiType}:`, error.message)
      console.error('Raw data structure:', JSON.stringify(rawData, null, 2))
      return []
    }
  }
  
  private extractItems(apiType: string, data: any) {
    try {
      console.log(`🔍 Extracting items for ${apiType}`)
      
      if (!data || typeof data !== 'object') {
        console.warn(`⚠️  Invalid data structure for ${apiType}:`, typeof data)
        return []
      }
      
      if (apiType === 'base_tour') {
        // base_tour는 직접 items 배열 구조
        console.log(`📊 base_tour data keys:`, Object.keys(data))
        
        const items = data.items
        if (!items) {
          console.warn(`⚠️  No items found in base_tour data`)
          return []
        }
        
        const itemCount = Array.isArray(items) ? items.length : 0
        console.log(`📊 base_tour extracted ${itemCount} items`)
        
        return Array.isArray(items) ? items : []
      } else {
        // greentour, barrier_free는 response.body.items.item 구조
        const response = data.response
        if (!response || !response.body) {
          console.warn(`⚠️  Invalid response structure for ${apiType}`)
          console.log('Response structure:', JSON.stringify(data, null, 2))
          return []
        }
        
        const items = response.body.items?.item
        if (!items) {
          console.warn(`⚠️  No items found in ${apiType} response`)
          return []
        }
        
        // 단일 아이템인 경우 배열로 변환
        const extractedItems = Array.isArray(items) ? items : [items]
        console.log(`📊 ${apiType} extracted ${extractedItems.length} items`)
        
        return extractedItems
      }
    } catch (error) {
      console.error(`❌ Item extraction failed for ${apiType}:`, error.message)
      return []
    }
  }
  
  private mapItem(apiType: string, item: any) {
    if (!item || typeof item !== 'object') {
      throw new Error('Invalid item: not an object')
    }
    
    switch (apiType) {
      case 'greentour':
        return this.mapGreentourData(item)
      case 'barrier_free':
        return this.mapBarrierFreeData(item)
      case 'base_tour':
        return this.mapBaseTourData(item)
      default:
        throw new Error(`Unknown API type: ${apiType}`)
    }
  }
  
  private mapGreentourData(item: any) {
    return {
      contentid: String(item.contentid || ''),
      areacode: item.areacode || null,
      sigungucode: item.sigungucode || null,
      title: item.title || null,
      addr: item.addr || null,
      tel: item.tel || null,
      telname: item.telname || null,
      mainimage: item.mainimage || null,
      summary: item.summary || null,
      createdtime: item.createdtime || null,
      modifiedtime: item.modifiedtime || null,
      cpyrhtdivcd: item.cpyrhtDivCd || null
    }
  }
  
  private mapBarrierFreeData(item: any) {
    return {
      contentid: String(item.contentid || ''),
      contenttypeid: item.contenttypeid || null,
      areacode: item.areacode || null,
      sigungucode: item.sigungucode || null,
      cat1: item.cat1 || null,
      cat2: item.cat2 || null,
      cat3: item.cat3 || null,
      title: item.title || null,
      addr1: item.addr1 || null,
      addr2: item.addr2 || null,
      tel: item.tel || null,
      firstimage: item.firstimage || null,
      firstimage2: item.firstimage2 || null,
      mapx: this.parseFloat(item.mapx),
      mapy: this.parseFloat(item.mapy),
      mlevel: this.parseInt(item.mlevel),
      zipcode: item.zipcode || null,
      createdtime: item.createdtime || null,
      modifiedtime: item.modifiedtime || null,
      cpyrhtdivcd: item.cpyrhtDivCd || null,
      lclssystm1: item.lclsSystm1 || null,
      lclssystm2: item.lclsSystm2 || null,
      lclssystm3: item.lclsSystm3 || null,
      ldongregn_cd: item.lDongRegnCd || null,
      ldongsigngu_cd: item.lDongSignguCd || null
    }
  }
  
  private mapBaseTourData(item: any) {
    return {
      hubtatscode: String(item.hubTatsCd || ''),
      baseym: item.baseYm || null,
      areacd: item.areaCd || null,
      areanm: item.areaNm || null,
      signgucd: item.signguCd || null,
      signgunm: item.signguNm || null,
      hubtatsname: item.hubTatsNm || null,
      hubctgrylclsnm: item.hubCtgryLclsNm || null,
      hubctgrymclsnm: item.hubCtgryMclsNm || null,
      hubrank: this.parseInt(item.hubRank),
      mapx: this.parseFloat(item.mapX),
      mapy: this.parseFloat(item.mapY)
    }
  }
  
  private parseFloat(value: any): number | null {
    if (value === null || value === undefined || value === '') return null
    const parsed = parseFloat(value)
    return isNaN(parsed) ? null : parsed
  }
  
  private parseInt(value: any): number | null {
    if (value === null || value === undefined || value === '') return null
    const parsed = parseInt(value)
    return isNaN(parsed) ? null : parsed
  }
  
  private async calculateHash(data: any): Promise<string> {
    try {
      // 객체를 정규화된 JSON 문자열로 변환
      const normalized = JSON.stringify(data, Object.keys(data).sort())
      
      // TextEncoder로 문자열을 Uint8Array로 변환
      const encoder = new TextEncoder()
      const dataBuffer = encoder.encode(normalized)
      
      // SHA-256 해시 계산
      const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
      
      // ArrayBuffer를 hex 문자열로 변환
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
      
      return hashHex
    } catch (error) {
      console.warn('Hash calculation failed, using fallback:', error.message)
      // 해시 계산 실패 시 타임스탬프 기반 fallback
      return `fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
  }
  
  getKeyFields(apiType: string): string | string[] {
    switch (apiType) {
      case 'greentour':
      case 'barrier_free':
        return 'contentid'
      case 'base_tour':
        return ['hubtatscode', 'baseym']
      default:
        throw new Error(`Unknown API type: ${apiType}`)
    }
  }
  
  getTableName(apiType: string): string {
    const tableMap = {
      greentour: 'greentour_areabased',
      barrier_free: 'barrier_free_areabased',
      base_tour: 'base_tour_areabased'
    }
    
    const tableName = tableMap[apiType as keyof typeof tableMap]
    if (!tableName) {
      throw new Error(`Unknown API type: ${apiType}`)
    }
    
    return tableName
  }
}
