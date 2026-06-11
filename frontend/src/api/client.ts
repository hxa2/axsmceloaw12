import type {
  MethodsResponse,
  SampleProblem,
  SolveRequest,
  SolveResponse,
} from '@/types/transportation'
import type {
  MaxTransportRequest,
  ForbiddenCellsRequest,
  InequalityRequest,
  WarehouseRequest,
  AssignmentRequest,
  ExtendedSolveResponse,
} from '@/types/extended'

const BASE_URL = '/api/transportation'
const ASSIGNMENT_URL = '/api/assignment'

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
  const response = await fetch(path, {
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
    request<{ status: string; version: string; message: string }>(`${BASE_URL}/health`),

  getMethods: () => request<MethodsResponse>(`${BASE_URL}/methods`),

  getSamples: () => request<SampleProblem[]>(`${BASE_URL}/samples`),

  getSample: (id: string) =>
    request<SampleProblem>(`${BASE_URL}/sample?id=${encodeURIComponent(id)}`),

  getRandomSample: (m: number, n: number, degenerate = false) =>
    request<SampleProblem>(
      `${BASE_URL}/sample/random?m=${m}&n=${n}&degenerate=${degenerate}`,
    ),

  solve: (payload: SolveRequest): Promise<SolveResponse> =>
    request<SolveResponse>(`${BASE_URL}/solve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  parseFile: async (file: File): Promise<SampleProblem> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BASE_URL}/parse-file`, {
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

    return response.json() as Promise<SampleProblem>
  },

  // ── Extended Transportation ───────────────────────────────────────────────

  solveMax: (payload: MaxTransportRequest): Promise<ExtendedSolveResponse> =>
    request<ExtendedSolveResponse>(`${BASE_URL}/max`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  solveForbidden: (payload: ForbiddenCellsRequest): Promise<ExtendedSolveResponse> =>
    request<ExtendedSolveResponse>(`${BASE_URL}/forbidden`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  solveInequality: (payload: InequalityRequest): Promise<ExtendedSolveResponse> =>
    request<ExtendedSolveResponse>(`${BASE_URL}/inequality`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  solveWarehouse: (payload: WarehouseRequest): Promise<ExtendedSolveResponse> =>
    request<ExtendedSolveResponse>(`${BASE_URL}/warehouse`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // ── Assignment ────────────────────────────────────────────────────────────

  solveAssignment: (payload: AssignmentRequest): Promise<ExtendedSolveResponse> =>
    request<ExtendedSolveResponse>(`${ASSIGNMENT_URL}/solve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}

export { ApiError }
