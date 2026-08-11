from solver_modules.utils.constants import (
    MORNING_END
)


def add_special_subject_constraints(
    model,
    data,
    variables
):

    add_naa_mudalvan_constraints(
        model,
        data,
        variables
    )

    add_audit_constraints(
        model,
        data,
        variables
    )

    add_ioc_constraints(
        model,
        data,
        variables
    )


def add_naa_mudalvan_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]
    naan_start = variables["naan_start"]

    for s, subject in enumerate(
        subjects
    ):

        if subject["subject_type"] != (
            "naan_mudalvan"
        ):
            continue

        duration = int(
            subject["theory_hours"]
        )

        starts = [
            naan_start[
                key
            ]
            for key in naan_start
            if key[0] == s
        ]

        # Exactly one continuous block
        model.Add(
            sum(starts)
            == 1
        )

        for d in range(days):

            for p in range(periods):

                covering = []

                for key, start_var in (
                    naan_start.items()
                ):

                    ss, dd, pp = key

                    if ss != s:
                        continue

                    if dd != d:
                        continue

                    if (
                        pp <= p
                        < pp + duration
                    ):

                        covering.append(
                            start_var
                        )

                if covering:

                    model.Add(
                        theory_y[
                            s,
                            d,
                            p
                        ]
                        == sum(covering)
                    )

                else:

                    model.Add(
                        theory_y[
                            s,
                            d,
                            p
                        ]
                        == 0
                    )


def add_audit_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]

    for s, subject in enumerate(
        subjects
    ):

        if subject["subject_type"] != (
            "audit"
        ):
            continue

        # Only last 2 periods
        first_allowed = max(
            0,
            periods - 2
        )

        for d in range(days):

            for p in range(
                0,
                first_allowed
            ):

                model.Add(
                    theory_y[
                        s,
                        d,
                        p
                    ]
                    == 0
                )


def add_ioc_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]

    for s, subject in enumerate(
        subjects
    ):

        if subject["subject_type"] != (
            "ioc"
        ):
            continue

        # Only last 2 periods
        first_allowed = max(
            0,
            periods - 2
        )

        for d in range(days):

            for p in range(
                0,
                first_allowed
            ):

                model.Add(
                    theory_y[
                        s,
                        d,
                        p
                    ]
                    == 0
                )