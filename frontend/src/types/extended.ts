// src/types/extended.ts
// =======================
// TypeScript interfaces cho 5 bài toán mở rộng.

// ── Shared types ──────────────────────────────────────────────────────────────

export interface TransformationInfo {
  type: string
  description: string
  formula?: string
  details?: Record<string, unknown>
}

export interface StepInfo {
  type: string
  description: string
  matrixBefore?: (number | null)[][] | null
  matrixAfter?: (number | null)[][] | null
  details?: Record<string, unknown>
}

export interface ExtendedSolveResponse {
  problemType: string   // "transportation" | "assignment"
  variant: string       // "max_profit" | "forbidden_cells" | "inequality" | "warehouse" | "assignment"

  originalProblem: Record<string, unknown>
  transformedProblem: Record<string, unknown>
  transformations: TransformationInfo[]

  solution: Record<string, unknown>
  interpretation: Record<string, unknown>
  steps: StepInfo[]

  warnings: string[]
  isOptimal: boolean
  isFeasible: boolean
  infeasibilityReason?: string | null
}

// ── Max Transportation ────────────────────────────────────────────────────────

export interface MaxTransportRequest {
  profitMatrix: number[][]
  supply: number[]
  demand: number[]
  sourceNames?: string[]
  destinationNames?: string[]
  initialMethod?: string
  optimizationMethod?: string
}

// ── Forbidden Cells ───────────────────────────────────────────────────────────

export interface ForbiddenCell {
  row: number
  col: number
}

export interface ForbiddenCellsRequest {
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  forbiddenCells: ForbiddenCell[]
  sourceNames?: string[]
  destinationNames?: string[]
  initialMethod?: string
  optimizationMethod?: string
}

// ── Inequality Constraints ────────────────────────────────────────────────────

export type SupplyConstraint = 'equal' | 'less_or_equal'
export type DemandConstraint = 'equal' | 'greater_or_equal' | 'less_or_equal'

export interface InequalityRequest {
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  supplyConstraint: SupplyConstraint
  demandConstraint: DemandConstraint
  sourceNames?: string[]
  destinationNames?: string[]
  initialMethod?: string
  optimizationMethod?: string
}

// ── Warehouse Receiving ───────────────────────────────────────────────────────

export interface WarehouseSpec {
  name: string
  demandMode: 'fixed' | 'max_capacity'
  amount: number
  costsFromSources: number[]
  storageCostPerUnit?: number
}

export interface WarehouseRequest {
  baseCostMatrix: number[][]
  supply: number[]
  demand: number[]
  warehouses: WarehouseSpec[]
  sourceNames?: string[]
  destinationNames?: string[]
  initialMethod?: string
  optimizationMethod?: string
}

// ── Assignment ────────────────────────────────────────────────────────────────

export interface AssignmentRequest {
  matrix: number[][]
  objective: 'minimize' | 'maximize'
  workerNames?: string[]
  jobNames?: string[]
}

export interface AssignmentEntry {
  workerIndex: number
  jobIndex: number
  workerName: string
  jobName: string
  value: number
  isDummy: boolean
}

// ── Tab definition ────────────────────────────────────────────────────────────

export type ProblemTab =
  | 'basic'
  | 'max'
  | 'forbidden'
  | 'inequality'
  | 'warehouse'
  | 'assignment'
