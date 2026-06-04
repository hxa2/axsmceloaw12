// src/types/transportation.ts
// ============================
// TypeScript types cho bài toán vận tải.
// Mirror của Pydantic schemas phía backend.

export interface TransportationProblem {
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  sourceNames?: string[]
  destinationNames?: string[]
}

export interface IterationResult {
  step: number
  allocationMatrix: number[][]
  totalCost: number | null
  potentialsU: (number | null)[] | null
  potentialsV: (number | null)[] | null
  reducedCosts: (number | null)[][] | null
  enteringCell: [number, number] | null
  leavingCell: [number, number] | null
  cycle: [number, number][] | null
  theta?: number | null
  costDelta?: number | null
  isOptimal?: boolean | null
  description: string
}

export interface SolveResponse {
  allocationMatrix: number[][]
  totalCost: number
  isOptimal: boolean
  iterations: IterationResult[]
  message: string
  warnings: string[]
  initialCost: number | null
  numIterations: number
  basisCells: [number, number][]
  costMatrix?: number[][]
  supply?: number[]
  demand?: number[]
  sourceNames: string[] | null
  destinationNames: string[] | null

  // Balance metadata
  isBalancedOriginal?: boolean
  balanceType?: 'none' | 'dummy_source' | 'dummy_destination'
  dummySourceIndex?: number | null
  dummyDestinationIndex?: number | null
  originalSupplyTotal?: number | null
  originalDemandTotal?: number | null
}

export interface SolveRequest {
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  initialMethod?: InitialMethod
  optimizationMethod?: OptimizationMethod
  sourceNames?: string[]
  destinationNames?: string[]
  includeIterations?: boolean
}

export type InitialMethod = 'least_cost' | 'northwest_corner' | 'vogel'
export type OptimizationMethod = 'potential' | 'none'

export interface MethodInfo {
  id: string
  name: string
  description: string
  isAvailable: boolean
}

export interface MethodsResponse {
  initialMethods: MethodInfo[]
  optimizationMethods: MethodInfo[]
}

export interface SampleProblem {
  name: string
  description: string
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  optimalCost?: number | null
  sourceNames?: string[] | null
  destinationNames?: string[] | null
}

export interface ApiError {
  detail: string
}

// UI state types
export type SolverState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: SolveResponse; request: SolveRequest }
  | { status: 'error'; message: string; request?: SolveRequest }

export interface ProblemEditorState {
  costMatrix: string[][]  // Luôn là string để cho phép nhập liệu
  supply: string[]
  demand: string[]
  sourceNames: string[]
  destinationNames: string[]
  initialMethod: InitialMethod
  optimizationMethod: OptimizationMethod
  includeIterations: boolean
}
