from ortools.sat.python import cp_model


def add_theory_constraints(timetable):
    """
    Add all HARD constraints related to theory classes.

    Constraints:
        1. Exact theory hours per target batch.
        2. Theory can be scheduled on at most 2 days.
        3. day_used correctly reflects theory days.
        4. Theory periods must be continuous on a day.
        5. theory_y = 0 for non-target batches.
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    theory_y = timetable.theory_y
    day_used = timetable.day_used
    theory_block_start = timetable.theory_block_start

    for s, subject in enumerate(subjects):

        theory_hours = subject.get(
            "theory_hours",
            subject.get("theory", 0)
        )
        try:
            theory_hours = int(theory_hours)
        except (TypeError, ValueError):
            theory_hours = 0

        if theory_hours < 0:
            raise ValueError(
                f"Invalid theory hours for: "
                f"{subject_name(subject, s)}"
            )

        # ========================================================
        # DETERMINE TARGET BATCHES
        # ========================================================

        subject_batch_id = (
            subject.get("batch_id")
            or subject.get("batch")
            or subject.get("schedule_id")
        )

        target_batches = set()

        for b, batch in enumerate(batches):
            if subject_batch_id is not None:
                batch_id = (
                    batch.get("id")
                    if isinstance(batch, dict)
                    else batch
                )
                if str(batch_id) != str(subject_batch_id):
                    continue
            target_batches.add(b)

        # ========================================================
        # FORCE theory_y = 0 FOR NON-TARGET BATCHES
        # ========================================================

        for b in range(len(batches)):
            if b in target_batches:
                continue
            for d in range(days):
                for p in range(periods):
                    model.Add(
                        theory_y[s, b, d, p] == 0
                    )
                    model.Add(
                        day_used[s, b, d] == 0
                    )

        # ========================================================
        # 1. EXACT THEORY HOURS (target batches only)
        # ========================================================

        for b in target_batches:
            total_theory = sum(
                theory_y[s, b, d, p]
                for d in range(days)
                for p in range(periods)
            )
            model.Add(total_theory == theory_hours)

        # ========================================================
        # 2. THEORY ON MAX 2 DAYS (target batches only)
        # ========================================================

        for b in target_batches:
            model.Add(
                sum(
                    day_used[s, b, d]
                    for d in range(days)
                ) <= 2
            )

        # ========================================================
        # 3. LINK day_used WITH THEORY PERIODS
        # ========================================================

        for b in target_batches:
            for d in range(days):
                daily_theory = sum(
                    theory_y[s, b, d, p]
                    for p in range(periods)
                )
                model.Add(
                    daily_theory <= periods * day_used[s, b, d]
                )
                model.Add(
                    daily_theory >= day_used[s, b, d]
                )

        # ========================================================
        # 4. THEORY PERIODS MUST BE CONTINUOUS ON A DAY
        # ========================================================

        for b in target_batches:
            for d in range(days):
                starts = []

                for p in range(periods):
                    start_var = theory_block_start[s, b, d, p]
                    starts.append(start_var)

                    if p == 0:
                        model.Add(
                            start_var == theory_y[s, b, d, p]
                        )
                    else:
                        model.Add(
                            start_var >=
                            theory_y[s, b, d, p]
                            - theory_y[s, b, d, p - 1]
                        )
                        model.Add(
                            start_var <= theory_y[s, b, d, p]
                        )
                        model.Add(
                            start_var <=
                            1 - theory_y[s, b, d, p - 1]
                        )

                model.Add(sum(starts) <= 1)

        # ========================================================
        # 5. BLOCK COUNT = day_used
        # ========================================================

        for b in target_batches:
            for d in range(days):
                model.Add(
                    sum(
                        theory_block_start[s, b, d, p]
                        for p in range(periods)
                    ) == day_used[s, b, d]
                )

    return model


def subject_name(subject, index):
    if isinstance(subject, dict):
        return (
            subject.get("name")
            or subject.get("subject_name")
            or subject.get("code")
            or f"subject_{index}"
        )
    return str(subject)
