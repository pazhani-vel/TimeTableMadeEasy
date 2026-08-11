from solver_modules.utils.constants import (
    DAY_NAMES
)


def format_timetable(
    solver,
    data,
    variables
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    batches = data["batches"]
    labs = data["labs"]

    theory_y = variables["theory_y"]
    lab_y = variables["lab_y"]
    lab_start = variables["lab_start"]

    lab_assignment = variables[
        "lab_assignment"
    ]

    timetable = {}

    # -------------------------------------------------
    # Initialize
    # -------------------------------------------------

    for batch in batches:

        batch_id = batch["id"]

        timetable[batch_id] = [
            [None for _ in range(periods)]
            for _ in range(days)
        ]

    # -------------------------------------------------
    # Theory
    # -------------------------------------------------

    for s, subject in enumerate(
        subjects
    ):

        batch_id = subject["batch_id"]

        for d in range(days):

            for p in range(periods):

                if solver.Value(
                    theory_y[s, d, p]
                ):

                    timetable[
                        batch_id
                    ][d][p] = {

                        "subject":
                            subject["name"],

                        "staff":
                            subject["staff"],

                        "type":
                            "theory"
                    }

    # -------------------------------------------------
    # Labs
    # -------------------------------------------------

    for s, subject in enumerate(
        subjects
    ):

        if not subject["has_lab"]:
            continue

        batch_id = subject[
            "batch_id"
        ]

        for d in range(days):

            for p in range(periods):

                if (
                    s,
                    d,
                    p
                ) not in lab_start:

                    continue

                if not solver.Value(
                    lab_start[
                        s,
                        d,
                        p
                    ]
                ):

                    continue

                room_name = None

                for lab_index, lab in enumerate(
                    labs
                ):

                    key = (
                        s,
                        d,
                        p,
                        lab_index
                    )

                    if key in lab_assignment:

                        if solver.Value(
                            lab_assignment[
                                key
                            ]
                        ):

                            room_name = (
                                lab["id"]
                            )

                            break

                for offset in range(2):

                    period = p + offset

                    timetable[
                        batch_id
                    ][d][period] = {

                        "subject":
                            subject["name"],

                        "staff":
                            subject["staff"],

                        "type":
                            "lab",

                        "lab":
                            room_name
                    }

    # -------------------------------------------------
    # Library
    # -------------------------------------------------

    for batch_id in timetable:

        for d in range(days):

            for p in range(periods):

                if (
                    timetable[
                        batch_id
                    ][d][p]
                    is None
                ):

                    timetable[
                        batch_id
                    ][d][p] = {

                        "subject":
                            "Library",

                        "staff":
                            None,

                        "type":
                            "library"
                    }

    return timetable