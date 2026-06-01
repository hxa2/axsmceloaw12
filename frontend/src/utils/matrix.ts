// src/utils/matrix.ts
// =====================
// Utility functions cho matrix operations trong UI.

import type { ProblemEditorState } from '@/types/transportation'

export function createEmptyMatrix(m: number, n: number): string[][] {
  return Array.from({ length: m }, () => Array.from({ length: n }, () => ''))
}

export function parseMatrix(matrix: string[][]): number[][] | null {
  try {
    const result = matrix.map((row) =>
      row.map((cell) => {
        const v = parseFloat(cell)
        if (isNaN(v)) throw new Error(`Invalid: ${cell}`)
        return v
      }),
    )
    return result
  } catch {
    return null
  }
}

export function parseVector(vec: string[]): number[] | null {
  try {
    return vec.map((cell) => {
      const v = parseFloat(cell)
      if (isNaN(v)) throw new Error(`Invalid: ${cell}`)
      return v
    })
  } catch {
    return null
  }
}

export function matrixToStrings(matrix: number[][]): string[][] {
  return matrix.map((row) => row.map((v) => String(v)))
}

export function vectorToStrings(vec: number[]): string[] {
  return vec.map((v) => String(v))
}

export function resizeMatrix(
  matrix: string[][],
  newM: number,
  newN: number,
): string[][] {
  const result: string[][] = []
  for (let i = 0; i < newM; i++) {
    const row: string[] = []
    for (let j = 0; j < newN; j++) {
      row.push(matrix[i]?.[j] ?? '')
    }
    result.push(row)
  }
  return result
}

export function resizeVector(vec: string[], newLen: number): string[] {
  const result: string[] = []
  for (let i = 0; i < newLen; i++) {
    result.push(vec[i] ?? '')
  }
  return result
}

export function createDefaultEditorState(m: number, n: number): ProblemEditorState {
  return {
    costMatrix: createEmptyMatrix(m, n),
    supply: Array(m).fill(''),
    demand: Array(n).fill(''),
    sourceNames: Array.from({ length: m }, (_, i) => `S${i + 1}`),
    destinationNames: Array.from({ length: n }, (_, i) => `D${i + 1}`),
    initialMethod: 'least_cost',
    optimizationMethod: 'potential',
    includeIterations: true,
  }
}

export function formatNumber(v: number | null | undefined, decimals = 4): string {
  if (v === null || v === undefined) return '–'
  if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v))
  return v.toFixed(decimals).replace(/\.?0+$/, '')
}

export function calcTotalCost(
  costMatrix: number[][],
  allocationMatrix: number[][],
): number {
  let total = 0
  for (let i = 0; i < costMatrix.length; i++) {
    for (let j = 0; j < costMatrix[i].length; j++) {
      total += (costMatrix[i]?.[j] ?? 0) * (allocationMatrix[i]?.[j] ?? 0)
    }
  }
  return total
}
