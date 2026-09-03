from ortools.sat.python import cp_model


def add_resource_constraints(timetable):
    """
    Add HARD constraints related to laboratories and physical resources.

    Constraints:
        1. No physical lab clash.
        2. A lab subject can only use a compatible lab.
        3. Required lab resources must exist.
        4. One physical lab is assigned to a lab session.
        5. Department/resource restrictions are respected.
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches
    labs = timetable.labs

    days = timetable.num_days
    periods = timetable.num_periods

    lab_start = timetable.lab_start
    lab_y = timetable.lab_y

    # ============================================================
    # NO LABS AVAILABLE
    # ============================================================

    lab_subjects_exist = any(
        get_lab_hours(subject) > 0
        for subject in subjects
    )

    if lab_subjects_exist and len(labs) == 0:
        raise ValueError(
            "Lab sessions are required, but no physical laboratories "
            "are available."
        )

    # ============================================================
    # CREATE PHYSICAL LAB ASSIGNMENT VARIABLES
    # ============================================================
    #
    # lab_assignment[s,b,d,p,l]
    #
    # 1 → subject s / batch b / day d / starting period p
    #     uses physical lab l.
    #
    # Only the START period is used here.
    #
    # A lab session occupying:
    #
    #     P3 + P4
    #
    # is represented by:
    #
    #     lab_assignment[s,b,d,P3,l] = 1
    #
    # ============================================================

    timetable.lab_assignment = {}

    for s, subject in enumerate(subjects):

        if get_lab_hours(subject) <= 0:
            continue

        compatible_labs = get_compatible_labs(
            subject,
            labs
        )

        # --------------------------------------------------------
        # If this subject requires a lab but no compatible lab
        # exists, the timetable is impossible.
        # --------------------------------------------------------

        if len(compatible_labs) == 0:
            raise ValueError(
                f"No compatible laboratory found for subject: "
                f"{subject_name(subject, s)}"
            )

        for b, batch in enumerate(batches):

            for d in range(days):

                for p in range(periods):

                    # ------------------------------------------------
                    # Last period cannot be a lab start because a
                    # lab occupies two periods.
                    # ------------------------------------------------

                    if p == periods - 1:
                        continue

                    for l in compatible_labs:

                        timetable.lab_assignment[
                            s, b, d, p, l
                        ] = model.NewBoolVar(
                            f"lab_assign_s{s}_b{b}_d{d}_p{p}_l{l}"
                        )

    # ============================================================
    # 1. EVERY LAB SESSION MUST HAVE EXACTLY ONE PHYSICAL LAB
    # ============================================================

    for s, subject in enumerate(subjects):

        if get_lab_hours(subject) <= 0:
            continue

        compatible_labs = get_compatible_labs(
            subject,
            labs
        )

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods - 1):

                    assignments = []

                    for l in compatible_labs:

                        key = (
                            s,
                            b,
                            d,
                            p,
                            l
                        )

                        if key in timetable.lab_assignment:
                            assignments.append(
                                timetable.lab_assignment[key]
                            )

                    # ------------------------------------------------
                    # lab_start = 1
                    #     → exactly one physical lab
                    #
                    # lab_start = 0
                    #     → no physical lab assigned
                    # ------------------------------------------------

                    model.Add(
                        sum(assignments)
                        ==
                        lab_start[s, b, d, p]
                    )

    # ============================================================
    # 2. NO PHYSICAL LAB CLASH
    # ============================================================
    #
    # A physical laboratory cannot be used by two batches at
    # the same time.
    #
    # Example:
    #
    # Monday P3:
    #
    #     Batch A → IT Lab 1
    #     Batch B → IT Lab 1
    #
    # INVALID.
    #
    # ============================================================

    for l in range(len(labs)):

        for d in range(days):

            for p in range(periods):

                lab_usage = []

                # A lab session starting at P occupies P and P+1.
                #
                # Therefore, at period P we need to check:
                #
                #     sessions starting at P
                #     sessions starting at P-1
                #

                for s, subject in enumerate(subjects):

                    if get_lab_hours(subject) <= 0:
                        continue

                    for b in range(len(batches)):

                        # --------------------------------------------
                        # Session starts at current period.
                        # --------------------------------------------

                        current_key = (
                            s,
                            b,
                            d,
                            p,
                            l
                        )

                        if current_key in timetable.lab_assignment:
                            lab_usage.append(
                                timetable.lab_assignment[
                                    current_key
                                ]
                            )

                        # --------------------------------------------
                        # Session started at previous period.
                        # --------------------------------------------

                        if p > 0:

                            previous_key = (
                                s,
                                b,
                                d,
                                p - 1,
                                l
                            )

                            if previous_key in timetable.lab_assignment:
                                lab_usage.append(
                                    timetable.lab_assignment[
                                        previous_key
                                    ]
                                )

                # ----------------------------------------------------
                # Physical lab can be used by at most one batch.
                # ----------------------------------------------------

                model.Add(
                    sum(lab_usage) <= 1
                )

    # ============================================================
    # 3. DEPARTMENT / LAB COMPATIBILITY
    # ============================================================
    #
    # Compatibility is already enforced by only creating
    # lab_assignment variables for compatible laboratories.
    #
    # For additional explicit restrictions, the subject may
    # specify:
    #
    #     department
    #
    # and labs may specify:
    #
    #     department
    #
    # Example:
    #
    #     IT subject → IT lab
    #     AIDS subject → AIDS lab
    #
    # ============================================================

    for s, subject in enumerate(subjects):

        if get_lab_hours(subject) <= 0:
            continue

        subject_department = get_subject_department(
            subject
        )

        if subject_department is None:
            continue

        compatible_labs = get_compatible_labs(
            subject,
            labs
        )

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods - 1):

                    for l in range(len(labs)):

                        lab_department = get_lab_department(
                            labs[l]
                        )

                        if (
                            lab_department is not None
                            and
                            normalize(
                                lab_department
                            )
                            !=
                            normalize(
                                subject_department
                            )
                        ):

                            key = (
                                s,
                                b,
                                d,
                                p,
                                l
                            )

                            if key in timetable.lab_assignment:

                                model.Add(
                                    timetable.lab_assignment[
                                        key
                                    ] == 0
                                )

    # ============================================================
    # 4. REQUIRED LAB TYPE / RESOURCE
    # ============================================================
    #
    # If a subject specifies:
    #
    #     required_lab_type
    #
    # or:
    #
    #     lab_type
    #
    # only labs with that type can be used.
    #
    # ============================================================

    for s, subject in enumerate(subjects):

        if get_lab_hours(subject) <= 0:
            continue

        required_type = get_required_lab_type(
            subject
        )

        if required_type is None:
            continue

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods - 1):

                    for l in range(len(labs)):

                        lab_type = get_lab_type(
                            labs[l]
                        )

                        if lab_type is None:
                            continue

                        if (
                            normalize(lab_type)
                            !=
                            normalize(required_type)
                        ):

                            key = (
                                s,
                                b,
                                d,
                                p,
                                l
                            )

                            if key in timetable.lab_assignment:

                                model.Add(
                                    timetable.lab_assignment[
                                        key
                                    ] == 0
                                )

    return model


# ================================================================
# LAB HOURS
# ================================================================

def get_lab_hours(subject):
    """
    Get required laboratory hours for a subject.

    Supported fields:

        lab_hours
        lab
    """

    if not isinstance(subject, dict):
        return 0

    value = subject.get(
        "lab_hours",
        subject.get("lab", 0)
    )

    try:
        return int(value)

    except (TypeError, ValueError):
        return 0


# ================================================================
# COMPATIBLE LABS
# ================================================================

def get_compatible_labs(subject, labs):
    """
    Return indexes of laboratories compatible with a subject.

    Supported subject fields:

        lab_id
        required_lab
        lab_type
        required_lab_type
        lab_department
        department

    If the subject does not specify a particular requirement,
    all laboratories are initially considered compatible.
    """

    if not isinstance(subject, dict):
        return list(range(len(labs)))

    required_lab = subject.get(
        "lab_id"
    )

    if required_lab is None:
        required_lab = subject.get(
            "required_lab"
        )

    required_type = subject.get(
        "required_lab_type"
    )

    if required_type is None:
        required_type = subject.get(
            "lab_type"
        )

    department = get_subject_department(
        subject
    )

    compatible = []

    for index, lab in enumerate(labs):

        # --------------------------------------------------------
        # Specific physical lab requirement
        # --------------------------------------------------------

        if required_lab is not None:

            lab_id = get_lab_id(lab)

            if (
                lab_id is not None
                and
                str(lab_id)
                !=
                str(required_lab)
            ):
                continue

        # --------------------------------------------------------
        # Lab type requirement
        # --------------------------------------------------------

        if required_type is not None:

            lab_type = get_lab_type(lab)

            if lab_type is None:
                continue

            if (
                normalize(lab_type)
                !=
                normalize(required_type)
            ):
                continue

        # --------------------------------------------------------
        # Department requirement
        # --------------------------------------------------------

        if department is not None:

            lab_department = get_lab_department(
                lab
            )

            if lab_department is not None:

                if (
                    normalize(lab_department)
                    !=
                    normalize(department)
                ):
                    continue

        compatible.append(index)

    return compatible


# ================================================================
# SUBJECT INFORMATION
# ================================================================

def get_subject_department(subject):

    if not isinstance(subject, dict):
        return None

    return (
        subject.get("department")
        or subject.get("dept")
        or subject.get("branch")
    )


def get_required_lab_type(subject):

    if not isinstance(subject, dict):
        return None

    return (
        subject.get("required_lab_type")
        or subject.get("lab_type")
    )


# ================================================================
# LAB INFORMATION
# ================================================================

def get_lab_id(lab):

    if not isinstance(lab, dict):
        return lab

    return (
        lab.get("id")
        or lab.get("_id")
        or lab.get("lab_id")
        or lab.get("name")
    )


def get_lab_type(lab):

    if not isinstance(lab, dict):
        return None

    return (
        lab.get("type")
        or lab.get("lab_type")
        or lab.get("category")
    )


def get_lab_department(lab):

    if not isinstance(lab, dict):
        return None

    return (
        lab.get("department")
        or lab.get("dept")
        or lab.get("branch")
    )


# ================================================================
# SUBJECT NAME
# ================================================================

def subject_name(subject, index):

    if isinstance(subject, dict):

        return (
            subject.get("name")
            or subject.get("subject_name")
            or subject.get("code")
            or f"subject_{index}"
        )

    return str(subject)


# ================================================================
# NORMALIZE
# ================================================================

def normalize(value):

    return str(value).strip().lower()