import json
import os
import sys


# ================================================================
# INPUT LOADER
# ================================================================

def load_input():
    """
    Load timetable input.

    Priority:

        1. JSON passed through stdin
        2. File path passed as command-line argument
        3. input.json in the solver directory

    This allows Node.js to send JSON directly to Python.
    """

    # ============================================================
    # 1. TRY STDIN
    # ============================================================

    try:

        if not sys.stdin.isatty():

            raw_input = sys.stdin.read().strip()

            if raw_input:

                data = json.loads(
                    raw_input
                )

                return normalize_input(
                    data
                )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Invalid JSON input: {error}"
        )

    # ============================================================
    # 2. COMMAND LINE FILE
    # ============================================================

    if len(sys.argv) > 1:

        input_path = sys.argv[1]

        if not os.path.exists(
            input_path
        ):

            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

        return load_json_file(
            input_path
        )

    # ============================================================
    # 3. DEFAULT input.json
    # ============================================================

    default_path = os.path.join(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        ),
        "input.json"
    )

    if os.path.exists(
        default_path
    ):

        return load_json_file(
            default_path
        )

    # ============================================================
    # NOTHING FOUND
    # ============================================================

    raise ValueError(
        "No timetable input found. "
        "Provide JSON through stdin, "
        "a JSON file path, or solver/input.json."
    )


# ================================================================
# LOAD JSON FILE
# ================================================================

def load_json_file(
    path
):
    """
    Read JSON from a file.
    """

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Invalid JSON in {path}: {error}"
        )

    return normalize_input(
        data
    )


# ================================================================
# NORMALIZE INPUT
# ================================================================

def normalize_input(
    data
):
    """
    Normalize input so model.py can work with a predictable
    structure.

    The frontend/backend can send slightly different field names,
    but internally we use one standard structure.
    """

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Timetable input must be a JSON object."
        )

    normalized = {}

    # ============================================================
    # SUBJECTS
    # ============================================================

    normalized["subjects"] = normalize_subjects(
        data.get(
            "subjects",
            []
        )
    )

    # ============================================================
    # BATCHES
    # ============================================================

    normalized["batches"] = normalize_list(
        data.get(
            "batches",
            []
        )
    )

    # ============================================================
    # FACULTIES / STAFF
    # ============================================================
    #
    # If the input provides a separate "faculties" or "staff"
    # list, use it.
    #
    # Otherwise, build the staff list from the subjects'
    # "staff" field.
    # ============================================================

    provided_faculties = normalize_list(
        data.get(
            "faculties",
            data.get("staff", [])
        )
    )

    if not provided_faculties:

        provided_faculties = (
            extract_staff_from_subjects(
                normalized["subjects"]
            )
        )

    normalized["faculties"] = provided_faculties

    normalized["staff"] = provided_faculties

    # ============================================================
    # LABS
    # ============================================================

    normalized["labs"] = normalize_list(
        data.get(
            "labs",
            []
        )
    )

    # ============================================================
    # ROOMS
    # ============================================================

    normalized["rooms"] = normalize_list(
        data.get(
            "rooms",
            []
        )
    )

    # ============================================================
    # DAYS
    # ============================================================

    normalized["days"] = normalize_days(
        data.get(
            "days"
        )
    )

    # ============================================================
    # PERIODS
    # ============================================================

    normalized["periods"] = normalize_periods(
        data.get(
            "periods"
        )
    )

    # ============================================================
    # SPECIAL CLASS SETTINGS
    # ============================================================

    normalized[
        "naan_mudalvan_periods"
    ] = get_int(
        data.get(
            "naan_mudalvan_periods",
            data.get(
                "naan_mudalvan_hours",
                0
            )
        )
    )

    normalized[
        "audit_periods"
    ] = get_int(
        data.get(
            "audit_periods",
            0
        )
    )

    normalized[
        "ioc_periods"
    ] = get_int(
        data.get(
            "ioc_periods",
            0
        )
    )

    # ============================================================
    # OBJECTIVE WEIGHTS
    # ============================================================

    normalized[
        "objective_weights"
    ] = normalize_weights(
        data.get(
            "objective_weights",
            {}
        )
    )

    # ============================================================
    # SOLVER SETTINGS
    # ============================================================

    normalized[
        "solver_timeout"
    ] = get_number(
        data.get(
            "solver_timeout",
            60
        ),
        default=60
    )

    normalized[
        "solver_workers"
    ] = get_int(
        data.get(
            "solver_workers",
            8
        )
    )

    if normalized[
        "solver_workers"
    ] <= 0:

        normalized[
            "solver_workers"
        ] = 8

    # ============================================================
    # RANDOM SEED
    # ============================================================

    if "solver_seed" in data:

        normalized[
            "solver_seed"
        ] = get_int(
            data[
                "solver_seed"
            ]
        )

    # ============================================================
    # KEEP ADDITIONAL INPUT
    # ============================================================

    # Anything not explicitly normalized is retained so that
    # future constraints can access it.

    for key, value in data.items():

        if key not in normalized:

            normalized[
                key
            ] = value

    # ============================================================
    # BASIC VALIDATION
    # ============================================================

    validate_input(
        normalized
    )

    return normalized


