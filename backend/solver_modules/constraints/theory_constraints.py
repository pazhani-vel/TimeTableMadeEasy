def add_theory_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]
    day_used = variables["day_used"]

    for s, subject in enumerate(
        subjects
    ):

        hours = int(
            subject["theory_hours"]
        )

        # -----------------------------------------
        # Exact theory hours
        # -----------------------------------------

        model.Add(
            sum(
                theory_y[s, d, p]
                for d in range(days)
                for p in range(periods)
            )
            == hours
        )

        # -----------------------------------------
        # Link day_used
        # -----------------------------------------

        for d in range(days):

            daily_total = sum(
                theory_y[s, d, p]
                for p in range(periods)
            )

            model.Add(
                daily_total
                <= periods
                * day_used[s, d]
            )

            model.Add(
                daily_total
                >= day_used[s, d]
            )

        # -----------------------------------------
        # Theory maximum 2 days
        # -----------------------------------------

        model.Add(
            sum(
                day_used[s, d]
                for d in range(days)
            )
            <= 2
        )