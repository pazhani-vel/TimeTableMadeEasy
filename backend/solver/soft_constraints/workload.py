from ortools.sat.python import cp_model
from soft_constraints.batch_scope import get_target_batches


def add_workload_constraints(timetable):
    """
    Add SOFT workload-balancing constraints.

    Goals:
        1. Avoid excessively heavy days for a batch.
        2. Encourage workload to be distributed across days.
        3. Avoid large differences between the busiest and
           lightest working days.

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

    penalties = []

    # ============================================================
    # CONFIGURATION
    # ============================================================

    # Maximum number of classes we would ideally like a batch
    # to have on one day.
    #
    # This is SOFT, not HARD.
    #
    # Example:
    #
    # daily_target = 6
    #
    # If a batch gets 8 classes on one day:
    #
    #     excess = 2
    #
    # and a penalty is added.
    #

    daily_target = timetable.data.get(
        "preferred_daily_periods",
        6
    )

    try:
        daily_target = int(daily_target)
    except (TypeError, ValueError):
        daily_target = 6

    daily_target = max(
        1,
        min(daily_target, periods)
    )

    # ============================================================
    # 1. DAILY WORKLOAD
    # ============================================================
    #
    # Calculate:
    #
    #     number of actual teaching periods
    #
    # for every batch/day.
    #
    # Labs count as two occupied periods because lab_y contains
    # both periods of the laboratory.
    #
    # ============================================================

    daily_workload = {}

    for b in range(len(batches)):

        for d in range(days):

            workload = model.NewIntVar(
                0,
                periods,
                f"workload_b{b}_d{d}"
            )

            class_vars = []

            for s in range(len(subjects)):

                for p in range(periods):

                    class_vars.append(
                        theory_y[s, b, d, p]
                    )

                    class_vars.append(
                        lab_y[s, b, d, p]
                    )

            # ----------------------------------------------------
            # Because batch.py already guarantees that a batch
            # cannot have two classes in the same period, we can
            # safely calculate workload using the actual occupied
            # timetable periods.
            #
            # Duplicates between theory/lab cannot occur.
            # ----------------------------------------------------

            model.Add(
                workload
                ==
                sum(
                    theory_y[s, b, d, p]
                    +
                    lab_y[s, b, d, p]
                    for s in range(len(subjects))
                    for p in range(periods)
                )
            )

            daily_workload[
                b, d
            ] = workload

    # ============================================================
    # 2. PENALIZE EXCESSIVE DAILY WORKLOAD
    # ============================================================
    #
    # If:
    #
    #     target = 6
    #
    # and:
    #
    #     workload = 8
    #
    # then:
    #
    #     excess = 2
    #
    # The solver tries to minimize this.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            excess = model.NewIntVar(
                0,
                periods,
                f"workload_excess_b{b}_d{d}"
            )

            model.Add(
                excess
                >=
                daily_workload[b, d]
                -
                daily_target
            )

            model.Add(
                excess >= 0
            )

            penalties.append(
                excess
            )

    # ============================================================
    # 3. BALANCE WORKLOAD BETWEEN DAYS
    # ============================================================
    #
    # We want:
    #
    #     busiest day ≈ lightest day
    #
    # rather than:
    #
    #     Monday    = 8
    #     Tuesday   = 2
    #     Wednesday = 8
    #     Thursday  = 2
    #
    # This is SOFT.
    #
    # ============================================================

    for b in range(len(batches)):

        max_workload = model.NewIntVar(
            0,
            periods,
            f"max_workload_b{b}"
        )

        min_workload = model.NewIntVar(
            0,
            periods,
            f"min_workload_b{b}"
        )

        # --------------------------------------------------------
        # max_workload >= every day's workload
        # --------------------------------------------------------

        for d in range(days):

            model.Add(
                max_workload
                >=
                daily_workload[b, d]
            )

        # --------------------------------------------------------
        # min_workload <= every day's workload
        # --------------------------------------------------------

        for d in range(days):

            model.Add(
                min_workload
                <=
                daily_workload[b, d]
            )

        # --------------------------------------------------------
        # Difference between busiest and lightest day.
        # --------------------------------------------------------

        workload_difference = model.NewIntVar(
            0,
            periods,
            f"workload_difference_b{b}"
        )

        model.Add(
            workload_difference
            ==
            max_workload
            -
            min_workload
        )

        penalties.append(
            workload_difference
        )

    # ============================================================
    # 4. ENCOURAGE SUBJECT DISTRIBUTION
    # ============================================================
    #
    # This is particularly important for your requirement:
    #
    # If a subject has N periods assigned during the week,
    # don't unnecessarily put all of them on one day.
    #
    # Example:
    #
    # Subject = DBMS
    # Required = 4 periods
    #
    # Better:
    #
    # Monday    → 2
    # Wednesday → 2
    #
    # Worse:
    #
    # Monday    → 4
    #
    # This is a SOFT preference.
    #
    # NOTE:
    #
    # The separate distribution.py file will handle the stronger
    # "continuous and distributed in the same day" requirement
    # that you specifically requested.
    #
    # ============================================================

    for s, subject in enumerate(subjects):

        total_required = get_total_subject_periods(
            subject
        )

        if total_required <= 1:
            continue

        target_batches = get_target_batches(subject, batches)

        for b in target_batches:

            # ----------------------------------------------------
            # Number of days on which this subject occurs.
            # ----------------------------------------------------

            subject_days = []

            for d in range(days):

                subject_day_used = model.NewBoolVar(
                    f"subject_day_used"
                    f"_s{s}"
                    f"_b{b}"
                    f"_d{d}"
                )

                day_classes = []

                for p in range(periods):

                    day_classes.append(
                        theory_y[s, b, d, p]
                    )

                    day_classes.append(
                        lab_y[s, b, d, p]
                    )

                model.Add(
                    sum(day_classes)
                    >=
                    subject_day_used
                )

                model.Add(
                    sum(day_classes)
                    <=
                    len(day_classes)
                    *
                    subject_day_used
                )

                subject_days.append(
                    subject_day_used
                )

            # ----------------------------------------------------
            # If a subject has several periods, encourage it to
            # use more than one day.
            #
            # We don't force a particular number of days because
            # that depends on the subject's required periods and
            # the other hard constraints.
            # ----------------------------------------------------

            if total_required >= 4:

                all_on_one_day = model.NewBoolVar(
                    f"subject_all_one_day"
                    f"_s{s}"
                    f"_b{b}"
                )

                # all_on_one_day = 1 means exactly one day is used.
                #
                # If only one day is used, sum(subject_days) = 1.
                #
                # If multiple days are used, it becomes 0.

                model.Add(
                    sum(subject_days)
                    <=
                    1
                    +
                    len(subject_days)
                    *
                    (
                        1
                        -
                        all_on_one_day
                    )
                )

                model.Add(
                    sum(subject_days)
                    >=
                    1
                )

                # The expression above permits all_on_one_day = 0
                # even when only one day is used, so add the reverse
                # implication using a helper variable.

                exactly_one_day = model.NewBoolVar(
                    f"subject_exactly_one_day"
                    f"_s{s}"
                    f"_b{b}"
                )

                model.Add(
                    sum(subject_days)
                    == 1
                ).OnlyEnforceIf(
                    exactly_one_day
                )

                model.Add(
                    sum(subject_days)
                    >= 2
                ).OnlyEnforceIf(
                    exactly_one_day.Not()
                )

                penalties.append(
                    exactly_one_day
                )

    # ============================================================
    # RETURN ALL WORKLOAD PENALTIES
    # ============================================================

    return penalties


# ================================================================
# SUBJECT PERIOD CALCULATION
# ================================================================

def get_total_subject_periods(subject):
    """
    Estimate the total number of timetable periods required
    by a subject.

    Supported fields:

        theory_hours
        theory_periods
        periods
        lab_hours
        lab_periods
        lab

    Lab hours are treated as actual occupied periods.

    Example:

        theory_hours = 3
        lab_hours = 4

    Total = 7 periods.
    """

    if not isinstance(subject, dict):
        return 0

    theory = (
        subject.get("theory_hours")
        if subject.get("theory_hours") is not None
        else subject.get("theory_periods")
    )

    if theory is None:
        theory = subject.get(
            "periods",
            0
        )

    lab = (
        subject.get("lab_hours")
        if subject.get("lab_hours") is not None
        else subject.get("lab_periods")
    )

    if lab is None:
        lab = subject.get(
            "lab",
            0
        )

    try:
        theory = int(theory)
    except (TypeError, ValueError):
        theory = 0

    try:
        lab = int(lab)
    except (TypeError, ValueError):
        lab = 0

    return theory + lab