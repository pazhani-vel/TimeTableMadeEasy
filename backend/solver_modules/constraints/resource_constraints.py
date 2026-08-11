from solver_modules.model.variables import (
    is_compatible_lab
)


def add_resource_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]
    labs = data["labs"]

    days = data["days"]
    periods = data["periods_per_day"]

    lab_start = variables["lab_start"]
    lab_assignment = variables[
        "lab_assignment"
    ]

    # -------------------------------------------------
    # Every lab session must have exactly one
    # compatible physical lab.
    # -------------------------------------------------

    for s, subject in enumerate(
        subjects
    ):

        if not subject["has_lab"]:
            continue

        for d in range(days):

            for p in range(periods):

                if (
                    s,
                    d,
                    p
                ) not in lab_start:

                    continue

                assignments = [
                    lab_assignment[
                        s,
                        d,
                        p,
                        lab_index
                    ]

                    for lab_index, lab in (
                        enumerate(labs)
                    )

                    if (
                        s,
                        d,
                        p,
                        lab_index
                    ) in lab_assignment
                ]

                model.Add(
                    sum(assignments)
                    ==
                    lab_start[
                        s,
                        d,
                        p
                    ]
                )

    # -------------------------------------------------
    # Physical lab clash
    # -------------------------------------------------

    for lab_index, lab in enumerate(
        labs
    ):

        capacity = int(
            lab.get(
                "capacity",
                1
            )
        )

        for d in range(days):

            for p in range(periods):

                occupancy = []

                # Lab starts at current period
                for s, subject in enumerate(
                    subjects
                ):

                    if (
                        s,
                        d,
                        p,
                        lab_index
                    ) in lab_assignment:

                        occupancy.append(
                            lab_assignment[
                                s,
                                d,
                                p,
                                lab_index
                            ]
                        )

                # Lab started in previous period
                if p > 0:

                    for s, subject in enumerate(
                        subjects
                    ):

                        if (
                            s,
                            d,
                            p - 1,
                            lab_index
                        ) in lab_assignment:

                            occupancy.append(
                                lab_assignment[
                                    s,
                                    d,
                                    p - 1,
                                    lab_index
                                ]
                            )

                if occupancy:

                    model.Add(
                        sum(occupancy)
                        <= capacity
                    )

    # -------------------------------------------------
    # Infrastructure validation through constraints
    #
    # IT:
    #   exactly/use only 2 AC + 1 NON_AC
    #
    # AIDS:
    #   separate AIDS resources
    #
    # Compatibility is already enforced when
    # lab_assignment variables are created.
    # -------------------------------------------------

    it_ac_labs = [
        lab
        for lab in labs
        if (
            lab.get("department")
            == "IT"
            and lab.get("type")
            == "AC"
        )
    ]

    it_non_ac_labs = [
        lab
        for lab in labs
        if (
            lab.get("department")
            == "IT"
            and lab.get("type")
            == "NON_AC"
        )
    ]

    # If the resources don't exist, subjects needing
    # those resources become infeasible through the
    # assignment constraint.