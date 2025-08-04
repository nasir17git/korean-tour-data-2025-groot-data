import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { TourismApiClient } from './api-client-v2.ts'  // 새로운 클라이언트 사용
import { DataMapper } from './data-mapper.ts'
import { DatabaseHandler } from './database.ts'

interface SyncResult {
  api_type: string
  status: 'SUCCESS' | 'FAILED'
  total?: number
  new?: number
  updated?: number
  execution_time?: number
  error?: string
}

serve(async (req) => {
  const startTime = Date.now()
  
  try {
    console.log('🚀 Tourism data sync started at', new Date().toISOString())
    console.log('🔧 Environment check:')
    console.log('  - SUPABASE_URL exists:', !!Deno.env.get('SUPABASE_URL'))
    console.log('  - SUPABASE_SERVICE_ROLE_KEY exists:', !!Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'))
    console.log('  - DATA_KEY_DECODING exists:', !!Deno.env.get('DATA_KEY_DECODING'))
    
    // CORS 헤더 설정
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    }

    if (req.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders })
    }
    
    // 요청 본문 파싱 (있는 경우)
    let requestBody = {}
    try {
      if (req.body) {
        requestBody = await req.json()
        console.log('📥 Request body:', requestBody)
      }
    } catch (e) {
      console.log('📥 No request body or invalid JSON')
    }
    
    // Supabase 클라이언트 초기화
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Missing Supabase credentials')
    }
    
    const supabase = createClient(supabaseUrl, supabaseKey)
    console.log('✅ Supabase client initialized')
    
    const apiClient = new TourismApiClient()
    const mapper = new DataMapper()
    const dbHandler = new DatabaseHandler(supabase)
    
    // 데이터베이스 연결 테스트
    console.log('🔍 Testing database connection...')
    const dbConnected = await dbHandler.testConnection()
    if (!dbConnected) {
      throw new Error('Database connection failed')
    }
    console.log('✅ Database connection verified')
    
    const results: SyncResult[] = []
    
    // 3개 API 순차 처리
    const apis = [
      { key: '1', type: 'greentour', endpoint: '2', name: '생태관광' },
      { key: '2', type: 'barrier_free', endpoint: '5', name: '무장애여행' },
      { key: '3', type: 'base_tour', endpoint: '1', name: '중심관광지' }
    ]
    
    for (const api of apis) {
      const apiStartTime = Date.now()
      
      try {
        console.log(`\n${'='.repeat(50)}`)
        console.log(`📊 Processing ${api.name} (${api.type})...`)
        console.log(`🔗 API ${api.key}, Endpoint ${api.endpoint}`)
        
        // API 연결 테스트 (디버깅용)
        console.log(`🧪 Testing API connection for ${api.type}...`)
        const testResult = await apiClient.testApiConnection(api.key, api.endpoint)
        console.log(`🧪 Connection test result:`, testResult.success ? 'PASS' : 'FAIL')
        
        if (!testResult.success) {
          throw new Error(`API connection test failed: ${testResult.error}`)
        }
        
        // 실제 API 호출
        console.log(`📡 Fetching data from ${api.type} API...`)
        const rawData = await apiClient.fetchData(api.key, api.endpoint)
        console.log(`✅ API data fetched for ${api.type}`)
        
        // 데이터 매핑
        console.log(`🔄 Mapping data for ${api.type}...`)
        const mappedData = await mapper.mapData(api.type, rawData)
        console.log(`✅ Data mapped for ${api.type}: ${mappedData.length} items`)
        
        if (mappedData.length === 0) {
          console.warn(`⚠️  No data to sync for ${api.type}`)
          results.push({
            api_type: api.type,
            status: 'SUCCESS',
            total: 0,
            new: 0,
            updated: 0,
            execution_time: Math.round((Date.now() - apiStartTime) / 1000)
          })
          continue
        }
        
        // DB 저장
        console.log(`💾 Syncing data to database for ${api.type}...`)
        const syncResult = await dbHandler.syncData(api.type, mappedData)
        console.log(`✅ DB sync completed for ${api.type}`)
        
        const executionTime = Math.round((Date.now() - apiStartTime) / 1000)
        
        results.push({
          api_type: api.type,
          status: 'SUCCESS',
          total: mappedData.length,
          new: syncResult.new,
          updated: syncResult.updated,
          execution_time: executionTime
        })
        
        console.log(`🎉 ${api.name} completed: ${syncResult.new} new, ${syncResult.updated} updated (${executionTime}s)`)
        
      } catch (error) {
        const executionTime = Math.round((Date.now() - apiStartTime) / 1000)
        console.error(`❌ ${api.name} failed:`, error.message)
        console.error(`❌ Error stack:`, error.stack)
        
        results.push({
          api_type: api.type,
          status: 'FAILED',
          execution_time: executionTime,
          error: error.message
        })
      }
    }
    
    const totalExecutionTime = Math.round((Date.now() - startTime) / 1000)
    const successCount = results.filter(r => r.status === 'SUCCESS').length
    
    console.log(`\n${'='.repeat(50)}`)
    console.log(`🏁 Sync completed: ${successCount}/${apis.length} successful (${totalExecutionTime}s total)`)
    
    // 결과 요약 로그
    results.forEach(result => {
      const status = result.status === 'SUCCESS' ? '✅' : '❌'
      console.log(`${status} ${result.api_type}: ${result.status} (${result.execution_time}s)`)
      if (result.status === 'SUCCESS') {
        console.log(`   📊 Total: ${result.total}, New: ${result.new}, Updated: ${result.updated}`)
      } else {
        console.log(`   💥 Error: ${result.error}`)
      }
    })
    
    // 전체 결과 반환
    const responseData = {
      success: successCount === apis.length,
      timestamp: new Date().toISOString(),
      total_execution_time: totalExecutionTime,
      summary: {
        total_apis: apis.length,
        successful: successCount,
        failed: apis.length - successCount
      },
      results,
      debug_info: {
        environment_variables: {
          supabase_url_exists: !!supabaseUrl,
          service_key_exists: !!supabaseKey,
          data_key_exists: !!Deno.env.get('DATA_KEY_DECODING')
        },
        request_info: requestBody
      }
    }
    
    console.log(`📤 Returning response with ${successCount} successful APIs`)
    
    return new Response(
      JSON.stringify(responseData),
      { 
        headers: { 
          "Content-Type": "application/json",
          ...corsHeaders
        },
        status: 200 
      }
    )
    
  } catch (error) {
    const totalExecutionTime = Math.round((Date.now() - startTime) / 1000)
    console.error('💥 Sync failed:', error.message)
    console.error('💥 Error stack:', error.stack)
    
    const errorResponse = {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      total_execution_time: totalExecutionTime,
      debug_info: {
        environment_variables: {
          supabase_url_exists: !!Deno.env.get('SUPABASE_URL'),
          service_key_exists: !!Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
          data_key_exists: !!Deno.env.get('DATA_KEY_DECODING')
        }
      }
    }
    
    console.log(`📤 Returning error response`)
    
    return new Response(
      JSON.stringify(errorResponse),
      { 
        headers: { 
          "Content-Type": "application/json",
          'Access-Control-Allow-Origin': '*'
        },
        status: 500 
      }
    )
  }
})
