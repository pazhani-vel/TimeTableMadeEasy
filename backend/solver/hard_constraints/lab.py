from ortools.sat.python import cp_model


def add_lab_constraints(timetable):
    """
    Add all HARD constraints related to laboratory classes.

    Constraints:
        1. Exact number of lab sessions per batch.
        2. Every lab occupies exactly 2 consecutive periods.
        3. Lab cannot cross lunch.
        4. Maximum one lab session per subject per day.
        5. Theory and lab of the same subject cannot occur
           on the same day.

    Subjects are scoped to their batch via batch_id.
    Non-target batches get lab_start forced to 0.
    """
    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches

    days = timetable.num_days
    periods = timetable.num_periods

    lab_start = timetable.lab_start
    lab_y = timetable.lab_y
    day_used = timetable.day_used

    lunch_after_period = timetable.data.get(
        "lunch_after_period", 4
    )
    try:
        lunch_after_period = int(lunch_after_period)
    except (TypeError, ValueError):
        lunch_after_period = 4

    lunch_index = lunch_after_period - 1

    for s, subject in enumerate(subjects):

        lab_hours = subject.get(
            "lab_hours",
            subject.get("lab", 0)
        )
        try:
            lab_hours = int(lab_hours)
        except (TypeError, ValueError):
            lab_hours = 0

        if lab_hours < 0:
            raise ValueError(
                f"Invalid lab hours for: "
                f"{subject_name(subject, s)}"
            )

        if lab_hours % 2 != 0:
            raise ValueError(
                f"Lab hours must be even for: "
                f"{subject_name(subject, s)}. "
                f"Got: {lab_hours}"
            )

        required_lab_sessions = lab_hours // 2

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
        # FORCE lab_start = 0 for NON-TARGET batches
        # ========================================================

        for b in range(len(batches)):

            if b in target_batches:
                continue

            for d in range(days):
                for p in range(periods):
                    model.Add(
                        lab_start[s, b, d, p] == 0
                    )
                    model.Add(
                        lab_y[s, b, d, p] == 0
                    )

        # ========================================================
        # PROCESS EACH TARGET BATCH
        # ========================================================

        for b in target_batches:

            # --- 1. EXACT NUMBER OF LAB SESSIONS ---

            total_lab_starts = sum(
                lab_start[s, b, d, p]
                for d in range(days)
                for p in range(periods)
            )
            model.Add(
                total_lab_starts == required_lab_sessions
            )

            # --- 2. LAB START → TWO CONSECUTIVE PERIODS ---

            for d in range(days):
                for p in range(periods):
                    start = lab_start[s, b, d, p]

                    if p == periods - 1:
                        model.Add(start == 0)
                        continue

                    model.Add(lab_y[s, b, d, p] >= start)
                    model.Add(
                        lab_y[s, b, d, p + 1] >= start
                    )

            # --- 3. LINK LAB OCCUPANCY TO LAB STARTS ---

            for d in range(days):
                for p in range(periods):
                    covering = [lab_start[s, b, d, p]]
                    if p > 0:
                        covering.append(
                            lab_start[s, b, d, p - 1]
                        )
                    model.Add(
                        lab_y[s, b, d, p]
                        == sum(covering)
                    )

            # --- 4. LAB CANNOT CROSS LUNCH ---

            for d in range(days):
                model.Add(
                    lab_start[s, b, d, lunch_index] == 0
                )

            # --- 5. MAX ONE LAB PER SUBJECT PER DAY ---

            for d in range(days):
                model.Add(
                    sum(
                        lab_start[s, b, d, p]
                        for p in range(periods)
                    ) <= 1
                )

            # --- 6. THEORY AND LAB ON DIFFERENT DAYS ---

            for d in range(days):
                daily_lab = sum(
                    lab_start[s, b, d, p]
                    for p in range(periods)
                )
                model.Add(
                    daily_lab + day_used[s, b, d] <= 1
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
