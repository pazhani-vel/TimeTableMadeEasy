import json
import sys
import traceback

from ortools.sat.python import cp_model

from input_loader import load_input
from model import build_model

from hard_constraints.theory import (
    add_theory_constraints
)

from hard_constraints.lab import (
    add_lab_constraints
)

from hard_constraints.batch import (
    add_batch_constraints
)

from hard_constraints.faculty import (
    add_faculty_constraints
)

from hard_constraints.day import (
    add_day_constraints
)

from hard_constraints.special import (
    add_special_constraints
)

from hard_constraints.resource import (
    add_resource_constraints
)

from soft_constraints.preferred_days import (
    add_preferred_day_constraints
)

from soft_constraints.workload import (
    add_workload_constraints
)

from soft_constraints.gaps import (
    add_gap_constraints
)

from soft_constraints.distribution import (
    add_distribution_constraints
)

from soft_constraints.timetable_quality import (
    add_timetable_quality_constraints
)

from soft_constraints.consecutive import (
    add_consecutive_theory_lab_constraints
)

from objective import add_objective

from result_validator import (
    validate_result
)


# ================================================================
# MAIN SOLVER
# ================================================================

def solve_timetable(data):
    """
    Build and solve the timetable.

    Returns a JSON-serializable dictionary.
    """

    # ============================================================
    # 1. CREATE MODEL
    # ============================================================

    timetable = build_model(
        data
    )

    model = timetable.model

    # ============================================================
    # 2. ADD HARD CONSTRAINTS
    # ============================================================
    #
    # These constraints MUST be satisfied.
    #
    # If any hard constraint cannot be satisfied, the solver
    # should return INFEASIBLE.
    # ============================================================

    add_theory_constraints(
        timetable
    )

    add_lab_constraints(
        timetable
    )

    add_batch_constraints(
        timetable
    )

    add_faculty_constraints(
        timetable
    )

    add_day_constraints(
        timetable
    )

    add_special_constraints(
        timetable
    )

    add_resource_constraints(
        timetable
    )

    # ============================================================
    # 3. ADD SOFT CONSTRAINTS
    # ============================================================
    #
    # These produce penalties/rewards.
    #
    # They do NOT make the model infeasible.
    # ============================================================

    preferred_day_result = (
        add_preferred_day_constraints(
            timetable
        )
    )

    workload_result = (
        add_workload_constraints(
            timetable
        )
    )

    gap_result = (
        add_gap_constraints(
            timetable
        )
    )

    distribution_result = (
        add_distribution_constraints(
            timetable
        )
    )

    quality_result = (
        add_timetable_quality_constraints(
            timetable
        )
    )

    consecutive_result = (
        add_consecutive_theory_lab_constraints(
            timetable
        )
    )

    # ============================================================
    # 4. EXTRACT PENALTIES
    # ============================================================

    preferred_day_penalties = (
        extract_penalties(
            preferred_day_result
        )
    )

    workload_penalties = (
        extract_penalties(
            workload_result
        )
    )

    gap_penalties = (
        extract_penalties(
            gap_result
        )
    )

    # ============================================================
    # 5. ADD OBJECTIVE
    # ============================================================

    add_objective(
        timetable=timetable,

        preferred_day_penalties=(
            preferred_day_penalties
        ),

        workload_penalties=(
            workload_penalties
        ),

        gap_penalties=(
            gap_penalties
        ),

        distribution_result=(
            distribution_result
        ),

        quality_result=(
            quality_result
        ),

        consecutive_result=(
            consecutive_result
        )
    )

    # ============================================================
    # 6. CREATE SOLVER
    # ============================================================

    solver = cp_model.CpSolver()

    # ------------------------------------------------------------
    # Solver configuration
    # ------------------------------------------------------------

    solver.parameters.max_time_in_seconds = (
        get_solver_timeout(data)
    )

    solver.parameters.num_search_workers = (
        get_solver_workers(data)
    )

    # ------------------------------------------------------------
    # Optional random seed
    # ------------------------------------------------------------

    seed = data.get(
        "solver_seed"
    )

    if seed is not None:

        try:

            solver.parameters.random_seed = int(
                seed
            )

        except (
            TypeError,
            ValueError
        ):
            pass

    # ============================================================
    # 7. SOLVE
    # ============================================================

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        status_name = "OPTIMAL"
    elif status == cp_model.FEASIBLE:
        status_name = "FEASIBLE"
    elif status == cp_model.INFEASIBLE:
        status_name = "INFEASIBLE"
    elif status == cp_model.MODEL_INVALID:
        status_name = "MODEL_INVALID"
    elif status == cp_model.UNKNOWN:
        status_name = "UNKNOWN"
    else:
        status_name = str(status)

    # ============================================================
    # 8. NO SOLUTION
    # ============================================================

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):

        return {
            "success": False,

            "status": status_name,

            "message": (
                "No valid timetable could be generated "
                "with the supplied hard constraints."
            ),

            "timetable": None,

            "validation": {
                "valid": False,
                "errors": [
                    {
                        "constraint": "solver",
                        "message": (
                            "The constraint system is "
                            "infeasible."
                        ),
                        "details": {}
                    }
                ],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0
            }
        }

    # ============================================================
    # 9. VALIDATE RESULT
    # ============================================================

    validation = validate_result(
        timetable,
        solver
    )

    # ============================================================
    # 10. IF VALIDATION FAILS
    # ============================================================

    if not validation["valid"]:

        return {
            "success": False,

            "status": status_name,

            "message": (
                "The solver produced a timetable, "
                "but the final validation failed."
            ),

            # Keep the generated timetable so we can inspect it
        "timetable": build_timetable_result(
            timetable,
            solver
        ),

            "validation": validation,

            # ADD THIS
        "error": validation.get("errors", [])
        }

    # ============================================================
    # 11. CONVERT SOLUTION TO JSON
    # ============================================================

    timetable_result = build_timetable_result(
        timetable,
        solver
    )

    # ============================================================
    # 12. OBJECTIVE VALUE
    # ============================================================

    objective_value = (
        solver.ObjectiveValue()
    )

    # ============================================================
    # 13. FINAL RESPONSE
    # ============================================================

    return {
        "success": True,

        "status": status_name,

        "message": (
            "Timetable generated successfully."
        ),

        "objective_value": objective_value,

        "timetable": timetable_result,

        "validation": validation
    }


