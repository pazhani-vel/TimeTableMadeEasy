# ================================================================
# DAY-BASED HARD CONSTRAINTS
# ================================================================
#
# Rules enforced here:
#
# 1. P1 must not be empty (batch.py handles this).
# 2. P2 must not be empty (batch.py handles this).
# 3. Subject periods on the same day must be continuous.
#
# NOTE: theory.py handles max 2 days per subject.
#       batch.py handles P1/P2 occupancy.
#       This file is kept minimal to avoid conflicts.
#
# ================================================================


def add_day_constraints(timetable):
    """
    Day-based hard constraints.

    Currently a no-op because:
    - P1/P2 is enforced by batch.py
    - Max 2 days is enforced by theory.py
    - Theory continuity is enforced by theory.py

    Kept as a hook for future day-specific rules.
    """
    pass


# ================================================================
# GET PERIOD VARIABLES
# ================================================================

def get_period_variables(timetable, batch, day, period):
    """
    Return every variable that can occupy a batch's period.
    """
    variables = []

    for s in range(len(timetable.subjects)):
        variables.append(timetable.theory_y[s, batch, day, period])
        variables.append(timetable.lab_y[s, batch, day, period])

    variables.append(timetable.naan_mudalvan[batch, day, period])
    variables.append(timetable.audit[batch, day, period])
    variables.append(timetable.ioc[batch, day, period])

    return variables


# ================================================================
# REQUIRED PERIODS
# ================================================================

def get_required_periods(subject):
    if not isinstance(subject, dict):
        return 0

    if "required_periods" in subject:
        try:
            return int(subject["required_periods"])
        except (TypeError, ValueError):
            pass

    theory = subject.get(
        "theory_periods",
        subject.get("theory_hours", subject.get("theory", 0))
    )
    lab = subject.get(
        "lab_periods",
        subject.get("lab_hours", subject.get("lab", 0))
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
