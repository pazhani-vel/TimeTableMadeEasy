from ortools.sat.python import cp_model


def add_faculty_constraints(timetable):
    """
    Add HARD faculty/staff constraints.

    Constraints:
        1. A faculty member cannot teach two batches at the same time.
        2. Between separate teaching sessions, at least one free period
           must exist (no back-to-back across different sessions).
        3. Same-subject same-batch consecutive periods (theory blocks)
           are ALLOWED.
        4. Two consecutive lab periods belonging to the same lab
           session are ALLOWED.

    CRITICAL: The staff_teach linking uses a per-staff upper bound
    (sum across ALL subjects taught by that staff), NOT per-subject
    upper bounds. Per-subject upper bounds cause infeasibility when
    a staff teaches multiple subjects across different batches.
    """

    model = timetable.model

    subjects = timetable.subjects
    batches = timetable.batches
    staff = timetable.staff

    days = timetable.num_days
    periods = timetable.num_periods

    theory_y = timetable.theory_y
    lab_y = timetable.lab_y
    lab_start = timetable.lab_start
    staff_teach = timetable.staff_teach

    # ============================================================
    # PRECOMPUTE: Which subjects does each staff member teach?
    # ============================================================

    staff_subjects = {}
    for s, subject in enumerate(subjects):
        si = get_staff_index(subject, staff, s)
        if si is not None:
            staff_subjects.setdefault(si, []).append(s)

    # ============================================================
    # 1. LINK STAFF_TEACH WITH THEORY AND LAB CLASSES
    # ============================================================
    #
    # For each (staff, batch, day, period):
    #
    #   staff_teach >= theory_y[s] for each subject s taught
    #   staff_teach >= lab_y[s] for each subject s taught
    #   staff_teach <= sum(theory_y[s] + lab_y[s] for all s)
    #
    # The upper bound MUST be across ALL subjects taught by this
    # staff, not per-subject. Per-subject bounds cause conflicts
    # when a staff teaches subjects for different batches.
    #
    # ============================================================

    for si, subject_indices in staff_subjects.items():

        for b in range(len(batches)):

            for d in range(days):

                for p in range(periods):

                    # -------------------------------------------
                    # Lower bounds: staff_teach >= each subject
                    # -------------------------------------------

                    for s in subject_indices:

                        model.Add(
                            staff_teach[si, b, d, p]
                            >= theory_y[s, b, d, p]
                        )

                        model.Add(
                            staff_teach[si, b, d, p]
                            >= lab_y[s, b, d, p]
                        )

                    # -------------------------------------------
                    # Upper bound: staff_teach <= sum of ALL
                    # subjects taught by this staff
                    # -------------------------------------------

                    model.Add(
                        staff_teach[si, b, d, p]
                        <= sum(
                            theory_y[s, b, d, p]
                            + lab_y[s, b, d, p]
                            for s in subject_indices
                        )
                    )

    # ============================================================
    # 2. NO FACULTY CLASH
    # ============================================================
    #
    # A faculty member can teach at most ONE batch at a time.
    #
    # ============================================================

    for st in range(len(staff)):

        for d in range(days):

            for p in range(periods):

                model.Add(
                    sum(
                        staff_teach[st, b, d, p]
                        for b in range(len(batches))
                    )
                    <= 1
                )

    # ============================================================
    # 3. FACULTY GAP BETWEEN SEPARATE SESSIONS
    # ============================================================
    #
    # Adjacent periods (P and P+1) are allowed only when both
    # belong to the SAME continuous block:
    #
    #   a) Same theory block for same subject + same batch
    #   b) Same lab session for same subject + same batch
    #
    # Otherwise: current + next <= 1
    #
    # ============================================================

    for st in range(len(staff)):

        for d in range(days):

            for p in range(periods - 1):

                current = staff_teaching_at_period(
                    staff_teach, st, batches, d, p
                )
                next_period = staff_teaching_at_period(
                    staff_teach, st, batches, d, p + 1
                )

                block_exemptions = []

                for s_idx in staff_subjects.get(st, []):

                    for b_idx in range(len(batches)):

                        # --- Theory block exemption ---
                        theory_both = model.NewBoolVar(
                            f"theory_both_st{st}_s{s_idx}"
                            f"_b{b_idx}_d{d}_p{p}"
                        )
                        model.Add(
                            theory_both
                            <= theory_y[s_idx, b_idx, d, p]
                        )
                        model.Add(
                            theory_both
                            <= theory_y[s_idx, b_idx, d, p + 1]
                        )
                        model.Add(
                            theory_both >=
                            theory_y[s_idx, b_idx, d, p]
                            + theory_y[s_idx, b_idx, d, p + 1]
                            - 1
                        )
                        block_exemptions.append(theory_both)

                        # --- Lab session exemption ---
                        block_exemptions.append(
                            lab_start[s_idx, b_idx, d, p]
                        )

                model.Add(
                    current + next_period
                    <= 1 + sum(block_exemptions)
                )

    return model


# ================================================================
# HELPERS
# ================================================================

def get_staff_index(subject, staff, subject_index):
    """
    Find the faculty/staff index associated with a subject.
    """

    if not isinstance(subject, dict):
        return None

    value = (
        subject.get("staff_id")
        if subject.get("staff_id") is not None
        else subject.get("faculty_id")
    )

    if value is None:
        value = subject.get("staff")
    if value is None:
        value = subject.get("faculty")
    if value is None:
        value = subject.get("staff_index")
    if value is None:
        return None

    if isinstance(value, int):
        if 0 <= value < len(staff):
            return value
        return None

    value_str = str(value)

    for index, member in enumerate(staff):
        if isinstance(member, dict):
            possible_values = [
                member.get("id"),
                member.get("_id"),
                member.get("staff_id"),
                member.get("faculty_id"),
                member.get("name"),
                member.get("staff_name"),
            ]
            if value_str in {
                str(v) for v in possible_values if v is not None
            }:
                return index
        else:
            if str(member) == value_str:
                return index

    return None


def staff_teaching_at_period(
    staff_teach, staff_index, batches, day, period
):
    """
    Return the sum of all batches taught by a faculty member
    at a particular day/period.
    """
    return sum(
        staff_teach[staff_index, b, day, period]
        for b in range(len(batches))
    )
