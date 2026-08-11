from copy import deepcopy

from solver_modules.utils.constants import (
    DEFAULT_DAYS,
    DEFAULT_PERIODS_PER_DAY,
    DEFAULT_SOLVER_TIME_LIMIT,
    DEFAULT_SOLVER_WORKERS,
    DEFAULT_IT_BATCHES
)


DAY_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}


def make_batch_id(batch):

    if isinstance(batch, str):
        return batch

    department = batch.get(
        "department",
        "IT"
    )

    year = batch.get("year")

    batch_name = batch.get(
        "batch",
        batch.get("name")
    )

    if year is not None and batch_name:
        return f"{department}_{year}_{batch_name}"

    return batch.get(
        "id",
        batch_name
    )


def normalize_days(day_values):

    if day_values is None:
        return None

    if isinstance(day_values, str):
        day_values = [day_values]

    result = []

    for day in day_values:

        if isinstance(day, int):

            result.append(day)

        elif isinstance(day, str):

            if day not in DAY_INDEX:
                raise ValueError(
                    f"Invalid day: {day}"
                )

            result.append(
                DAY_INDEX[day]
            )

    return sorted(set(result))


def load_model_data(data):

    data = deepcopy(data)

    days = int(
        data.get(
            "days",
            DEFAULT_DAYS
        )
    )

    periods_per_day = int(
        data.get(
            "periods_per_day",
            DEFAULT_PERIODS_PER_DAY
        )
    )

    # -------------------------------------------------
    # Batches
    # -------------------------------------------------

    raw_batches = data.get(
        "batches"
    )

    if not raw_batches:

        raw_batches = deepcopy(
            DEFAULT_IT_BATCHES
        )

    batches = []

    for batch in raw_batches:

        if isinstance(batch, str):

            batches.append({
                "id": batch,
                "department": "IT",
                "year": None,
                "batch": batch
            })

        else:

            batch_copy = deepcopy(batch)

            batch_id = make_batch_id(
                batch_copy
            )

            batch_copy["id"] = batch_id

            batches.append(
                batch_copy
            )

    batch_map = {
        batch["id"]: batch
        for batch in batches
    }

    # -------------------------------------------------
    # Subjects
    # -------------------------------------------------

    subjects = []

    for index, raw_subject in enumerate(
        data.get("subjects", [])
    ):

        subject = deepcopy(
            raw_subject
        )

        subject["id"] = subject.get(
            "id",
            f"SUBJECT_{index + 1}"
        )

        # ---------------------------------------------
        # Department
        # ---------------------------------------------

        subject["department"] = subject.get(
            "department",
            "IT"
        )

        # ---------------------------------------------
        # Batch ID
        # ---------------------------------------------

        if "batch_id" in subject:

            batch_id = subject["batch_id"]

        elif isinstance(
            subject.get("batch"),
            dict
        ):

            batch_id = make_batch_id(
                subject["batch"]
            )

        elif (
            subject.get("year") is not None
            and subject.get("batch")
        ):

            batch_id = (
                f'{subject["department"]}_'
                f'{subject["year"]}_'
                f'{subject["batch"]}'
            )

        else:

            batch_id = subject.get(
                "batch"
            )

        subject["batch_id"] = batch_id

        # ---------------------------------------------
        # Subject type
        # ---------------------------------------------

        subject["subject_type"] = subject.get(
            "subject_type",
            subject.get(
                "type",
                "regular"
            )
        )

        # ---------------------------------------------
        # Hours
        # ---------------------------------------------

        subject["theory_hours"] = int(
            subject.get(
                "theory_hours",
                0
            )
        )

        subject["has_lab"] = bool(
            subject.get(
                "has_lab",
                False
            )
        )

        subject["lab_hours"] = int(
            subject.get(
                "lab_hours",
                0
            )
        )

        # ---------------------------------------------
        # Lab type
        # ---------------------------------------------

        subject["lab_type"] = subject.get(
            "lab_type"
        )

        # ---------------------------------------------
        # Days
        # ---------------------------------------------

        subject["fixed_days"] = normalize_days(
            subject.get("fixed_days")
        )

        subject["allowed_days"] = normalize_days(
            subject.get("allowed_days")
        )

        subject["preferred_days"] = normalize_days(
            subject.get("preferred_days")
        )

        subjects.append(
            subject
        )

    # -------------------------------------------------
    # Labs
    # -------------------------------------------------

    labs = []

    for index, raw_lab in enumerate(
        data.get("labs", [])
    ):

        lab = deepcopy(
            raw_lab
        )

        lab["id"] = lab.get(
            "id",
            f"LAB_{index + 1}"
        )

        lab["department"] = lab.get(
            "department",
            "IT"
        )

        lab["type"] = lab.get(
            "type",
            "AC"
        )

        lab["capacity"] = int(
            lab.get(
                "capacity",
                1
            )
        )

        labs.append(
            lab
        )

    # -------------------------------------------------
    # Staff
    # -------------------------------------------------

    staff = []

    explicit_staff = data.get(
        "staff",
        []
    )

    for item in explicit_staff:

        if isinstance(item, str):
            staff.append(item)

        elif isinstance(item, dict):

            name = item.get(
                "name"
            )

            if name:
                staff.append(name)

    # Add staff from subjects
    for subject in subjects:

        name = subject.get(
            "staff"
        )

        if name and name not in staff:
            staff.append(name)

    staff = sorted(
        set(staff)
    )

    # -------------------------------------------------
    # Final structure
    # -------------------------------------------------

    model_data = {

        "days": days,

        "periods_per_day":
            periods_per_day,

        "batches":
            batches,

        "batch_map":
            batch_map,

        "subjects":
            subjects,

        "labs":
            labs,

        "staff":
            staff,

        "solver_time_limit_seconds":
            float(
                data.get(
                    "solver_time_limit_seconds",
                    DEFAULT_SOLVER_TIME_LIMIT
                )
            ),

        "solver_workers":
            int(
                data.get(
                    "solver_workers",
                    DEFAULT_SOLVER_WORKERS
                )
            )
    }

    return model_data