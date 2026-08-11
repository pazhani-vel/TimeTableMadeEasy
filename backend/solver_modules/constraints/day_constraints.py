def add_day_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]
    lab_start = variables["lab_start"]

    # -------------------------------------------------
    # Subject day restrictions
    # -------------------------------------------------

    for s, subject in enumerate(
        subjects
    ):

        fixed_days = subject.get(
            "fixed_days"
        )

        allowed_days = subject.get(
            "allowed_days"
        )

        # Fixed days have priority.
        restricted_days = (
            fixed_days
            if fixed_days is not None
            else allowed_days
        )

        if restricted_days is None:
            continue

        restricted_days = set(
            restricted_days
        )

        for d in range(days):

            if d in restricted_days:
                continue

            # No theory on this day
            for p in range(periods):

                model.Add(
                    theory_y[s, d, p]
                    == 0
                )

            # No lab start on this day
            for p in range(periods):

                if (
                    s,
                    d,
                    p
                ) in lab_start:

                    model.Add(
                        lab_start[
                            s,
                            d,
                            p
                        ]
                        == 0
                    )

    # -------------------------------------------------
    # The morning must not start with two consecutive
    # empty / library periods.
    #
    # For each batch and each day, at least one of
    # Period 1 (index 0) or Period 2 (index 1) must
    # contain a real class (theory or lab).
    #
    # sum(P1_classes + P2_classes) >= 1
    # -------------------------------------------------

    if periods >= 2:

        for batch in data["batches"]:

            batch_id = batch["id"]

            batch_subjects = [
                s
                for s, subject in enumerate(
                    subjects
                )
                if subject["batch_id"]
                == batch_id
            ]

            for d in range(days):

                morning_classes = []

                for p in (0, 1):

                    for s in batch_subjects:

                        morning_classes.append(
                            theory_y[s, d, p]
                        )

                        morning_classes.append(
                            variables[
                                "lab_y"
                            ][s, d, p]
                        )

                if morning_classes:

                    model.Add(
                        sum(morning_classes)
                        >= 1
                    )