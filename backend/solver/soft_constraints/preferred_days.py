from ortools.sat.python import cp_model


def add_preferred_day_constraints(timetable):
    """
    Add SOFT constraints for preferred days.

    A subject can have:

        preferred_days: ["Monday", "Wednesday"]

    The solver will TRY to schedule the subject on those days.

    If it cannot, the timetable is still valid.

    Instead, a penalty is added to the objective.

    Returns:
        List of penalty variables.
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    theory_y = timetable.theory_y
    lab_y = timetable.lab_y

    day_index = build_day_index(timetable)

    penalties = []

    # ============================================================
    # PROCESS EACH SUBJECT
    # ============================================================

    for s, subject in enumerate(subjects):

        preferred_days = get_preferred_days(
            subject,
            day_index
        )

        # No preference specified.
        if not preferred_days:
            continue

        # ========================================================
        # FOR EACH BATCH
        # ========================================================

        for b in range(len(batches)):

            # ----------------------------------------------------
            # Determine whether the subject is scheduled on each
            # day.
            # ----------------------------------------------------

            day_used = []

            for d in range(days):

                classes_on_day = []

                for p in range(periods):

                    classes_on_day.append(
                        theory_y[s, b, d, p]
                    )

                    classes_on_day.append(
                        lab_y[s, b, d, p]
                    )

                used = model.NewBoolVar(
                    f"preferred_subject_{s}"
                    f"_batch_{b}"
                    f"_day_{d}"
                )

                # If used = 1, at least one class exists.
                model.Add(
                    sum(classes_on_day) >= used
                )

                # If used = 0, no class exists.
                model.Add(
                    sum(classes_on_day)
                    <= len(classes_on_day) * used
                )

                day_used.append(used)

            # ====================================================
            # PENALIZE NON-PREFERRED DAYS
            # ====================================================

            for d in range(days):

                # If this day is preferred:
                #
                #     no penalty.
                #
                # If this day is NOT preferred:
                #
                #     scheduling the subject here creates a
                #     penalty.
                #

                if d in preferred_days:
                    continue

                penalty = model.NewBoolVar(
                    f"preferred_day_penalty"
                    f"_s{s}"
                    f"_b{b}"
                    f"_d{d}"
                )

                # penalty = day_used
                model.Add(
                    penalty == day_used[d]
                )

                penalties.append(
                    penalty
                )

    return penalties


# ================================================================
# READ PREFERRED DAYS
# ================================================================

def get_preferred_days(subject, day_index):
    """
    Read preferred days from a subject.

    Expected format:

        {
            "name": "DBMS",
            "preferred_days": [
                "Monday",
                "Wednesday"
            ]
        }

    Also accepts:

        "preferred_day": "Monday"

    If no preference is provided, an empty set is returned.
    """

    if not isinstance(subject, dict):
        return set()

    value = subject.get(
        "preferred_days"
    )

    if value is None:

        value = subject.get(
            "preferred_day"
        )

    if value is None:
        return set()

    if not isinstance(value, list):
        value = [value]

    result = set()

    for day in value:

        resolved = resolve_day(
            day,
            day_index
        )

        if resolved is not None:
            result.add(resolved)

    return result


# ================================================================
# DAY HELPERS
# ================================================================

def build_day_index(timetable):
    """
    Create a mapping such as:

        Monday    -> 0
        Tuesday   -> 1
        Wednesday -> 2
        ...

    based on timetable.days.
    """

    result = {}

    for index, day in enumerate(
        timetable.days
    ):

        result[
            normalize_day(day)
        ] = index

    return result


def resolve_day(day, day_index):
    """
    Convert a day name or numeric index to the
    solver's day index.
    """

    if isinstance(day, int):

        if 0 <= day < len(day_index):
            return day

        return None

    return day_index.get(
        normalize_day(day)
    )


def normalize_day(day):
    return str(day).strip().lower()