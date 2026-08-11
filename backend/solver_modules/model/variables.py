from ortools.sat.python import cp_model

from solver_modules.utils.constants import (
    LAB_PERIODS,
    MORNING_END
)


def create_theory_variables(
    model,
    data
):

    subjects = data["subjects"]
    days = data["days"]
    periods = data["periods_per_day"]

    theory_y = {}

    for s in range(len(subjects)):

        for d in range(days):

            for p in range(periods):

                theory_y[s, d, p] = (
                    model.NewBoolVar(
                        f"theory_{s}_{d}_{p}"
                    )
                )

    return theory_y


def create_day_variables(
    model,
    data
):

    subjects = data["subjects"]
    days = data["days"]

    day_used = {}

    for s in range(len(subjects)):

        for d in range(days):

            day_used[s, d] = (
                model.NewBoolVar(
                    f"theory_day_{s}_{d}"
                )
            )

    return day_used


def create_lab_variables(
    model,
    data
):

    subjects = data["subjects"]
    days = data["days"]
    periods = data["periods_per_day"]

    lab_start = {}
    lab_y = {}

    half = periods // 2

    for s, subject in enumerate(
        subjects
    ):

        for d in range(days):

            for p in range(periods):

                lab_y[s, d, p] = (
                    model.NewBoolVar(
                        f"lab_{s}_{d}_{p}"
                    )
                )

                can_start = (
                    p <= periods - LAB_PERIODS
                    and p != half - 1
                )

                if (
                    subject["has_lab"]
                    and can_start
                ):

                    lab_start[s, d, p] = (
                        model.NewBoolVar(
                            f"lab_start_{s}_{d}_{p}"
                        )
                    )

    # Lab occupancy
    for s, subject in enumerate(
        subjects
    ):

        for d in range(days):

            for p in range(periods):

                covering = []

                if (
                    s, d, p
                ) in lab_start:

                    covering.append(
                        lab_start[s, d, p]
                    )

                if p > 0 and (
                    s,
                    d,
                    p - 1
                ) in lab_start:

                    covering.append(
                        lab_start[
                            s,
                            d,
                            p - 1
                        ]
                    )

                if covering:

                    model.Add(
                        lab_y[s, d, p]
                        == sum(covering)
                    )

                else:

                    model.Add(
                        lab_y[s, d, p]
                        == 0
                    )

    return lab_start, lab_y


def create_naa_mudalvan_variables(
    model,
    data
):

    subjects = data["subjects"]

    days = data["days"]
    periods = data["periods_per_day"]

    naan_start = {}

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

        for d in range(days):

            # Morning
            for p in range(
                0,
                MORNING_END - duration + 1
            ):

                naan_start[
                    s,
                    d,
                    p
                ] = model.NewBoolVar(
                    f"naan_start_{s}_{d}_{p}"
                )

            # Afternoon
            for p in range(
                MORNING_END,
                periods - duration + 1
            ):

                naan_start[
                    s,
                    d,
                    p
                ] = model.NewBoolVar(
                    f"naan_start_{s}_{d}_{p}"
                )

    return naan_start


def create_staff_variables(
    model,
    data
):

    staff = data["staff"]

    staff_index = {
        name: index
        for index, name in enumerate(staff)
    }

    teach = {}

    for staff_name, staff_id in (
        staff_index.items()
    ):

        for d in range(
            data["days"]
        ):

            for p in range(
                data["periods_per_day"]
            ):

                teach[
                    staff_id,
                    d,
                    p
                ] = model.NewBoolVar(
                    (
                        f"teach_"
                        f"{staff_id}_"
                        f"{d}_"
                        f"{p}"
                    )
                )

    return teach, staff_index

def create_resource_variables(
    model,
    data,
    lab_start
):

    labs = data["labs"]
    subjects = data["subjects"]

    lab_assignment = {}

    for s, subject in enumerate(
        subjects
    ):

        if not subject["has_lab"]:
            continue

        for d in range(
            data["days"]
        ):

            for p in range(
                data["periods_per_day"]
            ):

                if (
                    s, d, p
                ) not in lab_start:
                    continue

                for lab_index, lab in enumerate(
                    labs
                ):

                    if is_compatible_lab(
                        subject,
                        lab
                    ):

                        lab_assignment[
                            s,
                            d,
                            p,
                            lab_index
                        ] = model.NewBoolVar(
                            (
                                f"lab_assign_"
                                f"{s}_{d}_{p}_"
                                f"{lab_index}"
                            )
                        )

    return lab_assignment


def is_compatible_lab(
    subject,
    lab
):

    department = subject.get(
        "department",
        "IT"
    )

    required_type = subject.get(
        "lab_type"
    )

    lab_department = lab.get(
        "department"
    )

    lab_type = lab.get(
        "type"
    )

    # Department must match.
    if department != lab_department:
        return False

    # Explicit lab type.
    if required_type:

        return (
            required_type
            == lab_type
        )

    # Default IT practical
    if department == "IT":

        return lab_type in (
            "AC",
            "NON_AC"
        )

    # AIDS
    if department == "AIDS":

        return lab_type == "AIDS"

    return False


def create_variables(
    model,
    data
):

    variables = {}

    variables["theory_y"] = (
        create_theory_variables(
            model,
            data
        )
    )

    variables["day_used"] = (
        create_day_variables(
            model,
            data
        )
    )

    (
        variables["lab_start"],
        variables["lab_y"]
    ) = create_lab_variables(
        model,
        data
    )

    variables["naan_start"] = (
        create_naa_mudalvan_variables(
            model,
            data
        )
    )

    (
        variables["teach"],
        variables["staff_index"]
    ) = create_staff_variables(
        model,
        data
    )

    variables["lab_assignment"] = (
        create_resource_variables(
            model,
            data,
            variables["lab_start"]
        )
    )

    return variables