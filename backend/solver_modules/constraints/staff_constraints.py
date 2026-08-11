def add_staff_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]
    lab_y = variables["lab_y"]
    lab_start = variables["lab_start"]

    teach = variables["teach"]
    staff_index = variables["staff_index"]

    # -------------------------------------------------
    # Connect teach variables to actual classes
    # -------------------------------------------------

    for staff_name, staff_id in (
        staff_index.items()
    ):

        staff_subjects = [
            s
            for s, subject in enumerate(
                subjects
            )
            if subject["staff"]
            == staff_name
        ]

        for d in range(days):

            for p in range(periods):

                class_expression = []

                for s in staff_subjects:

                    class_expression.append(
                        theory_y[s, d, p]
                    )

                    class_expression.append(
                        lab_y[s, d, p]
                    )

                model.Add(
                    teach[
                        staff_id,
                        d,
                        p
                    ]
                    == sum(
                        class_expression
                    )
                )

                # ---------------------------------
                # Staff cannot teach 2 classes
                # simultaneously
                # ---------------------------------

                model.Add(
                    teach[
                        staff_id,
                        d,
                        p
                    ]
                    <= 1
                )

        # -------------------------------------------------
        # Staff gap constraint
        # -------------------------------------------------

        for d in range(days):

            for p in range(
                periods - 1
            ):

                lab_starts = []

                for s in staff_subjects:

                    if (
                        s,
                        d,
                        p
                    ) in lab_start:

                        lab_starts.append(
                            lab_start[
                                s,
                                d,
                                p
                            ]
                        )

                # Adjacent periods are allowed only
                # when they are the same 2-period lab.
                model.Add(
                    teach[
                        staff_id,
                        d,
                        p
                    ]
                    +
                    teach[
                        staff_id,
                        d,
                        p + 1
                    ]
                    <=
                    1
                    +
                    sum(lab_starts)
                )

    # -------------------------------------------------
    # Monday morning staff/batch restriction
    #
    # If a staff member teaches a particular batch
    # in the morning on Monday, that same staff member
    # cannot teach the same batch in the morning on
    # another day.
    # -------------------------------------------------

    morning_end = min(
        4,
        periods
    )

    for staff_name, staff_id in (
        staff_index.items()
    ):

        for batch in data["batches"]:

            batch_id = batch["id"]

            batch_subjects = [
                s
                for s, subject in enumerate(
                    subjects
                )
                if (
                    subject["staff"]
                    == staff_name
                    and subject["batch_id"]
                    == batch_id
                )
            ]

            if not batch_subjects:
                continue

            morning_used = {}

            for d in range(days):

                value = model.NewBoolVar(
                    (
                        f"morning_staff_batch_"
                        f"{staff_id}_{batch_id}_{d}"
                    )
                )

                morning_classes = []

                for s in batch_subjects:

                    for p in range(
                        morning_end
                    ):

                        morning_classes.append(
                            theory_y[s, d, p]
                        )

                        morning_classes.append(
                            lab_y[s, d, p]
                        )

                model.Add(
                    sum(morning_classes)
                    >= value
                )

                model.Add(
                    sum(morning_classes)
                    <= (
                        len(morning_classes)
                        * value
                    )
                )

                morning_used[d] = value

            # Monday = day 0
            if days > 1:

                for d in range(
                    1,
                    days
                ):

                    model.Add(
                        morning_used[0]
                        +
                        morning_used[d]
                        <= 1
                    )