# ================================================================
# SUBJECT NORMALIZATION
# ================================================================

def normalize_subjects(
    subjects
):
    """
    Normalize subject information.

    Supported examples:

        {
            "name": "DBMS",
            "faculty": "F1",
            "theory_periods": 3
        }

    or:

        {
            "subject_name": "DBMS",
            "faculty_id": "F1",
            "theory_hours": 3
        }
    """

    if not isinstance(
        subjects,
        list
    ):

        raise ValueError(
            "'subjects' must be a list."
        )

    result = []

    for index, subject in enumerate(
        subjects
    ):

        # --------------------------------------------------------
        # Convert string subject into object
        # --------------------------------------------------------

        if isinstance(
            subject,
            str
        ):

            subject = {
                "name": subject
            }

        if not isinstance(
            subject,
            dict
        ):

            raise ValueError(
                f"Subject at index {index} "
                f"must be an object."
            )

        item = dict(
            subject
        )

        # --------------------------------------------------------
        # Name
        # --------------------------------------------------------

        item["name"] = (
            item.get("name")
            or item.get("subject_name")
            or item.get("subjectName")
            or item.get("code")
            or f"Subject {index + 1}"
        )

        # --------------------------------------------------------
        # Faculty
        # --------------------------------------------------------

        item["faculty"] = (
            item.get("faculty")
            or item.get("faculty_id")
            or item.get("facultyId")
            or item.get("teacher")
        )

        # --------------------------------------------------------
        # Theory periods
        # --------------------------------------------------------

        item["theory_periods"] = get_int(
            item.get(
                "theory_periods",
                item.get(
                    "theory_hours",
                    item.get(
                        "theory",
                        0
                    )
                )
            )
        )

        # --------------------------------------------------------
        # Lab periods
        # --------------------------------------------------------

        item["lab_periods"] = get_int(
            item.get(
                "lab_periods",
                item.get(
                    "lab_hours",
                    item.get(
                        "lab",
                        0
                    )
                )
            )
        )

        # --------------------------------------------------------
        # Lab flag
        # --------------------------------------------------------

        item["is_lab"] = bool(
            item.get(
                "is_lab",
                False
            )
        )

        if item[
            "lab_periods"
        ] > 0:

            item[
                "is_lab"
            ] = True

        # --------------------------------------------------------
        # Preferred days
        # --------------------------------------------------------

        preferred = (
            item.get(
                "preferred_days"
            )
            or item.get(
                "preferred_day"
            )
            or []
        )

        if not isinstance(
            preferred,
            list
        ):

            preferred = [
                preferred
            ]

        item[
            "preferred_days"
        ] = preferred

        # --------------------------------------------------------
        # Required total periods
        # --------------------------------------------------------

        item[
            "required_periods"
        ] = (
            item[
                "theory_periods"
            ]
            +
            item[
                "lab_periods"
            ]
        )

        result.append(
            item
        )

    return result


# ================================================================
# NORMALIZE GENERIC LIST
# ================================================================

def normalize_list(
    value
):
    """
    Normalize batches, faculties, labs and rooms.
    """

    if value is None:
        return []

    if not isinstance(
        value,
        list
    ):

        raise ValueError(
            "Expected a list."
        )

    return value


# ================================================================
# DAYS
# ================================================================

def normalize_days(
    days
):
    """
    Default academic week:

        Monday-Friday
    """

    if days is None:

        return [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday"
        ]

    if not isinstance(
        days,
        list
    ):

        raise ValueError(
            "'days' must be a list."
        )

    if len(days) == 0:

        raise ValueError(
            "At least one day is required."
        )

    return [
        str(day).strip()
        for day in days
    ]


