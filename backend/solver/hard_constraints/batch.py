from ortools.sat.python import cp_model


def add_batch_constraints(timetable):
    """
    Add HARD constraints related to batches.

    Constraints:
        1. A batch can have at most one class in a period.
        2. Theory and lab classes are included in clash checking.
        3. Special classes are included in clash checking.
        4. Both P1 and P2 must contain a real class every day.
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    theory_y = timetable.theory_y
    lab_y = timetable.lab_y

    naan_mudalvan = timetable.naan_mudalvan
    audit = timetable.audit
    ioc = timetable.ioc

    # ============================================================
    # 1. NO BATCH CLASH
    # ============================================================
    #
    # A batch cannot have:
    #
    #     DBMS
    #     OS
    #
    # at the same day and period.
    #
    # The same applies to labs and special classes.
    #
    # ============================================================

    for b, batch in enumerate(batches):

        for d in range(days):

            for p in range(periods):

                classes_at_this_time = []

                # ------------------------------------------------
                # THEORY CLASSES
                # ------------------------------------------------

                for s in range(len(subjects)):

                    classes_at_this_time.append(
                        theory_y[s, b, d, p]
                    )

                # ------------------------------------------------
                # LAB CLASSES
                # ------------------------------------------------

                for s in range(len(subjects)):

                    classes_at_this_time.append(
                        lab_y[s, b, d, p]
                    )

                # ------------------------------------------------
                # SPECIAL CLASSES
                # ------------------------------------------------

                classes_at_this_time.append(
                    naan_mudalvan[b, d, p]
                )

                classes_at_this_time.append(
                    audit[b, d, p]
                )

                classes_at_this_time.append(
                    ioc[b, d, p]
                )

                # ------------------------------------------------
                # AT MOST ONE CLASS
                # ------------------------------------------------

                model.Add(
                    sum(classes_at_this_time) <= 1
                )

    # ============================================================
    # 2. BOTH P1 AND P2 MUST BE OCCUPIED
    # ============================================================
    #
    # This is a HARD constraint.
    #
    # For every batch and every day:
    #
    #     P1 != empty
    #     P2 != empty
    #
    # However, this is only enforced when the batch has
    # enough subjects to realistically fill both periods.
    #
    # A batch needs at least 2 subjects with theory hours
    # to satisfy P1+P2 for every day of the week.
    #
    # ============================================================

    for b, batch in enumerate(batches):

        # --------------------------------------------------------
        # Count how many subjects this batch has.
        #
        # If a batch has fewer than 2 subjects,
        # skip the P1/P2 constraint for that batch.
        # --------------------------------------------------------

        batch_id = (
            batch.get("id")
            if isinstance(batch, dict)
            else batch
        )

        batch_subject_count = 0

        for s, subject in enumerate(subjects):

            subject_batch_id = (
                subject.get("batch_id")
                or subject.get("batch")
                or subject.get("schedule_id")
            )

            if subject_batch_id is not None:

                if str(subject_batch_id) != str(batch_id):
                    continue

            batch_subject_count += 1

        # --------------------------------------------------------
        # Skip P1/P2 constraint if batch has < 2 subjects.
        # --------------------------------------------------------

        if batch_subject_count < 2:
            continue

        for d in range(days):

            # ----------------------------------------------------
            # Make sure we actually have at least two periods.
            # ----------------------------------------------------

            if periods < 2:
                raise ValueError(
                    "At least 2 periods are required because "
                    "both P1 and P2 must be occupied."
                )

            # ----------------------------------------------------
            # P1
            # ----------------------------------------------------

            p1_classes = []

            for s in range(len(subjects)):

                p1_classes.append(
                    theory_y[s, b, d, 0]
                )

                p1_classes.append(
                    lab_y[s, b, d, 0]
                )

            p1_classes.append(
                naan_mudalvan[b, d, 0]
            )

            p1_classes.append(
                audit[b, d, 0]
            )

            p1_classes.append(
                ioc[b, d, 0]
            )

            # At least one real class must exist in P1.
            model.Add(
                sum(p1_classes) >= 1
            )

            # ----------------------------------------------------
            # P2
            # ----------------------------------------------------

            p2_classes = []

            for s in range(len(subjects)):

                p2_classes.append(
                    theory_y[s, b, d, 1]
                )

                p2_classes.append(
                    lab_y[s, b, d, 1]
                )

            p2_classes.append(
                naan_mudalvan[b, d, 1]
            )

            p2_classes.append(
                audit[b, d, 1]
            )

            p2_classes.append(
                ioc[b, d, 1]
            )

            # At least one real class must exist in P2.
            model.Add(
                sum(p2_classes) >= 1
            )

    return model