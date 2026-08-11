def add_optimization_objective(
    model,
    data,
    variables
):

    daily_range = variables.get(
        "daily_range",
        {}
    )

    weekly_range = variables.get(
        "weekly_range",
        {}
    )

    daily_penalty = sum(
        daily_range.values()
    )

    overall_weekly_penalty = sum(
        weekly_range.values()
    )

    # -------------------------------------------------
    # Objective priority
    #
    # Higher weight = more important.
    #
    # 100 -> balance daily staff workload
    # 10  -> balance weekly staff workload
    # -------------------------------------------------

    model.Minimize(
        (
            100
            * daily_penalty
        )
        +
        (
            10
            * overall_weekly_penalty
        )
    )