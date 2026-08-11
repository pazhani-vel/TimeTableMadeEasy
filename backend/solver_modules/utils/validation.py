from solver_modules.utils.constants import (
    VALID_SUBJECT_TYPES,
    VALID_LAB_TYPES
)


REQUIRED_IT_BATCHES = {
    "IT_2_B1",
    "IT_2_B2",
    "IT_3_B1",
    "IT_3_B2",
    "IT_4_B1",
    "IT_4_B2"
}


def validate_input(data):

    days = data["days"]
    periods = data["periods_per_day"]

    # -------------------------------------------------
    # Timetable configuration
    # -------------------------------------------------

    if days <= 0:
        raise ValueError(
            "days must be greater than 0"
        )

    if periods <= 0:
        raise ValueError(
            "periods_per_day must be greater than 0"
        )

    if periods % 2 != 0:
        raise ValueError(
            "periods_per_day must be even because "
            "the timetable has morning and afternoon sessions."
        )

    # -------------------------------------------------
    # Batches
    # -------------------------------------------------

    batch_ids = {
        batch["id"]
        for batch in data["batches"]
    }

    missing_batches = (
        REQUIRED_IT_BATCHES
        - batch_ids
    )

    if missing_batches:

        raise ValueError(
            "Missing required IT batches: "
            + ", ".join(
                sorted(missing_batches)
            )
        )

    # -------------------------------------------------
    # Labs
    # -------------------------------------------------

    labs = data["labs"]

    it_ac = [
        lab
        for lab in labs
        if (
            lab.get("department")
            == "IT"
            and lab.get("type")
            == "AC"
        )
    ]

    it_non_ac = [
        lab
        for lab in labs
        if (
            lab.get("department")
            == "IT"
            and lab.get("type")
            == "NON_AC"
        )
    ]

    if len(it_ac) != 2:

        raise ValueError(
            "IT must have exactly 2 AC labs."
        )

    if len(it_non_ac) != 1:

        raise ValueError(
            "IT must have exactly 1 non-AC lab."
        )

    # -------------------------------------------------
    # Subjects
    # -------------------------------------------------

    if not data["subjects"]:

        raise ValueError(
            "At least one subject is required."
        )

    subject_ids = set()

    for subject in data["subjects"]:

        subject_id = subject["id"]

        if subject_id in subject_ids:

            raise ValueError(
                f"Duplicate subject id: "
                f"{subject_id}"
            )

        subject_ids.add(
            subject_id
        )

        # ---------------------------------------------
        # Name
        # ---------------------------------------------

        if not subject.get("name"):

            raise ValueError(
                f"Subject {subject_id} "
                "must have a name."
            )

        # ---------------------------------------------
        # Staff
        # ---------------------------------------------

        if not subject.get("staff"):

            raise ValueError(
                f"Subject {subject['name']} "
                "must have a staff member."
            )

        # ---------------------------------------------
        # Batch
        # ---------------------------------------------

        if (
            subject["batch_id"]
            not in batch_ids
        ):

            raise ValueError(
                f"Subject {subject['name']} "
                f"uses unknown batch "
                f"{subject['batch_id']}."
            )

        # ---------------------------------------------
        # Theory hours
        # ---------------------------------------------

        theory_hours = int(
            subject["theory_hours"]
        )

        if theory_hours <= 0:

            raise ValueError(
                f"{subject['name']} must have "
                "at least 1 theory hour."
            )

        # ---------------------------------------------
        # Subject type
        # ---------------------------------------------

        subject_type = subject[
            "subject_type"
        ]

        if subject_type not in (
            VALID_SUBJECT_TYPES
        ):

            raise ValueError(
                f"Invalid subject type "
                f"{subject_type} for "
                f"{subject['name']}."
            )

        # ---------------------------------------------
        # Lab
        # ---------------------------------------------

        if subject["has_lab"]:

            lab_hours = int(
                subject["lab_hours"]
            )

            if (
                lab_hours <= 0
                or lab_hours % 2 != 0
            ):

                raise ValueError(
                    f"{subject['name']} lab hours "
                    "must be a positive multiple of 2."
                )

            lab_type = subject.get(
                "lab_type"
            )

            if lab_type not in (
                VALID_LAB_TYPES
            ):

                raise ValueError(
                    f"{subject['name']} needs a "
                    "valid lab_type: "
                    "AC, NON_AC or AIDS."
                )

            # -----------------------------------------
            # Department/resource separation
            # -----------------------------------------

            department = subject.get(
                "department"
            )

            if (
                department == "IT"
                and lab_type == "AIDS"
            ):

                raise ValueError(
                    f"{subject['name']} is IT but "
                    "uses AIDS lab."
                )

            if (
                department == "AIDS"
                and lab_type != "AIDS"
            ):

                raise ValueError(
                    f"{subject['name']} belongs to "
                    "AIDS and must use AIDS lab."
                )

        # ---------------------------------------------
        # Naan Mudalvan
        # ---------------------------------------------

        if subject_type == (
            "naan_mudalvan"
        ):

            if theory_hours < 2:

                raise ValueError(
                    "Naan Mudalvan should normally "
                    "have at least 2 continuous hours."
                )

            if theory_hours > 4:

                raise ValueError(
                    "Naan Mudalvan cannot exceed "
                    "4 continuous hours."
                )

        # ---------------------------------------------
        # Audit / IOC
        # ---------------------------------------------

        if subject_type in (
            "audit",
            "ioc"
        ):

            if theory_hours > 2:

                raise ValueError(
                    f"{subject_type} cannot have "
                    "more than 2 hours because it "
                    "is restricted to P7/P8."
                )

        # ---------------------------------------------
        # Days
        # ---------------------------------------------

        for field in (
            "fixed_days",
            "allowed_days",
            "preferred_days"
        ):

            values = subject.get(
                field
            )

            if values is None:
                continue

            for day in values:

                if day < 0 or day >= days:

                    raise ValueError(
                        f"{subject['name']} has "
                        f"invalid day index {day}."
                    )

    return True