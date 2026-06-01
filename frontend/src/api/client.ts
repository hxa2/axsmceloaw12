// src/api/client.ts
// ==================
// API client cho transportation backend.

import type {
  MethodsResponse,
  SampleProblem,
  SolveRequest,
  SolveResponse,
} from '@/types/transportation'

const BASE_URL = '/api/transportation'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.detail || errorMessage
    } catch {
      // Keep original error message
    }
    throw new ApiError(response.status, errorMessage)
  }

  return response.json() as Promise<T>
}

// ── Transportation API ────────────────────────────────────────────────────────

export const api = {
  health: () =>
    request<{ status: string; version: string; message: string }>('/health'),

  getMethods: () => request<MethodsResponse>('/methods'),

  getSamples: () => request<SampleProblem[]>('/samples'),

  getSample: (id: string) =>
    request<SampleProblem>(`/sample?id=${encodeURIComponent(id)}`),

  getRandomSample: (m: number, n: number, degenerate = false) =>
    request<SampleProblem>(
      `/sample/random?m=${m}&n=${n}&degenerate=${degenerate}`,
    ),

  solve: (payload: SolveRequest): Promise<SolveResponse> =>
    request<SolveResponse>('/solve', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  solveFromFile: async (
    file: File,
    options: {
      initialMethod?: string
      optimizationMethod?: string
      includeIterations?: boolean
    } = {},
  ): Promise<SolveResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('initialMethod', options.initialMethod ?? 'least_cost')
    formData.append('optimizationMethod', options.optimizationMethod ?? 'potential')
    formData.append('includeIterations', String(options.includeIterations ?? true))

    const response = await fetch(`${BASE_URL}/solve-from-file`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorMessage
      } catch {
        // Keep original error message
      }
      throw new ApiError(response.status, errorMessage)
    }

    return response.json() as Promise<SolveResponse>
  },
}

export { ApiError }
