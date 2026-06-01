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

  const solveFromFile = useCallback(
    async (
      file: File,
      options: { initialMethod?: string; optimizationMethod?: string } = {},
    ) => {
      setState({ status: 'loading' })
      try {
        const data = await api.solveFromFile(file, options)
        const dummyReq: SolveRequest = {
          costMatrix: data.costMatrix ?? [],
          supply: data.supply ?? [],
          demand: data.demand ?? [],
          initialMethod: options.initialMethod as any,
          optimizationMethod: options.optimizationMethod as any,
        }
        setState({ status: 'success', data, request: dummyReq })
      } catch (err: any) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Lỗi không xác định'
        setState({ status: 'error', message })
      }
    },
    [],
  )

  const reset = useCallback(() => {
    setState({ status: 'idle' })
  }, [])

  return { state, solve, solveFromFile, reset }
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
