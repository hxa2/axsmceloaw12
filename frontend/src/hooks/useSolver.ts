// src/hooks/useSolver.ts
// =======================
// Hook quản lý state của quá trình giải bài toán.

import { useCallback, useState } from 'react'
import { api, ApiError } from '@/api/client'
import type { SolveRequest, SolveResponse, SolverState } from '@/types/transportation'

export function useSolver() {
  const [state, setState] = useState<SolverState>({ status: 'idle' })

  const solve = useCallback(async (request: SolveRequest) => {
    setState({ status: 'loading' })
    try {
      const data = await api.solve(request)
      setState({ status: 'success', data, request })
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Lỗi không xác định'
      setState({ status: 'error', message, request })
    }
  }, [])

  const reset = useCallback(() => {
    setState({ status: 'idle' })
  }, [])

  return { state, solve, reset }
}

export function useSamples() {
  const [samples, setSamples] = useState<import('@/types/transportation').SampleProblem[]>([])
  const [loading, setLoading] = useState(false)

  const loadSamples = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getSamples()
      setSamples(data)
    } catch {
      // Silent fail for sample loading
    } finally {
      setLoading(false)
    }
  }, [])

  const getRandomSample = useCallback(
    async (m: number, n: number, degenerate = false) => {
      try {
        return await api.getRandomSample(m, n, degenerate)
      } catch {
        return null
      }
    },
    [],
  )

  return { samples, loading, loadSamples, getRandomSample }
}
