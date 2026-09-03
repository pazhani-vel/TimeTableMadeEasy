from ortools.sat.python import cp_model


def add_distribution_constraints(timetable):
    """
    Add SOFT constraints for subject period distribution.

    Main goal:

        If a subject has N periods on a particular day,
        those periods should preferably be consecutive.

    Example:

        DBMS DBMS DBMS
        -> good

    instead of:

        DBMS FREE DBMS FREE DBMS
        -> bad

    The solver receives a penalty for splitting a subject into
    multiple blocks.

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
    # 1. SUBJECT OCCUPANCY
    # ============================================================
    #
    # subject_used[s,b,d,p] = 1
    #
    # if subject s is scheduled for batch b on day d / period p.
    #
    # ============================================================

    subject_used = {}

    for s in range(len(subjects)):

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods):

                    used = model.NewBoolVar(
                        f"subject_used"
                        f"_s{s}"
                        f"_b{b}"
                        f"_d{d}"
                        f"_p{p}"
                    )

                    model.Add(
                        used >= theory_y[
                            s, b, d, p
                        ]
                    )

                    model.Add(
                        used >= lab_y[
                            s, b, d, p
                        ]
                    )

                    model.Add(
                        used <=
                        theory_y[
                            s, b, d, p
                        ]
                        +
                        lab_y[
                            s, b, d, p
                        ]
                    )

                    subject_used[
                        s, b, d, p
                    ] = used

    # ============================================================
    # 2. DETECT START OF A SUBJECT BLOCK
    # ============================================================
    #
    # Example:
    #
    # P1 DBMS
    # P2 DBMS
    # P3 OS
    # P4 DBMS
    #
    # DBMS has two blocks:
    #
    #     P1-P2
    #     P4
    #
    # We penalize the second block.
    #
    # ============================================================

    for s in range(len(subjects)):

        for b in range(len(batches)):

            for d in range(days):

                block_starts = []

                for p in range(periods):

                    current = subject_used[
                        s, b, d, p
                    ]

                    # ------------------------------------------------
                    # P1 is automatically a possible block start.
                    # ------------------------------------------------

                    if p == 0:

                        block_start = model.NewBoolVar(
                            f"subject_block_start"
                            f"_s{s}"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )

                        model.Add(
                            block_start == current
                        )

                        block_starts.append(
                            block_start
                        )

                    else:

                        previous = subject_used[
                            s, b, d, p - 1
                        ]

                        block_start = model.NewBoolVar(
                            f"subject_block_start"
                            f"_s{s}"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )

                        # block_start = current AND NOT previous

                        model.Add(
                            block_start <= current
                        )

                        model.Add(
                            block_start <= 1 - previous
                        )

                        model.Add(
                            block_start >=
                            current
                            -
                            previous
                        )

                        block_starts.append(
                            block_start
                        )

                # ----------------------------------------------------
                # If the subject occurs on a day, the first block
                # is free.
                #
                # Every additional block receives a penalty.
                # ----------------------------------------------------

                first_block = model.NewBoolVar(
                    f"first_subject_block"
                    f"_s{s}"
                    f"_b{b}"
                    f"_d{d}"
                )

                # first_block = 1 if at least one block exists
                model.Add(
                    first_block <= sum(block_starts)
                )

                for block_start in block_starts:
                    model.Add(
                        first_block >= block_start
                    )

                # ----------------------------------------------------
                # Instead of penalizing the first block, penalize:
                #
                #     number_of_blocks - 1
                #
                # ----------------------------------------------------

                extra_blocks = model.NewIntVar(
                    0,
                    periods,
                    f"extra_subject_blocks"
                    f"_s{s}"
                    f"_b{b}"
                    f"_d{d}"
                )

                model.Add(
                    extra_blocks
                    ==
                    sum(block_starts)
                    -
                    first_block
                )

                penalties.append(
                    extra_blocks
                )

    # ============================================================
    # 3. STRONGLY PENALIZE SPLITTING
    # ============================================================
    #
    # A subject with:
    #
    #     DBMS DBMS DBMS
    #
    # has one block.
    #
    # A subject with:
    #
    #     DBMS DBMS - DBMS
    #
    # has two blocks.
    #
    # The second case receives a stronger penalty.
    #
    # ============================================================

    for s in range(len(subjects)):

        for b in range(len(batches)):

            for d in range(days):

                for p in range(1, periods - 1):

                    previous = subject_used[
                        s, b, d, p - 1
                    ]

                    current = subject_used[
                        s, b, d, p
                    ]

                    next_period = subject_used[
                        s, b, d, p + 1
                    ]

                    # ------------------------------------------------
                    # Detect:
                    #
                    # subject
                    # empty
                    # subject
                    #
                    # This is a split pattern.
                    # ------------------------------------------------

                    split = model.NewBoolVar(
                        f"subject_split"
                        f"_s{s}"
                        f"_b{b}"
                        f"_d{d}"
                        f"_p{p}"
                    )

                    model.Add(
                        split <= previous
                    )

                    model.Add(
                        split <= 1 - current
                    )

                    model.Add(
                        split <= next_period
                    )

                    model.Add(
                        split >=
                        previous
                        +
                        next_period
                        -
                        current
                        -
                        1
                    )

                    # Strong penalty for this pattern.
                    penalties.append(split)
                    penalties.append(split)

    # ============================================================
    # 4. PREFER LARGER CONTINUOUS BLOCKS
    # ============================================================
    #
    # If a subject has multiple periods on a day, prefer:
    #
    #     XXX
    #
    # over:
    #
    #     XX X
    #
    # and:
    #
    #     X X X
    #
    # We identify adjacent pairs and reward them through negative
    # objective terms.
    #
    # This function returns "rewards" separately so objective.py
    # can maximize them.
    #
    # ============================================================

    rewards = []

    for s in range(len(subjects)):

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods - 1):

                    current = subject_used[
                        s, b, d, p
                    ]

                    next_period = subject_used[
                        s, b, d, p + 1
                    ]

                    adjacent = model.NewBoolVar(
                        f"subject_adjacent"
                        f"_s{s}"
                        f"_b{b}"
                        f"_d{d}"
                        f"_p{p}"
                    )

                    model.Add(
                        adjacent <= current
                    )

                    model.Add(
                        adjacent <= next_period
                    )

                    model.Add(
                        adjacent >=
                        current
                        +
                        next_period
                        -
                        1
                    )

                    rewards.append(adjacent)

    # ============================================================
    # RETURN
    # ============================================================
    #
    # Return both:
    #
    #     penalties
    #     rewards
    #
    # objective.py will decide how strongly each should affect
    # the final timetable.
    #
    # ============================================================

    return {
        "penalties": penalties,
        "rewards": rewards
    }