# ================================================================
# EXTRACT PENALTIES
# ================================================================

def extract_penalties(result):
    """
    Soft constraint files can return either:

        list

    or:

        {
            "penalties": [...],
            "rewards": [...]
        }

    This helper makes main.py compatible with both.
    """

    if result is None:
        return []

    if isinstance(
        result,
        list
    ):
        return result

    if isinstance(
        result,
        dict
    ):
        return result.get(
            "penalties",
            []
        )

    return []


# ================================================================
# BUILD FINAL TIMETABLE
# ================================================================

def build_timetable_result(
    timetable,
    solver
):
    """
    Convert OR-Tools decision variables into a normal
    JSON-compatible timetable.

    Output structure:

        {
            "batches": [
                {
                    "batch": "...",
                    "days": [
                        {
                            "day": "Monday",
                            "periods": [...]
                        }
                    ]
                }
            ]
        }
    """

    result = []

    # ============================================================
    # EACH BATCH
    # ============================================================

    for b in range(
        len(timetable.batches)
    ):

        batch_result = {
            "batch": timetable.batch_name(
                b
            ),
            "days": []
        }

        # ========================================================
        # EACH DAY
        # ========================================================

        for d in range(
            timetable.num_days
        ):

            day_result = {
                "day": timetable.days[d],
                "periods": []
            }

            # ====================================================
            # EACH PERIOD
            # ====================================================

            for p in range(
                timetable.num_periods
            ):

                entry = get_period_entry(
                    timetable,
                    solver,
                    b,
                    d,
                    p
                )

                day_result[
                    "periods"
                ].append(
                    entry
                )

            batch_result[
                "days"
            ].append(
                day_result
            )

        result.append(
            batch_result
        )

    return result


# ================================================================
# GET PERIOD ENTRY
# ================================================================

