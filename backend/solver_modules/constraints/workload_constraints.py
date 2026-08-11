def add_workload_constraints(
    model,
    data,
    variables
):

    staff = data["staff"]

    days = data["days"]
    periods = data["periods_per_day"]

    teach = variables["teach"]

    daily_load = {}
    weekly_load = {}

    daily_range = {}
    weekly_range = {}

    for staff_name, staff_id in (
        variables["staff_index"].items()
    ):

        daily_values = []

        # ---------------------------------------------
        # Daily workload
        # ---------------------------------------------

        for d in range(days):

            load = model.NewIntVar(
                0,
                periods,
                (
                    f"daily_load_"
                    f"{staff_id}_{d}"
                )
            )

            model.Add(
                load
                ==
                sum(
                    teach[
                        staff_id,
                        d,
                        p
                    ]
                    for p in range(periods)
                )
            )

            daily_load[
                staff_id,
                d
            ] = load

            daily_values.append(
                load
            )

        # ---------------------------------------------
        # Weekly workload
        # ---------------------------------------------

        weekly = model.NewIntVar(
            0,
            days * periods,
            f"weekly_load_{staff_id}"
        )

        model.Add(
            weekly
            ==
            sum(daily_values)
        )

        weekly_load[
            staff_id
        ] = weekly

        # ---------------------------------------------
        # Maximum daily load
        # ---------------------------------------------

        max_daily = model.NewIntVar(
            0,
            periods,
            f"max_daily_{staff_id}"
        )

        min_daily = model.NewIntVar(
            0,
            periods,
            f"min_daily_{staff_id}"
        )

        model.AddMaxEquality(
            max_daily,
            daily_values
        )

        model.AddMinEquality(
            min_daily,
            daily_values
        )

        daily_diff = model.NewIntVar(
            0,
            periods,
            f"daily_range_{staff_id}"
        )

        model.Add(
            daily_diff
            ==
            max_daily
            - min_daily
        )

        daily_range[
            staff_id
        ] = daily_diff

    # -------------------------------------------------
    # Overall weekly staff workload balance
    # -------------------------------------------------

    if staff:

        weekly_values = [
            weekly_load[
                staff_id
            ]
            for staff_id in weekly_load
        ]

        max_weekly = model.NewIntVar(
            0,
            days * periods,
            "max_weekly_staff_load"
        )

        min_weekly = model.NewIntVar(
            0,
            days * periods,
            "min_weekly_staff_load"
        )

        model.AddMaxEquality(
            max_weekly,
            weekly_values
        )

        model.AddMinEquality(
            min_weekly,
            weekly_values
        )

        overall_weekly_range = (
            model.NewIntVar(
                0,
                days * periods,
                "overall_weekly_range"
            )
        )

        model.Add(
            overall_weekly_range
            ==
            max_weekly
            - min_weekly
        )

        weekly_range[
            "overall"
        ] = overall_weekly_range

    variables[
        "daily_load"
    ] = daily_load

    variables[
        "weekly_load"
    ] = weekly_load

    variables[
        "daily_range"
    ] = daily_range

    variables[
        "weekly_range"
    ] = weekly_range