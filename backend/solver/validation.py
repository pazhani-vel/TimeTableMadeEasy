# ================================================================
# INPUT VALIDATION
# ================================================================


def validate_input(data):
    """
    Validate timetable input before sending it to the solver.

    This function checks:
        - Required fields
        - Subjects
        - Batches
        - Faculty information
        - Periods
        - Days
        - Subject workload
        - Lab requirements
        - P1/P2 availability
    """

    errors = []
    warnings = []

    # ============================================================
    # 1. BASIC INPUT
    # ============================================================

    if not isinstance(data, dict):

        return {
            "valid": False,
            "errors": [
                {
                    "field": "input",
                    "message": (
                        "Input must be a JSON object."
                    )
                }
            ],
            "warnings": []
        }

    # ============================================================
    # 2. SUBJECTS
    # ============================================================

    subjects = data.get(
        "subjects",
        []
    )

    if not isinstance(
        subjects,
        list
    ):

        errors.append({
            "field": "subjects",
            "message": (
                "'subjects' must be a list."
            )
        })

        subjects = []

    elif len(subjects) == 0:

        errors.append({
            "field": "subjects",
            "message": (
                "At least one subject is required."
            )
        })

    # ============================================================
    # 3. BATCHES
    # ============================================================

    batches = data.get(
        "batches",
        []
    )

    if not isinstance(
        batches,
        list
    ):

        errors.append({
            "field": "batches",
            "message": (
                "'batches' must be a list."
            )
        })

        batches = []

    elif len(batches) == 0:

        errors.append({
            "field": "batches",
            "message": (
                "At least one batch is required."
            )
        })

    # ============================================================
    # 4. FACULTIES
    # ============================================================

    faculties = data.get(
        "faculties",
        []
    )

    if not isinstance(
        faculties,
        list
    ):

        errors.append({
            "field": "faculties",
            "message": (
                "'faculties' must be a list."
            )
        })

        faculties = []

    # ============================================================
    # 5. DAYS
    # ============================================================

    days = data.get(
        "days",
        [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday"
        ]
    )

    if not isinstance(
        days,
        list
    ):

        errors.append({
            "field": "days",
            "message": (
                "'days' must be a list."
            )
        })

        days = []

    elif len(days) == 0:

        errors.append({
            "field": "days",
            "message": (
                "At least one day is required."
            )
        })

    # ============================================================
    # 6. PERIODS
    # ============================================================

    periods = data.get(
        "periods",
        8
    )

    # ------------------------------------------------------------
    # periods can be:
    #
    #   8
    #
    # or:
    #
    #   ["P1", "P2", ...]
    # ------------------------------------------------------------

    if isinstance(
        periods,
        int
    ):

        num_periods = periods

    elif isinstance(
        periods,
        list
    ):

        num_periods = len(
            periods
        )

    else:

        errors.append({
            "field": "periods",
            "message": (
                "'periods' must be an integer "
                "or a list."
            )
        })

        num_periods = 0

    # ============================================================
    # P1/P2 REQUIREMENT
    # ============================================================

    if num_periods < 2:

        errors.append({
            "field": "periods",
            "message": (
                "At least two periods are required "
                "because P1 and P2 cannot be empty."
            )
        })

    # ============================================================
    # 7. SUBJECT VALIDATION
    # ============================================================

    total_required_periods = 0

    for index, subject in enumerate(
        subjects
    ):

        # --------------------------------------------------------
        # Subject must be an object
        # --------------------------------------------------------

        if not isinstance(
            subject,
            dict
        ):

            errors.append({
                "field": f"subjects[{index}]",
                "message": (
                    "Subject must be an object."
                )
            })

            continue

        # --------------------------------------------------------
        # Subject name
        # --------------------------------------------------------

        subject_name = (
            subject.get("name")
            or subject.get("subject_name")
            or subject.get("subjectName")
            or subject.get("code")
        )

        if not subject_name:

            errors.append({
                "field": f"subjects[{index}].name",
                "message": (
                    "Subject name is required."
                )
            })

            subject_name = (
                f"Subject {index + 1}"
            )

        # --------------------------------------------------------
        # Theory periods
        # --------------------------------------------------------

        theory_periods = get_non_negative_int(
            subject.get(
                "theory_periods",
                subject.get(
                    "theory_hours",
                    subject.get(
                        "theory",
                        0
                    )
                )
            )
        )

        # --------------------------------------------------------
        # Lab periods
        # --------------------------------------------------------

        lab_periods = get_non_negative_int(
            subject.get(
                "lab_periods",
                subject.get(
                    "lab_hours",
                    subject.get(
                        "lab",
                        0
                    )
                )
            )
        )

        # --------------------------------------------------------
        # Check invalid values
        # --------------------------------------------------------

        raw_theory = subject.get(
            "theory_periods",
            subject.get(
                "theory_hours",
                subject.get(
                    "theory",
                    0
                )
            )
        )

        raw_lab = subject.get(
            "lab_periods",
            subject.get(
                "lab_hours",
                subject.get(
                    "lab",
                    0
                )
            )
        )

        if not is_non_negative_number(
            raw_theory
        ):

            errors.append({
                "field": (
                    f"subjects[{index}]."
                    "theory_periods"
                ),
                "message": (
                    f"Invalid theory period value "
                    f"for '{subject_name}'."
                )
            })

        if not is_non_negative_number(
            raw_lab
        ):

            errors.append({
                "field": (
                    f"subjects[{index}]."
                    "lab_periods"
                ),
                "message": (
                    f"Invalid lab period value "
                    f"for '{subject_name}'."
                )
            })

        # --------------------------------------------------------
        # At least one period
        # --------------------------------------------------------

        required = (
            theory_periods
            +
            lab_periods
        )

        if required == 0:

            errors.append({
                "field": f"subjects[{index}]",
                "message": (
                    f"Subject '{subject_name}' "
                    "must have at least one "
                    "theory or lab period."
                )
            })

        total_required_periods += required

        # --------------------------------------------------------
        # Faculty
        # --------------------------------------------------------

        faculty = (
            subject.get("faculty")
            or subject.get("faculty_id")
            or subject.get("facultyId")
            or subject.get("teacher")
            or subject.get("staff")
        )

        if not faculty:

            warnings.append({
                "field": (
                    f"subjects[{index}].faculty"
                ),
                "message": (
                    f"Subject '{subject_name}' "
                    "does not have a faculty assigned."
                )
            })

        # --------------------------------------------------------
        # Lab subject validation
        # --------------------------------------------------------

        is_lab = bool(
            subject.get(
                "is_lab",
                False
            )
        )

        subject_type = str(
            subject.get(
                "type",
                ""
            )
        ).lower()

        if subject_type in (
            "lab",
            "laboratory",
            "practical"
        ):

            is_lab = True

        if lab_periods > 0:

            is_lab = True

        if is_lab and lab_periods == 0:

            warnings.append({
                "field": (
                    f"subjects[{index}].lab_periods"
                ),
                "message": (
                    f"Subject '{subject_name}' "
                    "is marked as a lab but has "
                    "zero lab periods."
                )
            })

        # --------------------------------------------------------
        # Preferred days
        # --------------------------------------------------------

        preferred_days = subject.get(
            "preferred_days",
            subject.get(
                "preferred_day",
                []
            )
        )

        if preferred_days is not None:

            if not isinstance(
                preferred_days,
                list
            ):

                preferred_days = [
                    preferred_days
                ]

            for preferred_day in preferred_days:

                if preferred_day not in days:

                    warnings.append({
                        "field": (
                            f"subjects[{index}]."
                            "preferred_days"
                        ),
                        "message": (
                            f"Preferred day "
                            f"'{preferred_day}' "
                            f"for '{subject_name}' "
                            "is not present in "
                            "the timetable days."
                        )
                    })

    # ============================================================
    # 8. TOTAL CAPACITY
    # ============================================================

    available_capacity = (
        len(batches)
        *
        len(days)
        *
        num_periods
    )

    if (
        total_required_periods
        >
        available_capacity
    ):

        errors.append({
            "field": "subjects",
            "message": (
                "Total required subject periods "
                "exceed the available timetable "
                "capacity."
            ),
            "details": {
                "required_periods": (
                    total_required_periods
                ),
                "available_periods": (
                    available_capacity
                )
            }
        })

    # ============================================================
    # 9. DUPLICATE SUBJECT NAMES
    # ============================================================

    subject_names = []

    for subject in subjects:

        if not isinstance(
            subject,
            dict
        ):
            continue

        name = (
            subject.get("name")
            or subject.get("subject_name")
            or subject.get("subjectName")
            or subject.get("code")
        )

        if name:

            normalized_name = (
                str(name)
                .strip()
                .lower()
            )

            if normalized_name in subject_names:

                warnings.append({
                    "field": "subjects",
                    "message": (
                        f"Duplicate subject name "
                        f"'{name}' found."
                    )
                })

            else:

                subject_names.append(
                    normalized_name
                )

    # ============================================================
    # 10. DUPLICATE FACULTY ASSIGNMENTS
    # ============================================================

    faculty_names = set()

    for index, faculty in enumerate(
        faculties
    ):

        if isinstance(
            faculty,
            dict
        ):

            name = (
                faculty.get("name")
                or faculty.get("faculty_name")
                or faculty.get("id")
            )

        else:

            name = str(
                faculty
            )

        if name:

            normalized_name = (
                str(name)
                .strip()
                .lower()
            )

            if normalized_name in faculty_names:

                warnings.append({
                    "field": (
                        f"faculties[{index}]"
                    ),
                    "message": (
                        f"Duplicate faculty "
                        f"'{name}' found."
                    )
                })

            faculty_names.add(
                normalized_name
            )

    # ============================================================
    # 11. DAYS DUPLICATION
    # ============================================================

    normalized_days = [
        str(day).strip().lower()
        for day in days
    ]

    if len(
        normalized_days
    ) != len(
        set(normalized_days)
    ):

        errors.append({
            "field": "days",
            "message": (
                "Duplicate days are not allowed."
            )
        })

    # ============================================================
    # 12. PERIOD DUPLICATION
    # ============================================================

    if isinstance(
        periods,
        list
    ):

        normalized_periods = [
            str(period).strip().lower()
            for period in periods
        ]

        if len(
            normalized_periods
        ) != len(
            set(normalized_periods)
        ):

            errors.append({
                "field": "periods",
                "message": (
                    "Duplicate periods are not allowed."
                )
            })

    # ============================================================
    # FINAL RESULT
    # ============================================================

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }


# ================================================================
# INTEGER VALIDATION
# ================================================================

def get_non_negative_int(
    value
):
    """
    Convert a value to a non-negative integer.

    Invalid values become 0.
    """

    try:

        value = int(
            value
        )

        if value < 0:
            return 0

        return value

    except (
        TypeError,
        ValueError
    ):

        return 0


# ================================================================
# NUMBER VALIDATION
# ================================================================

def is_non_negative_number(
    value
):
    """
    Check whether a value represents a non-negative number.
    """

    try:

        number = float(
            value
        )

        return number >= 0

    except (
        TypeError,
        ValueError
    ):

        return False


# ================================================================
# CONVENIENCE FUNCTION
# ================================================================

def is_valid_input(
    data
):
    """
    Simple boolean version.

    Returns:

        True  -> input is valid
        False -> input has errors
    """

    result = validate_input(
        data
    )

    return result[
        "valid"
    ]