# ================================================================
# PERIODS
# ================================================================

def normalize_periods(
    periods
):
    """
    Supported:

        "periods": 8

    or:

        "periods": [
            "P1",
            "P2",
            ...
        ]
    """

    if periods is None:

        return [
            "P1",
            "P2",
            "P3",
            "P4",
            "P5",
            "P6",
            "P7",
            "P8"
        ]

    if isinstance(
        periods,
        int
    ):

        if periods <= 0:

            raise ValueError(
                "Number of periods must be positive."
            )

        return [
            f"P{i + 1}"
            for i in range(
                periods
            )
        ]

    if isinstance(
        periods,
        list
    ):

        if len(periods) == 0:

            raise ValueError(
                "At least one period is required."
            )

        return [
            str(period).strip()
            for period in periods
        ]

    raise ValueError(
        "'periods' must be either an integer or a list."
    )


# ================================================================
# OBJECTIVE WEIGHTS
# ================================================================

def normalize_weights(
    weights
):
    """
    Normalize soft-constraint weights.
    """

    default = {
        "distribution": 10,
        "gaps": 8,
        "workload": 6,
        "preferred_days": 5,
        "quality": 3
    }

    if not isinstance(
        weights,
        dict
    ):

        return default

    for key in default:

        if key not in weights:
            continue

        value = get_number(
            weights[key],
            default[key]
        )

        if value < 0:
            value = default[key]

        default[key] = value

    return default


# ================================================================
# INPUT VALIDATION
# ================================================================

def validate_input(
    data
):
    """
    Validate minimum information required by the solver.
    """

    if not data[
        "subjects"
    ]:

        raise ValueError(
            "At least one subject is required."
        )

    if not data[
        "batches"
    ]:

        raise ValueError(
            "At least one batch is required."
        )

    # ------------------------------------------------------------
    # Check subject period values
    # ------------------------------------------------------------

    for index, subject in enumerate(
        data["subjects"]
    ):

        if (
            subject[
                "theory_periods"
            ] < 0
        ):

            raise ValueError(
                f"Subject {index} has invalid "
                "theory_periods."
            )

        if (
            subject[
                "lab_periods"
            ] < 0
        ):

            raise ValueError(
                f"Subject {index} has invalid "
                "lab_periods."
            )

        if (
            subject[
                "required_periods"
            ] == 0
        ):

            raise ValueError(
                f"Subject '{subject['name']}' "
                "has no theory or lab periods."
            )

    # ------------------------------------------------------------
    # P1/P2 requirement
    # ------------------------------------------------------------

    if len(
        data["periods"]
    ) < 2:

        raise ValueError(
            "At least two periods are required "
            "because P1 and P2 cannot be empty."
        )

    # ------------------------------------------------------------
    # Check total workload
    # ------------------------------------------------------------

    total_periods = sum(
        subject[
            "required_periods"
        ]
        for subject
        in data["subjects"]
    )

    available_periods = (
        len(data["batches"])
        *
        len(data["days"])
        *
        len(data["periods"])
    )

    if total_periods > available_periods:

        raise ValueError(
            "Total subject workload exceeds "
            "available timetable capacity."
        )


# ================================================================
# INTEGER HELPER
# ================================================================

def get_int(
    value,
    default=0
):
    """

    Safely convert a value to integer.
    """

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default# ================================================================
# NUMBER HELPER
# ================================================================

def get_number(
    value,
    default=0
):
    """
    Safely convert a value to float.
    """

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ================================================================
# EXTRACT STAFF FROM SUBJECTS
# ================================================================

def extract_staff_from_subjects(
    subjects
):
    """
    Build a deduplicated staff list from the subjects.

    Each subject may have:
        staff
        faculty
        faculty_id
        staff_id
        teacher

    Returns a list of unique staff name strings.
    """

    seen = []

    for subject in subjects:

        if not isinstance(
            subject,
            dict
        ):
            continue

        staff_name = (
            subject.get("staff")
            or subject.get("faculty")
            or subject.get("faculty_id")
            or subject.get("staff_id")
            or subject.get("teacher")
        )

        if staff_name is None:
            continue

        staff_str = str(
            staff_name
        ).strip()

        if not staff_str:
            continue

        # Deduplicate by normalized name
        normalized = staff_str.lower()

        already_seen = False

        for existing in seen:

            if str(
                existing
            ).lower() == normalized:

                already_seen = True
                break

        if not already_seen:
            seen.append(staff_str)

    return seen