def get_period_entry(
    timetable,
    solver,
    batch,
    day,
    period
):
    """
    Return the class occupying one timetable cell.
    """

    # ============================================================
    # NORMAL SUBJECTS
    # ============================================================

    for s in range(
        len(timetable.subjects)
    ):

        # --------------------------------------------------------
        # Theory
        # --------------------------------------------------------

        if solver.Value(
            timetable.theory_y[
                s,
                batch,
                day,
                period
            ]
        ):

            subject = timetable.subjects[
                s
            ]

            return {
                "period": period + 1,
                "type": "theory",
                "subject": (
                    timetable.subject_name(
                        s
                    )
                ),
                "faculty": get_faculty(
                    subject
                )
            }

        # --------------------------------------------------------
        # Lab
        # --------------------------------------------------------

        if solver.Value(
            timetable.lab_y[
                s,
                batch,
                day,
                period
            ]
        ):

            subject = timetable.subjects[
                s
            ]

            return {
                "period": period + 1,
                "type": "lab",
                "subject": (
                    timetable.subject_name(
                        s
                    )
                ),
                "faculty": get_faculty(
                    subject
                )
            }

    # ============================================================
    # NAAN MUDALVAN
    # ============================================================

    if solver.Value(
        timetable.naan_mudalvan[
            batch,
            day,
            period
        ]
    ):

        return {
            "period": period + 1,
            "type": "special",
            "subject": "Naan Mudalvan",
            "faculty": None
        }

    # ============================================================
    # AUDIT
    # ============================================================

    if solver.Value(
        timetable.audit[
            batch,
            day,
            period
        ]
    ):

        return {
            "period": period + 1,
            "type": "special",
            "subject": "Audit",
            "faculty": None
        }

    # ============================================================
    # IOC
    # ============================================================

    if solver.Value(
        timetable.ioc[
            batch,
            day,
            period
        ]
    ):

        return {
            "period": period + 1,
            "type": "special",
            "subject": "IOC",
            "faculty": None
        }

    # ============================================================
    # EMPTY
    # ============================================================

    return {
        "period": period + 1,
        "type": "free",
        "subject": None,
        "faculty": None
    }


# ================================================================
# FACULTY HELPER
# ================================================================

def get_faculty(subject):

    if not isinstance(
        subject,
        dict
    ):
        return None

    return (
        subject.get("faculty")
        or subject.get("faculty_id")
        or subject.get("facultyId")
        or subject.get("teacher")
    )


# ================================================================
# SOLVER TIMEOUT
# ================================================================

def get_solver_timeout(data):

    value = data.get(
        "solver_timeout",
        60
    )

    try:

        value = float(
            value
        )

        return max(
            1,
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return 60


# ================================================================
# SOLVER WORKERS
# ================================================================

def get_solver_workers(data):

    value = data.get(
        "solver_workers",
        8
    )

    try:

        value = int(
            value
        )

        return max(
            1,
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return 8


# ================================================================
# COMMAND LINE ENTRY POINT
# ================================================================

def main():

    try:

        # ========================================================
        # LOAD INPUT
        # ========================================================

        data = load_input()

        # ========================================================
        # SOLVE
        # ========================================================

        result = solve_timetable(
            data
        )

        # ========================================================
        # PRINT JSON
        # ========================================================

        print(
            json.dumps(
                result,
                indent=2,
                default=str
            )
        )

        # ========================================================
        # EXIT CODE
        # ========================================================

        if result.get(
            "success",
            False
        ):

            sys.exit(0)

        sys.exit(1)

    except Exception as error:

        # --------------------------------------------------------
        # Never return raw Python traceback to the frontend.
        # --------------------------------------------------------

        error_result = {
            "success": False,

            "status": "ERROR",

            "message": str(
                error
            ),

            "timetable": None,

            "validation": {
                "valid": False,
                "errors": [
                    {
                        "constraint": "runtime",
                        "message": str(
                            error
                        ),
                        "details": {}
                    }
                ],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0
            }
        }

        print(
            json.dumps(
                error_result,
                indent=2
            )
        )

        # --------------------------------------------------------
        # Traceback goes to stderr, not JSON stdout.
        # --------------------------------------------------------

        traceback.print_exc(
            file=sys.stderr
        )

        sys.exit(1)


# ================================================================
# RUN
# ================================================================

if __name__ == "__main__":
    main()