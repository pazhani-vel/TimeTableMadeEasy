from ortools.sat.python import cp_model


def add_consecutive_theory_lab_constraints(timetable):
    """
    SOFT preference: theory and its lab may be consecutive.

    This never makes the model infeasible. A reward is created when
    the final theory period is immediately followed by the lab start
    for the same subject and schedule.
    """
    model = timetable.model
    subjects = timetable.subjects
    batches = timetable.batches
    days = timetable.num_days
    periods = timetable.num_periods

    rewards = []
    theory_y = timetable.theory_y
    lab_start = timetable.lab_start

    for s, subject in enumerate(subjects):
        if not isinstance(subject, dict):
            continue

        theory_periods = int(
            subject.get("theory_periods", 0) or 0
        )
        lab_periods = int(
            subject.get("lab_periods", 0) or 0
        )

        if theory_periods <= 0 or lab_periods <= 0:
            continue

        # Determine which batches this subject applies to
        subject_batch_id = (
            subject.get("batch_id")
            or subject.get("batch")
            or subject.get("schedule_id")
        )

        target_batches = []

        for b, batch in enumerate(batches):
            if subject_batch_id is not None:
                batch_id = (
                    batch.get("id")
                    if isinstance(batch, dict)
                    else batch
                )
                if str(batch_id) != str(subject_batch_id):
                    continue
            target_batches.append(b)

        for b in target_batches:
            for d in range(days):
                for p in range(periods - 1):
                    # Theory at p followed by lab starting at p+1
                    before = model.NewBoolVar(
                        f"theory_lab_consecutive_before_s{s}_b{b}_d{d}_p{p}"
                    )
                    model.Add(before <= theory_y[s, b, d, p])
                    model.Add(before <= lab_start[s, b, d, p + 1])
                    model.Add(
                        before >=
                        theory_y[s, b, d, p] +
                        lab_start[s, b, d, p + 1] - 1
                    )
                    rewards.append(before)

                    # Lab starting at p followed immediately by theory
                    # after the two-period lab (p+2)
                    if p + 2 < periods:
                        after = model.NewBoolVar(
                            f"theory_lab_consecutive_after_s{s}_b{b}_d{d}_p{p}"
                        )
                        model.Add(after <= lab_start[s, b, d, p])
                        model.Add(after <= theory_y[s, b, d, p + 2])
                        model.Add(
                            after >=
                            lab_start[s, b, d, p] +
                            theory_y[s, b, d, p + 2] - 1
                        )
                        rewards.append(after)

    return {"penalties": [], "rewards": rewards}
