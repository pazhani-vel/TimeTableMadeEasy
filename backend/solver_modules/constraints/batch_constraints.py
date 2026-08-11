def add_batch_constraints(
    model,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = variables["theory_y"]
    lab_y = variables["lab_y"]

    for batch in data["batches"]:

        batch_id = batch["id"]

        subject_indexes = [
            s
            for s, subject in enumerate(
                subjects
            )
            if subject["batch_id"]
            == batch_id
        ]

        for d in range(days):

            for p in range(periods):

                classes = []

                for s in subject_indexes:

                    classes.append(
                        theory_y[s, d, p]
                    )

                    classes.append(
                        lab_y[s, d, p]
                    )

                # ---------------------------------
                # One batch cannot have
                # two classes at same time
                # ---------------------------------

                model.Add(
                    sum(classes)
                    <= 1
                )