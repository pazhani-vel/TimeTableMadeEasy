from ortools.sat.python import cp_model


def add_gap_constraints(timetable):
    """
    Add SOFT constraints related to timetable gaps.

    Goals:
        1. Reduce unnecessary gaps between classes.
        2. Avoid isolated classes surrounded by empty periods.
        3. Avoid large gaps between the first and last class.
        4. Do NOT penalize the periods before the first class or
           after the last class.

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
    # CREATE OCCUPANCY VARIABLES
    # ============================================================
    #
    # occupancy[b,d,p] = 1
    #
    # if batch b has ANY real class at day d / period p.
    #
    # This includes:
    #
    #     Theory
    #     Lab
    #     Naan Mudalvan
    #     Audit
    #     IOC
    #
    # ============================================================

    occupancy = {}

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods):

                classes = []

                # ------------------------------------------------
                # Theory + Lab
                # ------------------------------------------------

                for s in range(len(subjects)):

                    classes.append(
                        theory_y[s, b, d, p]
                    )

                    classes.append(
                        lab_y[s, b, d, p]
                    )

                # ------------------------------------------------
                # Special classes
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
                    f"occupancy_b{b}_d{d}_p{p}"
                )

                # At least one class -> occupied.
                model.Add(
                    sum(classes) >= used
                )

                # No class -> not occupied.
                model.Add(
                    sum(classes)
                    <=
                    len(classes) * used
                )

                occupancy[
                    b, d, p
                ] = used

    # ============================================================
    # 1. PENALIZE INTERNAL EMPTY PERIODS
    # ============================================================
    #
    # Example:
    #
    # P1  P2  P3  P4  P5
    # C   C   -   C   C
    #
    # P3 is an INTERNAL GAP.
    #
    # This should receive a penalty.
    #
    # But:
    #
    # - P1 P2 C C C
    #
    # has no internal gap.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(1, periods - 1):

                before = occupancy[
                    b, d, p - 1
                ]

                current = occupancy[
                    b, d, p
                ]

                after = occupancy[
                    b, d, p + 1
                ]

                # ------------------------------------------------
                # gap = 1 when:
                #
                # before = 1
                # current = 0
                # after = 1
                #
                # ------------------------------------------------

                gap = model.NewBoolVar(
                    f"internal_gap"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                model.Add(
                    gap <= before
                )

                model.Add(
                    gap <= after
                )

                model.Add(
                    gap <= 1 - current
                )

                model.Add(
                    gap >=
                    before
                    +
                    after
                    -
                    current
                    -
                    1
                )

                penalties.append(gap)

    # ============================================================
    # 2. PENALIZE LONG INTERNAL GAPS
    # ============================================================
    #
    # Example:
    #
    # P1  P2  P3  P4  P5  P6
    # C   C   -   -   C   C
    #
    # This has two consecutive internal empty periods.
    #
    # The first rule detects P3 and P4 individually.
    #
    # We additionally give a stronger penalty to long gaps.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for start in range(periods):

                for length in range(2, periods - start):

                    end = start + length - 1

                    # Need occupied periods immediately before
                    # and immediately after the empty block.

                    before = start - 1
                    after = end + 1

                    if before < 0:
                        continue

                    if after >= periods:
                        continue

                    gap_vars = []

                    for p in range(
                        start,
                        end + 1
                    ):

                        gap_vars.append(
                            occupancy[
                                b,
                                d,
                                p
                            ]
                        )

                    long_gap = model.NewBoolVar(
                        f"long_gap"
                        f"_b{b}"
                        f"_d{d}"
                        f"_start{start}"
                        f"_length{length}"
                    )

                    # ------------------------------------------------
                    # Both sides must contain a class.
                    # ------------------------------------------------

                    model.Add(
                        long_gap
                        <=
                        occupancy[
                            b,
                            d,
                            before
                        ]
                    )

                    model.Add(
                        long_gap
                        <=
                        occupancy[
                            b,
                            d,
                            after
                        ]
                    )

                    # Every period inside the gap must be empty.
                    for gap_var in gap_vars:

                        model.Add(
                            long_gap
                            <=
                            1 - gap_var
                        )

                    # ------------------------------------------------
                    # If all conditions hold, long_gap can be 1.
                    # ------------------------------------------------

                    model.Add(
                        long_gap
                        >=
                        occupancy[
                            b,
                            d,
                            before
                        ]
                        +
                        occupancy[
                            b,
                            d,
                            after
                        ]
                        +
                        sum(
                            1 - v
                            for v in gap_vars
                        )
                        -
                        (length + 1)
                    )

                    # Give longer gaps a larger penalty.
                    #
                    # length 2 -> penalty 2
                    # length 3 -> penalty 3
                    # etc.
                    #
                    for _ in range(length):

                        penalties.append(
                            long_gap
                        )

    # ============================================================
    # 3. PENALIZE ISOLATED CLASSES
    # ============================================================
    #
    # Example:
    #
    # P1  P2  P3  P4
    # C   -   C   -
    #
    # P1 and P3 are separated.
    #
    # This is already partly captured by internal gaps.
    #
    # Here we additionally identify an isolated class:
    #
    #     - C -
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(1, periods - 1):

                left = occupancy[
                    b, d, p - 1
                ]

                current = occupancy[
                    b, d, p
                ]

                right = occupancy[
                    b, d, p + 1
                ]

                isolated = model.NewBoolVar(
                    f"isolated_class"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                model.Add(
                    isolated <= current
                )

                model.Add(
                    isolated <= 1 - left
                )

                model.Add(
                    isolated <= 1 - right
                )

                model.Add(
                    isolated
                    >=
                    current
                    -
                    left
                    -
                    right
                )

                penalties.append(
                    isolated
                )

    # ============================================================
    # 4. PENALIZE LONG SPAN
    # ============================================================
    #
    # We don't want:
    #
    # P1 = Class
    # P2 = empty
    # P3 = empty
    # P4 = empty
    # P5 = Class
    #
    # if a compact schedule is possible.
    #
    # But we DO NOT penalize periods after the last class or
    # before the first class.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            # ----------------------------------------------------
            # first_used[p]
            #
            # Indicates that Pp is the first class of the day.
            # ----------------------------------------------------

            first_used = []

            for p in range(periods):

                first = model.NewBoolVar(
                    f"first_class"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                first_used.append(first)

                # If first = 1, current period must be occupied.
                model.Add(
                    first <= occupancy[
                        b, d, p
                    ]
                )

                # All previous periods must be empty.
                for q in range(p):

                    model.Add(
                        first
                        <=
                        1 - occupancy[
                            b, d, q
                        ]
                    )

            # At most one first class.
            model.Add(
                sum(first_used) <= 1
            )

            # ----------------------------------------------------
            # last_used[p]
            # ----------------------------------------------------

            last_used = []

            for p in range(periods):

                last = model.NewBoolVar(
                    f"last_class"
                    f"_b{b}"
                    f"_d{d}"
                    f"_p{p}"
                )

                last_used.append(last)

                model.Add(
                    last <= occupancy[
                        b, d, p
                    ]
                )

                # All following periods must be empty.
                for q in range(p + 1, periods):

                    model.Add(
                        last
                        <=
                        1 - occupancy[
                            b, d, q
                        ]
                    )

            # At most one last class.
            model.Add(
                sum(last_used) <= 1
            )

            # ----------------------------------------------------
            # Penalize distance between first and last class.
            #
            # We use pair variables:
            #
            # first[p] AND last[q]
            #
            # and penalize the span.
            # ----------------------------------------------------

            for first_p in range(periods):

                for last_p in range(
                    first_p + 1,
                    periods
                ):

                    span = model.NewBoolVar(
                        f"daily_span"
                        f"_b{b}"
                        f"_d{d}"
                        f"_first{first_p}"
                        f"_last{last_p}"
                    )

                    model.Add(
                        span
                        <=
                        first_used[first_p]
                    )

                    model.Add(
                        span
                        <=
                        last_used[last_p]
                    )

                    model.Add(
                        span
                        >=
                        first_used[first_p]
                        +
                        last_used[last_p]
                        -
                        1
                    )

                    # Penalize larger spans more heavily.
                    span_length = last_p - first_p

                    for _ in range(
                        span_length
                    ):
                        penalties.append(
                            span
                        )

    return penalties