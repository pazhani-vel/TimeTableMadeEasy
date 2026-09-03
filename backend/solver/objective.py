from ortools.sat.python import cp_model


# ================================================================
# SOFT CONSTRAINT WEIGHTS
# ================================================================
#
# Higher weight = more important.
#
# Current priority:
#
# 1. Subject distribution
# 2. Gaps
# 3. Workload balance
# 4. Preferred days
# 5. General timetable quality
#
# These can be changed later without changing the individual
# soft-constraint files.
# ================================================================

DEFAULT_WEIGHTS = {
    "distribution": 10,
    "gaps": 8,
    "workload": 6,
    "preferred_days": 5,
    "quality": 3,
}


def add_objective(
    timetable,
    preferred_day_penalties,
    workload_penalties,
    gap_penalties,
    distribution_result,
    quality_result,
    consecutive_result=None,
):
    """
    Combine all SOFT constraints and create the final
    optimization objective.

    Important:

        This function DOES NOT add hard constraints.

    Hard constraints must already have been added by:

        hard_constraints/
            theory.py
            lab.py
            batch.py
            faculty.py
            day.py
            special.py
            resource.py

    The solver will first search only among valid timetables
    and then minimize the weighted soft-constraint score.
    """

    model = timetable.model

    # ============================================================
    # GET CONFIGURED WEIGHTS
    # ============================================================

    weights = get_weights(timetable)

    # ============================================================
    # DISTRIBUTION
    # ============================================================

    distribution_penalties = (
        distribution_result.get(
            "penalties",
            []
        )
    )

    distribution_rewards = (
        distribution_result.get(
            "rewards",
            []
        )
    )

    # ============================================================
    # QUALITY
    # ============================================================

    quality_penalties = (
        quality_result.get(
            "penalties",
            []
        )
    )

    quality_rewards = (
        quality_result.get(
            "rewards",
            []
        )
    )

    # ============================================================
    # BUILD OBJECTIVE
    # ============================================================
    #
    # Objective:
    #
    #     MINIMIZE(
    #
    #         distribution violations
    #       + gap violations
    #       + workload violations
    #       + preferred-day violations
    #       + quality violations
    #
    #       - rewards
    #
    #     )
    #
    # ============================================================

    objective_terms = []

    # ------------------------------------------------------------
    # 1. PREFERRED DAYS
    # ------------------------------------------------------------

    add_weighted_terms(
        objective_terms,
        preferred_day_penalties,
        weights["preferred_days"]
    )

    # ------------------------------------------------------------
    # 2. WORKLOAD
    # ------------------------------------------------------------

    add_weighted_terms(
        objective_terms,
        workload_penalties,
        weights["workload"]
    )

    # ------------------------------------------------------------
    # 3. GAPS
    # ------------------------------------------------------------

    add_weighted_terms(
        objective_terms,
        gap_penalties,
        weights["gaps"]
    )

    # ------------------------------------------------------------
    # 4. DISTRIBUTION
    # ------------------------------------------------------------

    add_weighted_terms(
        objective_terms,
        distribution_penalties,
        weights["distribution"]
    )

    # ------------------------------------------------------------
    # 5. GENERAL QUALITY PENALTIES
    # ------------------------------------------------------------

    add_weighted_terms(
        objective_terms,
        quality_penalties,
        weights["quality"]
    )

    # ============================================================
    # REWARDS
    # ============================================================
    #
    # Rewards are subtracted because we are MINIMIZING.
    #
    # Example:
    #
    # consecutive classes = reward
    #
    # More consecutive classes
    #     ↓
    # Larger reward
    #     ↓
    # Smaller objective
    #
    # ============================================================

    add_weighted_rewards(
        objective_terms,
        distribution_rewards,
        weights["distribution"]
    )

    add_weighted_rewards(
        objective_terms,
        quality_rewards,
        weights["quality"]
    )

    # ------------------------------------------------------------
    # CONSECUTIVE THEORY-LAB REWARDS
    # ------------------------------------------------------------

    if consecutive_result is not None:

        consecutive_rewards = (
            consecutive_result.get(
                "rewards",
                []
            )
        )

        add_weighted_rewards(
            objective_terms,
            consecutive_rewards,
            weights.get("quality", 3)
        )

    # ============================================================
    # SET FINAL OBJECTIVE
    # ============================================================

    if objective_terms:

        model.Minimize(
            sum(objective_terms)
        )

    else:

        # --------------------------------------------------------
        # No soft constraints were added.
        #
        # The solver will simply find any valid timetable.
        # --------------------------------------------------------

        model.Minimize(
            0
        )

    # Store the objective information so that other files,
    # especially result_validator.py, can inspect it later.
    timetable.objective_weights = weights

    timetable.objective_terms = objective_terms

    return model


# ================================================================
# WEIGHTS
# ================================================================

def get_weights(timetable):
    """
    Read objective weights from input data.

    Optional input:

        {
            "objective_weights": {
                "distribution": 10,
                "gaps": 8,
                "workload": 6,
                "preferred_days": 5,
                "quality": 3
            }
        }

    If a weight is not supplied, the default is used.
    """

    weights = DEFAULT_WEIGHTS.copy()

    data = getattr(
        timetable,
        "data",
        {}
    )

    custom_weights = data.get(
        "objective_weights",
        {}
    )

    if not isinstance(
        custom_weights,
        dict
    ):
        return weights

    for key in weights:

        if key not in custom_weights:
            continue

        try:

            value = float(
                custom_weights[key]
            )

            if value >= 0:
                weights[key] = value

        except (
            TypeError,
            ValueError
        ):
            pass

    return weights


# ================================================================
# ADD PENALTIES
# ================================================================

def add_weighted_terms(
    objective_terms,
    variables,
    weight
):
    """
    Add:

        variable * weight

    to the objective.

    Works with both:

        BoolVar
        IntVar
    """

    if not variables:
        return

    if weight == 0:
        return

    for variable in variables:

        objective_terms.append(
            weight * variable
        )


# ================================================================
# ADD REWARDS
# ================================================================

def add_weighted_rewards(
    objective_terms,
    variables,
    weight
):
    """
    Rewards are subtracted from the objective.

    Example:

        reward = 1
        weight = 5

        objective contribution = -5
    """

    if not variables:
        return

    if weight == 0:
        return

    for variable in variables:

        objective_terms.append(
            -weight * variable
        )


# ================================================================
# OBJECTIVE SUMMARY
# ================================================================

def get_objective_summary(timetable):
    """
    Return the objective configuration.

    Useful for debugging and API responses.
    """

    weights = getattr(
        timetable,
        "objective_weights",
        DEFAULT_WEIGHTS
    )

    return {
        "weights": weights,
        "priority": [
            "distribution",
            "gaps",
            "workload",
            "preferred_days",
            "quality",
        ]
    }