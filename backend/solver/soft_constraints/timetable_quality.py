from ortools.sat.python import cp_model


def add_timetable_quality_constraints(timetable):
    """
    Add general SOFT timetable-quality constraints.

    Goals:
        1. Avoid unnecessary use of undesirable periods.
        2. Prefer compact daily schedules.
        3. Avoid excessive first/last period usage.
        4. Encourage balanced period utilization.
        5. Avoid repeated undesirable patterns.

    These constraints must NEVER make the timetable infeasible.

    Returns:
        Dictionary containing:
            penalties
            rewards
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    theory_y = timetable.theory_y
    lab_y = timetable.lab_y

    penalties = []
    rewards = []

    # ============================================================
    # CREATE GENERAL OCCUPANCY VARIABLES
    # ============================================================

    occupancy = {}

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods):

                classes = []

                # ------------------------------------------------
                # Normal subjects
                # ------------------------------------------------

                for s in range(len(subjects)):

                    classes.append(
                        theory_y[s, b, d, p]
                    )

                    classes.append(
                        lab_y[s, b, d, p]
                    )

                # ------------------------------------------------
                # Special activities
                # ------------------------------------------------

                classes.append(
                    timetable.naan_mudalvan[b, d, p]
                )

                classes.append(
                    timetable.audit[b, d, p]
                )

                classes.append(
                    timetable.ioc[b, d, p]
                )

                used = model.NewBoolVar(
                    f"quality_occupancy"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                model.Add(
                    sum(classes) >= used
                )

                model.Add(
                    sum(classes)
                    <=
                    len(classes) * used
                )

                occupancy[
                    b, d, p
                ] = used

    # ============================================================
    # 1. AVOID UNNECESSARY FIRST-PERIOD CLASSES
    # ============================================================
    #
    # This is SOFT.
    #
    # It does NOT mean:
    #
    #     P1 must always be empty.
    #
    # It simply means that if another valid arrangement exists,
    # the solver prefers not to put a class in P1.
    #
    # ============================================================

    first_period_penalty_enabled = timetable.data.get(
        "penalize_first_period",
        True
    )

    if first_period_penalty_enabled:

        for b in range(len(batches)):

            for d in range(days):

                penalties.append(
                    occupancy[
                        b, d, 0
                    ]
                )

    # ============================================================
    # 2. AVOID UNNECESSARY LAST-PERIOD CLASSES
    # ============================================================
    #
    # Same principle as P1.
    #
    # P8 is not forbidden.
    #
    # It simply receives a soft penalty.
    #
    # ============================================================

    last_period_penalty_enabled = timetable.data.get(
        "penalize_last_period",
        True
    )

    if last_period_penalty_enabled:

        last_period = periods - 1

        for b in range(len(batches)):

            for d in range(days):

                penalties.append(
                    occupancy[
                        b,
                        d,
                        last_period
                    ]
                )

    # ============================================================
    # 3. REWARD CONSECUTIVE OCCUPIED PERIODS
    # ============================================================
    #
    # Example:
    #
    # P1 P2 P3 P4
    #
    # C  C  C  -
    #
    # is preferred over:
    #
    # C  -  C  -
    #
    # because it produces a more compact timetable.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods - 1):

                current = occupancy[
                    b, d, p
                ]

                next_period = occupancy[
                    b, d, p + 1
                ]

                consecutive = model.NewBoolVar(
                    f"quality_consecutive"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                model.Add(
                    consecutive <= current
                )

                model.Add(
                    consecutive <= next_period
                )

                model.Add(
                    consecutive >=
                    current
                    +
                    next_period
                    -
                    1
                )

                rewards.append(
                    consecutive
                )

    # ============================================================
    # 4. REWARD FULLY COMPACT DAYS
    # ============================================================
    #
    # If a day has:
    #
    #     P2 P3 P4 P5
    #
    # occupied continuously, reward it.
    #
    # We detect every possible continuous pair.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods - 1):

                left = occupancy[
                    b, d, p
                ]

                right = occupancy[
                    b, d, p + 1
                ]

                compact_pair = model.NewBoolVar(
                    f"compact_pair"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                model.Add(
                    compact_pair <= left
                )

                model.Add(
                    compact_pair <= right
                )

                model.Add(
                    compact_pair >=
                    left
                    +
                    right
                    -
                    1
                )

                rewards.append(
                    compact_pair
                )

    # ============================================================
    # 5. PENALIZE SINGLE-CLASS DAYS
    # ============================================================
    #
    # Example:
    #
    # Monday:
    #
    # P4 → DBMS
    #
    # and everything else empty.
    #
    # If the same class could be moved to another day where the
    # batch already has classes, this schedule is less desirable.
    #
    # Again, this is only a preference.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            day_workload = model.NewIntVar(
                0,
                periods,
                f"quality_day_workload"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                day_workload
                ==
                sum(
                    occupancy[
                        b, d, p
                    ]
                    for p in range(periods)
                )
            )

            single_class_day = model.NewBoolVar(
                f"single_class_day"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                day_workload
                == 1
            ).OnlyEnforceIf(
                single_class_day
            )

            model.Add(
                day_workload
                != 1
            ).OnlyEnforceIf(
                single_class_day.Not()
            )

            penalties.append(
                single_class_day
            )

    # ============================================================
    # 6. PENALIZE VERY LIGHT DAYS
    # ============================================================
    #
    # If a batch has:
    #
    # Monday    → 7
    # Tuesday   → 1
    # Wednesday → 7
    #
    # Tuesday is unnecessarily light.
    #
    # workload.py already handles overall balance.
    #
    # This provides an additional quality signal.
    #
    # ============================================================

    minimum_preferred_load = timetable.data.get(
        "preferred_min_daily_periods",
        3
    )

    try:
        minimum_preferred_load = int(
            minimum_preferred_load
        )
    except (TypeError, ValueError):
        minimum_preferred_load = 3

    minimum_preferred_load = max(
        1,
        min(
            minimum_preferred_load,
            periods
        )
    )

    for b in range(len(batches)):

        for d in range(days):

            day_workload = model.NewIntVar(
                0,
                periods,
                f"quality_load"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                day_workload
                ==
                sum(
                    occupancy[
                        b, d, p
                    ]
                    for p in range(periods)
                )
            )

            light_day_excess = model.NewIntVar(
                0,
                periods,
                f"light_day_penalty"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                light_day_excess
                >=
                minimum_preferred_load
                -
                day_workload
            )

            model.Add(
                light_day_excess
                >= 0
            )

            # Only penalize if the day actually has a class.
            has_class = model.NewBoolVar(
                f"has_class"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                day_workload >= has_class
            )

            model.Add(
                day_workload
                <=
                periods * has_class
            )

            actual_penalty = model.NewIntVar(
                0,
                periods,
                f"light_day_actual_penalty"
                f"_b{b}"
                f"_d{d}"
            )

            model.Add(
                actual_penalty
                <=
                light_day_excess
            )

            model.Add(
                actual_penalty
                <=
                periods * has_class
            )

            model.Add(
                actual_penalty
                >=
                light_day_excess
                -
                periods * (1 - has_class)
            )

            penalties.append(
                actual_penalty
            )

    # ============================================================
    # 7. REWARD PERIOD UTILIZATION
    # ============================================================
    #
    # If a batch already has classes on a day, filling nearby
    # periods is preferred over creating isolated classes.
    #
    # This works together with gaps.py.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods):

                current = occupancy[
                    b, d, p
                ]

                # ------------------------------------------------
                # Reward a class if the previous period is occupied.
                # ------------------------------------------------

                if p > 0:

                    previous = occupancy[
                        b, d, p - 1
                    ]

                    adjacent = model.NewBoolVar(
                        f"quality_adjacent"
                        f"_b{b}"
                        f"_d{d}"
                        f"_p{p}"
                    )

                    model.Add(
                        adjacent <= current
                    )

                    model.Add(
                        adjacent <= previous
                    )

                    model.Add(
                        adjacent >=
                        current
                        +
                        previous
                        -
                        1
                    )

                    rewards.append(
                        adjacent
                    )

    # ============================================================
    # 8. SUBJECT-SPECIFIC PERIOD PREFERENCE
    # ============================================================
    #
    # A subject may optionally specify:
    #
    #     preferred_periods: [2, 3]
    #
    # Meaning:
    #
    #     Prefer P2/P3.
    #
    # This is optional.
    #
    # ============================================================

    for s, subject in enumerate(subjects):

        preferred_periods = get_preferred_periods(
            subject,
            periods
        )

        if not preferred_periods:
            continue

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods):

                    if p in preferred_periods:
                        continue

                    subject_used = model.NewBoolVar(
                        f"preferred_period_penalty"
                        f"_s{s}"
                        f"_b{b}"
                        f"_d{d}"
                        f"_p{p}"
                    )

                    model.Add(
                        subject_used
                        >=
                        theory_y[
                            s, b, d, p
                        ]
                    )

                    model.Add(
                        subject_used
                        >=
                        lab_y[
                            s, b, d, p
                        ]
                    )

                    model.Add(
                        subject_used
                        <=
                        theory_y[
                            s, b, d, p
                        ]
                        +
                        lab_y[
                            s, b, d, p
                        ]
                    )

                    penalties.append(
                        subject_used
                    )

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "penalties": penalties,
        "rewards": rewards
    }


# ================================================================
# HELPER
# ================================================================

def get_preferred_periods(subject, periods):
    """
    Read optional preferred periods.

    Supported format:

        {
            "preferred_periods": [2, 3, 4]
        }

    Period numbers are assumed to be 1-based:

        P1 -> 1
        P2 -> 2
        P3 -> 3
        ...

    Internally they are converted to 0-based indexes.
    """

    if not isinstance(subject, dict):
        return set()

    value = subject.get(
        "preferred_periods"
    )

    if value is None:
        return set()

    if not isinstance(value, list):
        value = [value]

    result = set()

    for period in value:

        try:
            period_number = int(period)

        except (TypeError, ValueError):
            continue

        # Convert P1 -> index 0
        index = period_number - 1

        if 0 <= index < periods:
            result.add(index)

    return result