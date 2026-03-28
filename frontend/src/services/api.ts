// frontend/src/services/api.ts
import type { TripPlanRequest, TripPlan, StreamProgress } from '../types'

interface ImportMeta {
  readonly env: {
    readonly VITE_API_BASE_URL?: string
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// ── 普通 POST（不需要进度条时用）──────────────────────────
export async function createTripPlan(request: TripPlanRequest): Promise<TripPlan> {
  const res = await fetch(`${BASE_URL}/api/trip/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `请求失败 ${res.status}`)
  }
  return res.json()
}

// ── SSE 流式接口（带进度回调）─────────────────────────────
export function streamTripPlan(
  request: TripPlanRequest,
  onProgress: (p: StreamProgress) => void,
  onDone: (plan: TripPlan) => void,
  onError: (e: Error) => void,
): () => void {
  const controller = new AbortController()

  fetch(`${BASE_URL}/api/trip/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`请求失败 ${res.status}`)
      if (!res.body) throw new Error('无响应体')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload: StreamProgress = JSON.parse(line.slice(6))
            onProgress(payload)
            if (payload.progress === 100 && payload.result) {
              onDone(payload.result)
            }
            if (payload.progress === -1) {
              onError(new Error(payload.status))
            }
          } catch {
            // 跳过无法解析的行
          }
        }
      }
    })
    .catch((e) => {
      if (e.name !== 'AbortError') onError(e)
    })

  return () => controller.abort()
}