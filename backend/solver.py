from ortools.sat.python import cp_model


# ================================================================
# SOLVER CONFIGURATION
# ================================================================

DEFAULT_TIMEOUT = 60
DEFAULT_WORKERS = 8
DEFAULT_RANDOM_SEED = 42


# ================================================================
# CREATE SOLVER
# ================================================================

def create_solver(data=None):
    """
    Create and configure the OR-Tools CP-SAT solver.

    Configuration can be supplied through the input:

        {
            "solver_timeout": 60,
            "solver_workers": 8,
            "solver_seed": 42
        }
    """

    if data is None:
        data = {}

    solver = cp_model.CpSolver()

    # ============================================================
    # TIME LIMIT
    # ============================================================

    timeout = get_timeout(
        data.get(
            "solver_timeout",
            DEFAULT_TIMEOUT
        )
    )

    solver.parameters.max_time_in_seconds = (
        timeout
    )

    # ============================================================
    # NUMBER OF WORKERS
    # ============================================================

    workers = get_workers(
        data.get(
            "solver_workers",
            DEFAULT_WORKERS
        )
    )

    solver.parameters.num_search_workers = (
        workers
    )

    # ============================================================
    # RANDOM SEED
    # ============================================================

    seed = get_seed(
        data.get(
            "solver_seed",
            DEFAULT_RANDOM_SEED
        )
    )

    solver.parameters.random_seed = seed

    return solver


# ================================================================
# SOLVE MODEL
# ================================================================

def solve_model(
    model,
    data=None
):
    """
    Solve a CP-SAT model.

    Parameters
    ----------
    model:
        OR-Tools CpModel object.

    data:
        Solver configuration.

    Returns
    -------
    dictionary containing:

        status
        status_name
        solver
        objective_value
        wall_time
        conflicts
        branches
    """

    # ============================================================
    # CREATE SOLVER
    # ============================================================

    solver = create_solver(
        data
    )

    # ============================================================
    # SOLVE
    # ============================================================

    status = solver.Solve(
        model
    )

    # ============================================================
    # STATUS
    # ============================================================

    status_name = solver.StatusName(
        status
    )

    # ============================================================
    # RESULT
    # ============================================================

    result = {
        "status": status,
        "status_name": status_name,

        "solver": solver,

        "has_solution": (
            status
            in (
                cp_model.OPTIMAL,
                cp_model.FEASIBLE
            )
        ),

        "is_optimal": (
            status
            ==
            cp_model.OPTIMAL
        ),

        "is_feasible": (
            status
            ==
            cp_model.FEASIBLE
        ),

        "is_infeasible": (
            status
            ==
            cp_model.INFEASIBLE
        ),

        "is_unknown": (
            status
            ==
            cp_model.UNKNOWN
        ),

        "objective_value": (
            solver.ObjectiveValue()
            if status
            in (
                cp_model.OPTIMAL,
                cp_model.FEASIBLE
            )
            else None
        ),

        "best_bound": (
            solver.BestObjectiveBound()
            if status
            in (
                cp_model.OPTIMAL,
                cp_model.FEASIBLE
            )
            else None
        ),

        "wall_time": solver.WallTime(),

        "user_time": solver.UserTime(),

        "branches": solver.NumBranches(),

        "conflicts": solver.NumConflicts()
    }

    return result


# ================================================================
# CHECK SUCCESS
# ================================================================

def has_solution(
    status
):
    """
    Return True if the solver found a usable timetable.
    """

    return status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    )


# ================================================================
# CHECK OPTIMAL
# ================================================================

def is_optimal(
    status
):
    """
    Return True only if the solver proved optimality.
    """

    return status == cp_model.OPTIMAL


# ================================================================
# CHECK INFEASIBLE
# ================================================================

def is_infeasible(
    status
):
    """
    Return True if no timetable satisfies all hard constraints.
    """

    return status == cp_model.INFEASIBLE


# ================================================================
# STATUS MESSAGE
# ================================================================

def get_status_message(
    status
):
    """
    Convert OR-Tools status into a user-friendly message.
    """

    if status == cp_model.OPTIMAL:

        return (
            "Optimal timetable found. "
            "All hard constraints are satisfied "
            "and the best objective value was found."
        )

    if status == cp_model.FEASIBLE:

        return (
            "A feasible timetable was found. "
            "All hard constraints are satisfied, "
            "but optimality was not proven within "
            "the solver time limit."
        )

    if status == cp_model.INFEASIBLE:

        return (
            "No timetable satisfies all hard constraints."
        )

    if status == cp_model.MODEL_INVALID:

        return (
            "The timetable model is invalid. "
            "Check the model and constraint definitions."
        )

    if status == cp_model.UNKNOWN:

        return (
            "The solver could not determine whether "
            "a feasible timetable exists."
        )

    return (
        "Unknown solver status."
    )


# ================================================================
# SAFE INTEGER CONVERSION
# ================================================================

def get_workers(
    value
):
    """
    Get a valid number of solver workers.
    """

    try:

        value = int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        value = DEFAULT_WORKERS

    return max(
        1,
        value
    )


# ================================================================
# SAFE TIMEOUT CONVERSION
# ================================================================

def get_timeout(
    value
):
    """
    Get a valid solver timeout.
    """

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        value = DEFAULT_TIMEOUT

    return max(
        1.0,
        value
    )


# ================================================================
# SAFE SEED CONVERSION
# ================================================================

def get_seed(
    value
):
    """
    Get a valid random seed.
    """

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return DEFAULT_RANDOM_SEED