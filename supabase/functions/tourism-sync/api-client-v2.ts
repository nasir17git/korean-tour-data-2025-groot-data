export class TourismApiClient {
  private baseUrls = {
    greentour: 'https://apis.data.go.kr/B551011/GreenTourService1',
    barrier_free: 'https://apis.data.go.kr/B551011/KorWithService2',
    base_tour: 'https://apis.data.go.kr/B551011/LocgoHubTarService1'
  }
  
  private endpoints = {
    '1': { '2': '/areaBasedList1' },
    '2': { '5': '/areaBasedList2' },
    '3': { '1': '/areaBasedList1' }
  }
  
  async fetchData(apiKey: string, endpointId: string) {
    const apiType = this.getApiType(apiKey)
    const endpoint = this.endpoints[apiKey]?.[endpointId]
    
    if (!endpoint) {
      throw new Error(`Invalid API key or endpoint: ${apiKey}-${endpointId}`)
    }
    
    const baseUrl = this.baseUrls[apiType]
    
    // 환경 변수 확인
    const serviceKey = Deno.env.get('DATA_KEY_DECODING')
    if (!serviceKey) {
      throw new Error('DATA_KEY_DECODING environment variable is not set')
    }
    
    // 기본 파라미터
    const params = new URLSearchParams({
      serviceKey: serviceKey,
      numOfRows: '100',
      pageNo: '1',
      MobileOS: 'ETC',
      MobileApp: this.getAppName(apiType),
      _type: 'json'
    })
    
    // API별 추가 파라미터
    this.addApiSpecificParams(apiType, params)
    
    const url = `${baseUrl}${endpoint}?${params}`
    
    console.log(`🔄 Fetching ${apiType}: ${baseUrl}${endpoint}`)
    
    try {
      // 여러 방법으로 시도
      let response
      let lastError
      
      // 방법 1: 표준 fetch (Chrome User-Agent)
      try {
        console.log(`🧪 Trying method 1: Standard fetch with Chrome UA`)
        response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Cache-Control': 'no-cache'
          },
          signal: AbortSignal.timeout(30000)
        })
        
        if (response.ok) {
          console.log(`✅ Method 1 succeeded for ${apiType}`)
        } else {
          throw new Error(`HTTP ${response.status}`)
        }
      } catch (error) {
        console.log(`❌ Method 1 failed for ${apiType}:`, error.message)
        lastError = error
        
        // 방법 2: 최소한의 헤더
        try {
          console.log(`🧪 Trying method 2: Minimal headers`)
          response = await fetch(url, {
            method: 'GET',
            headers: {
              'User-Agent': 'curl/7.68.0'
            },
            signal: AbortSignal.timeout(30000)
          })
          
          if (response.ok) {
            console.log(`✅ Method 2 succeeded for ${apiType}`)
          } else {
            throw new Error(`HTTP ${response.status}`)
          }
        } catch (error2) {
          console.log(`❌ Method 2 failed for ${apiType}:`, error2.message)
          lastError = error2
          
          // 방법 3: HTTP로 시도 (최후의 수단)
          try {
            console.log(`🧪 Trying method 3: HTTP fallback`)
            const httpUrl = url.replace('https://', 'http://')
            response = await fetch(httpUrl, {
              method: 'GET',
              headers: {
                'User-Agent': 'TourismSync/1.0'
              },
              signal: AbortSignal.timeout(30000)
            })
            
            if (response.ok) {
              console.log(`✅ Method 3 (HTTP) succeeded for ${apiType}`)
            } else {
              throw new Error(`HTTP ${response.status}`)
            }
          } catch (error3) {
            console.log(`❌ Method 3 failed for ${apiType}:`, error3.message)
            throw lastError // 첫 번째 오류를 던짐
          }
        }
      }
      
      console.log(`📡 Response status for ${apiType}: ${response.status} ${response.statusText}`)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error(`❌ API Error Response for ${apiType}:`, errorText.substring(0, 500))
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const contentType = response.headers.get('content-type')
      console.log(`📄 Content-Type for ${apiType}: ${contentType}`)
      
      let data
      try {
        data = await response.json()
      } catch (parseError) {
        const textData = await response.text()
        console.error(`❌ JSON Parse Error for ${apiType}:`, parseError.message)
        console.error(`Raw response: ${textData.substring(0, 500)}...`)
        throw new Error(`Invalid JSON response from ${apiType} API`)
      }
      
      console.log(`✅ Successfully parsed JSON for ${apiType}`)
      
      // API 응답 검증
      this.validateApiResponse(apiType, data)
      
      return data
      
    } catch (error) {
      if (error.name === 'TimeoutError') {
        throw new Error(`API timeout for ${apiType} (30s exceeded)`)
      }
      
      console.error(`❌ API call failed for ${apiType}:`, error.message)
      throw new Error(`API call failed for ${apiType}: ${error.message}`)
    }
  }
  
  private getAppName(apiType: string): string {
    const appNames = {
      greentour: 'MyEcotourApp',
      barrier_free: 'BarrierFreeApp',
      base_tour: 'MyBaseTourApp'
    }
    return appNames[apiType as keyof typeof appNames] || 'TourismEdgeSync'
  }
  
  private addApiSpecificParams(apiType: string, params: URLSearchParams) {
    switch (apiType) {
      case 'barrier_free':
        params.append('arrange', 'C')
        params.append('areaCode', '35')
        break
      case 'base_tour':
        params.append('baseYm', '202506')
        params.append('areaCd', '47')
        break
      case 'greentour':
        // 생태관광은 추가 파라미터 없음
        break
    }
  }
  
  private validateApiResponse(apiType: string, data: any) {
    console.log(`🔍 Validating response for ${apiType}`)
    
    if (!data || typeof data !== 'object') {
      throw new Error(`Invalid response format: not an object`)
    }
    
    if (apiType === 'base_tour') {
      console.log(`📊 base_tour response keys:`, Object.keys(data))
      
      if (data.items !== undefined) {
        const itemCount = Array.isArray(data.items) ? data.items.length : 0
        console.log(`📊 base_tour items count: ${itemCount}`)
      } else if (data.response && data.response.body) {
        const totalCount = data.response.body.totalCount || 0
        const items = data.response.body.items?.item
        const itemCount = Array.isArray(items) ? items.length : (items ? 1 : 0)
        console.log(`📊 base_tour total: ${totalCount}, items: ${itemCount}`)
      } else {
        console.log(`📊 base_tour unknown structure, keys:`, Object.keys(data))
      }
      
    } else {
      // greentour, barrier_free
      if (!data.response) {
        console.log(`📊 ${apiType} response keys:`, Object.keys(data))
        throw new Error(`Invalid ${apiType} response: missing response property`)
      }
      
      if (!data.response.body) {
        console.log(`📊 ${apiType} response.keys:`, Object.keys(data.response))
        throw new Error(`Invalid ${apiType} response: missing response.body`)
      }
      
      const resultCode = data.response.header?.resultCode
      const resultMsg = data.response.header?.resultMsg
      
      console.log(`📊 ${apiType} result code: ${resultCode}, message: ${resultMsg}`)
      
      if (resultCode && resultCode !== '0000') {
        throw new Error(`API error ${resultCode}: ${resultMsg || 'Unknown error'}`)
      }
      
      const totalCount = data.response.body.totalCount || 0
      const items = data.response.body.items?.item
      const itemCount = Array.isArray(items) ? items.length : (items ? 1 : 0)
      
      console.log(`📊 ${apiType} total: ${totalCount}, items: ${itemCount}`)
    }
    
    console.log(`✅ Response validation passed for ${apiType}`)
  }
  
  private getApiType(apiKey: string): 'greentour' | 'barrier_free' | 'base_tour' {
    const mapping = {
      '1': 'greentour',
      '2': 'barrier_free', 
      '3': 'base_tour'
    } as const
    
    const apiType = mapping[apiKey as keyof typeof mapping]
    if (!apiType) {
      throw new Error(`Unknown API key: ${apiKey}`)
    }
    
    return apiType
  }
  
  // 간단한 연결 테스트
  async testApiConnection(apiKey: string, endpointId: string) {
    try {
      console.log(`🧪 Testing API connection for ${apiKey}-${endpointId}`)
      
      const apiType = this.getApiType(apiKey)
      const endpoint = this.endpoints[apiKey]?.[endpointId]
      const baseUrl = this.baseUrls[apiType]
      
      const serviceKey = Deno.env.get('DATA_KEY_DECODING')
      
      const params = new URLSearchParams({
        serviceKey: serviceKey || '',
        numOfRows: '1',
        pageNo: '1',
        MobileOS: 'ETC',
        MobileApp: this.getAppName(apiType),
        _type: 'json'
      })
      
      this.addApiSpecificParams(apiType, params)
      
      const testUrl = `${baseUrl}${endpoint}?${params}`
      
      // HTTP로 간단 테스트
      const httpUrl = testUrl.replace('https://', 'http://')
      console.log(`🧪 Testing with HTTP: ${httpUrl}`)
      
      const response = await fetch(httpUrl, {
        method: 'GET',
        headers: {
          'User-Agent': 'TourismSync/1.0'
        },
        signal: AbortSignal.timeout(15000)
      })
      
      console.log(`🧪 Test response: ${response.status} ${response.statusText}`)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`🧪 Test data structure:`, Object.keys(data))
        return { success: true, status: response.status, data }
      } else {
        const errorText = await response.text()
        console.log(`🧪 Test error:`, errorText.substring(0, 200))
        return { success: false, status: response.status, error: errorText }
      }
      
    } catch (error) {
      console.error(`🧪 Test failed:`, error.message)
      return { success: false, error: error.message }
    }
  }
}
