"""
backend/app/services/assignment_service.py
==========================================
Service điều phối bài toán phân việc (Hungarian Algorithm).
"""

import logging
from backend.app.schemas.request import AssignmentRequest
from backend.app.schemas.response import ExtendedSolveResponse, TransformationInfo, StepInfo
from backend.core.solvers.assignment_solver import solve_assignment, AssignmentStep

logger = logging.getLogger(__name__)


def solve_assignment_problem(req: AssignmentRequest) -> ExtendedSolveResponse:
    """Giải bài toán phân việc và trả ExtendedSolveResponse."""

    result = solve_assignment(
        matrix=req.matrix,
        objective=req.objective,
        worker_names=req.workerNames,
        job_names=req.jobNames,
    )

    n_workers = result.n_workers_orig
    n_jobs = result.n_jobs_orig
    w_names = req.workerNames or [f"Người {i+1}" for i in range(n_workers)]
    j_names = req.jobNames or [f"Việc {j+1}" for j in range(n_jobs)]

    # Build transformations list
    transformations = []
    if result.is_maximize:
        transformations.append(TransformationInfo(
            type="max_to_min",
            description=f"Chuyển bài toán tối đa lợi nhuận thành tối thiểu bằng c'_ij = P_max - p_ij (P_max = {result.p_max}).",
            formula="c'_ij = P_max - p_ij",
            details={"pMax": result.p_max},
        ))
    if result.added_dummy_workers > 0 or result.added_dummy_jobs > 0:
        transformations.append(TransformationInfo(
            type="rectangular_to_square",
            description=f"Ma trận {n_workers}×{n_jobs} không vuông. Thêm {result.added_dummy_workers} người ảo và {result.added_dummy_jobs} việc ảo để thành {result.n_size}×{result.n_size}.",
            formula="Chi phí dummy = 0",
            details={
                "addedDummyWorkers": result.added_dummy_workers,
                "addedDummyJobs": result.added_dummy_jobs,
                "paddedSize": result.n_size,
            },
        ))

    # Build steps
    steps = [
        StepInfo(
            type=s.type,
            description=s.description,
            matrixBefore=s.matrix_before,
            matrixAfter=s.matrix_after,
            details=s.details,
        )
        for s in result.steps
    ]

    # Real vs dummy assignments
    real_assignments = [a for a in result.assignments if not a.get("isDummy", False)]
    dummy_assignments = [a for a in result.assignments if a.get("isDummy", False)]
    unassigned_workers = [a["workerName"] for a in dummy_assignments if a["workerIndex"] < n_workers]
    unassigned_jobs = [
        j_names[j] for j in range(n_jobs)
        if j not in {a["jobIndex"] for a in real_assignments}
    ]

    objective_label = "totalProfit" if result.is_maximize else "totalCost"
    objective_value = result.total_profit if result.is_maximize else result.total_cost

    return ExtendedSolveResponse(
        problemType="assignment",
        variant="assignment",
        originalProblem={
            "matrix": result.original_matrix,
            "workerNames": w_names,
            "jobNames": j_names,
            "objective": req.objective,
        },
        transformedProblem={
            "matrix": result.working_matrix,
            "workerNames": w_names + [f"Dummy người {k+1}" for k in range(result.added_dummy_workers)],
            "jobNames": j_names + [f"Dummy việc {k+1}" for k in range(result.added_dummy_jobs)],
        },
        transformations=transformations,
        solution={
            "assignmentMatrix": result.assignment_matrix,
            "assignments": result.assignments,
            "totalCost": result.total_cost,
            "totalProfit": result.total_profit,
            "objectiveValue": objective_value,
            objective_label: objective_value,
            "isOptimal": True,
            "objective": req.objective,
        },
        interpretation={
            "realAssignments": real_assignments,
            "dummyAssignments": dummy_assignments,
            "unassignedWorkers": unassigned_workers,
            "unassignedJobs": unassigned_jobs,
        },
        steps=steps,
        isOptimal=True,
    )
