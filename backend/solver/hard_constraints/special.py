from ortools.sat.python import cp_model


def add_special_constraints(timetable):
    """
    Add HARD constraints for special timetable activities.

    Constraints:
        1. Naan Mudalvan must be continuous.
        2. Audit can only be in P7/P8.
        3. IOC can only be in P7/P8.
        4. Naan Mudalvan cannot be split into multiple blocks.
    """

    model = timetable.model

    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    naan_mudalvan = timetable.naan_mudalvan
    audit = timetable.audit
    ioc = timetable.ioc

    # ============================================================
    # SPECIAL PERIOD CONFIGURATION
    # ============================================================
    #
    # By default:
    #
    #     Audit → P7/P8
    #     IOC   → P7/P8
    #
    # If your timetable has fewer than 8 periods, this will raise
    # an error because P7/P8 cannot exist.
    #
    # ============================================================

    p7_index = 6
    p8_index = 7

    if periods < 8:
        raise ValueError(
            "At least 8 periods are required because "
            "Audit and IOC must be scheduled in P7/P8."
        )

    allowed_special_periods = {
        p7_index,
        p8_index
    }

    # ============================================================
    # 0. FORCE SPECIAL ACTIVITIES TO 0 WHEN NOT CONFIGURED
    # ============================================================
    #
    # If the user sets naan_mudalvan_periods = 0,
    # ioc_periods = 0, or audit_periods = 0,
    # force those variables to 0 everywhere.
    #
    # Without this, the solver would freely set them
    # to 1 in P7/P8 to fill empty slots.
    #
    # ============================================================

    audit_periods = get_audit_periods(timetable)
    ioc_periods = get_ioc_periods(timetable)
    naan_periods = get_naan_mudalvan_periods(timetable)

    if naan_periods == 0:
        for b in range(len(batches)):
            for d in range(days):
                for p in range(periods):
                    model.Add(
                        naan_mudalvan[b, d, p] == 0
                    )

    if audit_periods == 0:
        for b in range(len(batches)):
            for d in range(days):
                for p in range(periods):
                    model.Add(
                        audit[b, d, p] == 0
                    )

    if ioc_periods == 0:
        for b in range(len(batches)):
            for d in range(days):
                for p in range(periods):
                    model.Add(
                        ioc[b, d, p] == 0
                    )

    # ============================================================
    # 1. AUDIT ONLY IN P7/P8
    # ============================================================

    if audit_periods > 0:
        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods):

                    if p not in allowed_special_periods:

                        model.Add(
                            audit[b, d, p] == 0
                        )

    # ============================================================
    # 2. IOC ONLY IN P7/P8
    # ============================================================

    if ioc_periods > 0:
        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods):

                    if p not in allowed_special_periods:

                        model.Add(
                            ioc[b, d, p] == 0
                        )

    # ============================================================
    # 3. NAAN MUDALVAN CONTINUOUS
    # ============================================================

    if naan_periods > 0:

        if naan_periods > periods:

            raise ValueError(
                "Naan Mudalvan requires more periods than "
                "the timetable contains."
            )

        for b in range(len(batches)):

            # ----------------------------------------------------
            # A block can start only where N consecutive periods
            # are available.
            # ----------------------------------------------------

            possible_starts = []

            for d in range(days):

                for start in range(
                    periods - naan_periods + 1
                ):

                    start_var = model.NewBoolVar(
                        f"naan_start_b{b}_d{d}_p{start}"
                    )

                    possible_starts.append(
                        start_var
                    )

                    # ------------------------------------------------
                    # If start_var = 1, all N periods must be
                    # Naan Mudalvan.
                    # ------------------------------------------------

                    for offset in range(naan_periods):

                        p = start + offset

                        model.Add(
                            naan_mudalvan[
                                b, d, p
                            ]
                            >= start_var
                        )

                    # ------------------------------------------------
                    # If all N periods are occupied by Naan Mudalvan,
                    # start_var may become 1.
                    # ------------------------------------------------

                    block_vars = [
                        naan_mudalvan[
                            b,
                            d,
                            start + offset
                        ]
                        for offset in range(
                            naan_periods
                        )
                    ]

                    model.Add(
                        start_var
                        >=
                        sum(block_vars)
                        - naan_periods
                        + 1
                    )

                    # If start_var = 1, all block periods = 1.
                    # Already guaranteed above.

            # ----------------------------------------------------
            # Exact number of Naan Mudalvan periods.
            #
            # If N = 3, exactly 3 periods must be assigned.
            # ----------------------------------------------------

            model.Add(
                sum(
                    naan_mudalvan[
                        b, d, p
                    ]
                    for d in range(days)
                    for p in range(periods)
                )
                == naan_periods
            )

            # ----------------------------------------------------
            # Exactly ONE continuous block.
            # ----------------------------------------------------

            model.Add(
                sum(possible_starts) == 1
            )

    # ============================================================
    # 4. NO DUPLICATE SPECIAL ACTIVITY
    # ============================================================
    #
    # A batch cannot have:
    #
    #     Audit + IOC
    #
    # at the same time.
    #
    # Batch constraints also handle clashes with theory/lab.
    #
    # ============================================================

    for b in range(len(batches)):

        for d in range(days):

            for p in range(periods):

                model.Add(
                    audit[b, d, p]
                    +
                    ioc[b, d, p]
                    +
                    naan_mudalvan[b, d, p]
                    <= 1
                )

    return model


# ================================================================
# HELPER
# ================================================================

def get_naan_mudalvan_periods(timetable):
    """
    Read the required number of Naan Mudalvan periods.

    Supported input fields:

        naan_mudalvan_periods
        naan_mudalvan_hours

    If neither exists, returns 0.
    """

    data = timetable.data

    value = data.get(
        "naan_mudalvan_periods"
    )

    if value is None:
        value = data.get(
            "naan_mudalvan_hours",
            0
        )

    try:
        return int(value)

    except (TypeError, ValueError):

        return 0


# ================================================================
# HELPER - AUDIT PERIODS
# ================================================================

def get_audit_periods(timetable):
    """
    Read the required number of Audit periods.

    Supported input fields:

        audit_periods

    If not set, returns 0.
    """

    data = timetable.data

    value = data.get(
        "audit_periods",
        0
    )

    try:
        return int(value)

    except (TypeError, ValueError):

        return 0


# ================================================================
# HELPER - IOC PERIODS
# ================================================================

def get_ioc_periods(timetable):
    """
    Read the required number of IOC periods.

    Supported input fields:

        ioc_periods

    If not set, returns 0.
    """

    data = timetable.data

    value = data.get(
        "ioc_periods",
        0
    )

    try:
        return int(value)

    except (TypeError, ValueError):

        return 0