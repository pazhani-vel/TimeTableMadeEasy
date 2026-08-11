from solver_modules.utils.constants import (
    LAB_PERIODS
)


def add_lab_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    lab_start = variables["lab_start"]
    day_used = variables["day_used"]

    for s, subject in enumerate(
        subjects
    ):

        if not subject["has_lab"]:
            continue

        lab_hours = int(
            subject["lab_hours"]
        )

        sessions = (
            lab_hours // LAB_PERIODS
        )

        # -----------------------------------------
        # Exact number of lab sessions
        # -----------------------------------------

        starts = [
            lab_start[s, d, p]
            for d in range(days)
            for p in range(periods)
            if (
                s, d, p
            ) in lab_start
        ]

        model.Add(
            sum(starts)
            == sessions
        )

        # -----------------------------------------
        # Maximum one lab/day
        # -----------------------------------------

        for d in range(days):

            daily_lab_starts = [
                lab_start[s, d, p]
                for p in range(periods)
                if (
                    s, d, p
                ) in lab_start
            ]

            model.Add(
                sum(
                    daily_lab_starts
                )
                <= 1
            )

            # -------------------------------------
            # Theory and lab different days
            # -------------------------------------

            model.Add(
                sum(
                    daily_lab_starts
                )
                + day_used[s, d]
                <= 1
            )

        # -----------------------------------------
        # Lab cannot cross lunch
        #
        # For 8 periods:
        # P4 = index 3
        # P5 = index 4
        #
        # Therefore lab cannot start at index 3.
        # -----------------------------------------

        half = periods // 2

        for d in range(days):

            if (
                s,
                d,
                half - 1
            ) in lab_start:

                model.Add(
                    lab_start[
                        s,
                        d,
                        half - 1
                    ]
                    == 0
                )