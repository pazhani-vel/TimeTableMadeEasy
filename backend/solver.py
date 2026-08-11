# #!/usr/bin/env python3
# """
# Timetable solver using Google OR-Tools CP-SAT.
# Built for a single department (IT) with two batches of the same semester,
# using LTP (Lecture-Practical) subject codes. Tutorial (T) is not used.

# Input (stdin, JSON):
# {
#   "days": 5,
#   "periods_per_day": 8,
#   "batches": ["A", "B"],
#   "subjects": [
#     {
#       "name": "Data Structures",
#       "batch": "A",
#       "staff": "Dr. Radha Senthilkumar",
#       "theory_hours": 3,      # "L" - lecture periods/week
#       "has_lab": true,
#       "lab_hours": 2          # "P" - practical periods/week (multiples of 2)
#     },
#     ...
#   ]
# }

# Fixed daily structure (assumed 8 periods/day):
#   Period 1-4  -> morning session
#   LUNCH BREAK -> 12:00 - 1:00 (not a period, purely a display gap)
#   Period 5-8  -> afternoon session
# A 2-period lab block is never allowed to straddle the lunch break
# (e.g. period 4 + period 5), since that would put half a lab session
# before lunch and half after it.

# Rules encoded (per subject-batch-staff entry):
#   - No staff teaches two things at once (across batches).
#   - No batch has two classes at once.
#   - Theory (L) hours for a subject are spread across AT MOST 2 distinct days.
#   - If has_lab, lab_hours/2 separate 2-period-contiguous lab sessions are
#     scheduled, each on its own day, and every lab day is different from
#     every theory day for that subject (lab and theory never share a day).
#   - No lab block may straddle the lunch break.
#   - Every staff member gets at least a 1-period gap after any class ends
#     before their next class starts, on the same day (i.e. they are never
#     booked for two back-to-back periods unless it is their own 2-period
#     lab block, which is one continuous session, not two separate classes).

# Output (stdout, JSON):
# {
#   "status": "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "UNKNOWN",
#   "timetable": { "A": [[cell,...]*periods_per_day for each day], ... },
#   "message": "..."
# }
# Each cell is either null or {"subject":..., "staff":..., "type":"theory"|"lab"}.
# """

# import sys
# import json
# from ortools.sat.python import cp_model

# LAB_PERIODS = 2  # a single lab session occupies this many contiguous periods


# def solve(data):
#     days = data["days"]
#     periods = data["periods_per_day"]
#     batches = data["batches"]
#     subjects = data["subjects"]  # each: name, batch, staff, theory_hours, has_lab, lab_hours

#     # Where the lunch break sits: after the first half of the day's periods.
#     # For the standard 8-period day this is after period 4 (index 3),
#     # i.e. no lab may start at index (half - 1) because it would then
#     # occupy index (half - 1) and index half, straddling lunch.
#     half = periods // 2

#     model = cp_model.CpModel()
#     n = len(subjects)

#     staff_list = sorted({s["staff"] for s in subjects})
#     staff_of = {t: i for i, t in enumerate(staff_list)}

#     # ---- number of lab sessions per subject, derived from lab_hours ----
#     num_lab_sessions = []
#     for subj in subjects:
#         if subj.get("has_lab"):
#             lh = int(subj.get("lab_hours", LAB_PERIODS) or 0)
#             sessions = max(1, lh // LAB_PERIODS)
#         else:
#             sessions = 0
#         num_lab_sessions.append(sessions)

#     # theory_y[s][d][p] : subject s has a theory period on day d, period p
#     theory_y = {}
#     for s in range(n):
#         for d in range(days):
#             for p in range(periods):
#                 theory_y[s, d, p] = model.NewBoolVar(f"th_{s}_{d}_{p}")

#     # day_used[s][d]: subject s has any theory class on day d
#     day_used = {}
#     for s in range(n):
#         for d in range(days):
#             day_used[s, d] = model.NewBoolVar(f"du_{s}_{d}")

#     # lab_start[s][d][p]: subject s's lab session begins at day d, period p
#     # lab_y[s][d][p]: subject s occupies (via a lab) day d, period p
#     lab_start = {}
#     lab_y = {}
#     for s in range(n):
#         for d in range(days):
#             for p in range(periods):
#                 lab_y[s, d, p] = model.NewBoolVar(f"lb_{s}_{d}_{p}")
#                 can_start = (p <= periods - LAB_PERIODS) and (p != half - 1)
#                 if can_start:
#                     lab_start[s, d, p] = model.NewBoolVar(f"ls_{s}_{d}_{p}")

#     for s, subj in enumerate(subjects):
#         hours = int(subj["theory_hours"])

#         # 1) exact weekly theory (L) hours
#         model.Add(sum(theory_y[s, d, p] for d in range(days) for p in range(periods)) == hours)

#         # 2) link day_used to theory_y, and cap at 2 distinct days
#         for d in range(days):
#             day_sum = sum(theory_y[s, d, p] for p in range(periods))
#             model.Add(day_sum <= periods * day_used[s, d])
#             model.Add(day_sum >= day_used[s, d])
#         model.Add(sum(day_used[s, d] for d in range(days)) <= 2)

#         # 3) lab sessions: exactly `num_lab_sessions[s]` contiguous 2-period
#         #    blocks, one per day used for a lab, none straddling lunch.
#         starts = [lab_start[s, d, p] for d in range(days) for p in range(periods) if (s, d, p) in lab_start]
#         model.Add(sum(starts) == num_lab_sessions[s])

#         for d in range(days):
#             for p in range(periods):
#                 covering = []
#                 if (s, d, p) in lab_start:
#                     covering.append(lab_start[s, d, p])
#                 if p >= 1 and (s, d, p - 1) in lab_start:
#                     covering.append(lab_start[s, d, p - 1])
#                 if covering:
#                     model.Add(lab_y[s, d, p] == sum(covering))
#                 else:
#                     model.Add(lab_y[s, d, p] == 0)

#             # at most one lab session per day for this subject, and the
#             # lab day must differ from theory day(s) for this subject
#             lab_active_this_day = sum(
#                 lab_start[s, d, p] for p in range(periods) if (s, d, p) in lab_start
#             )
#             model.Add(lab_active_this_day <= 1)
#             model.Add(lab_active_this_day + day_used[s, d] <= 1)

#     # 4) batch clash-free: at most one class per batch per slot
#     for b in batches:
#         idxs = [s for s, subj in enumerate(subjects) if subj["batch"] == b]
#         for d in range(days):
#             for p in range(periods):
#                 model.Add(sum(theory_y[s, d, p] + lab_y[s, d, p] for s in idxs) <= 1)

#     # 5) staff clash-free + at-least-1-period gap between separate classes
#     teach = {}
#     for t in staff_list:
#         ti = staff_of[t]
#         idxs = [s for s, subj in enumerate(subjects) if subj["staff"] == t]
#         for d in range(days):
#             for p in range(periods):
#                 v = model.NewBoolVar(f"teach_{ti}_{d}_{p}")
#                 model.Add(v == sum(theory_y[s, d, p] + lab_y[s, d, p] for s in idxs))
#                 model.Add(v <= 1)
#                 teach[ti, d, p] = v

#         lab_idxs = [s for s in idxs if subjects[s].get("has_lab")]
#         for d in range(days):
#             lab_pair = {}
#             for p in range(periods):
#                 starters = [lab_start[s, d, p] for s in lab_idxs if (s, d, p) in lab_start]
#                 if starters:
#                     lp = model.NewBoolVar(f"labpair_{ti}_{d}_{p}")
#                     model.Add(lp == sum(starters))
#                 else:
#                     lp = model.NewConstant(0)
#                 lab_pair[p] = lp

#             for p in range(periods - 1):
#                 # Two adjacent periods can both be occupied by this staff
#                 # member only if it's their own lab block (one session).
#                 # Otherwise there must be at least a 1-period gap between
#                 # any two of their classes.
#                 model.Add(teach[ti, d, p] + teach[ti, d, p + 1] <= 1 + lab_pair[p])

#     solver = cp_model.CpSolver()
#     solver.parameters.max_time_in_seconds = 20.0
#     solver.parameters.num_search_workers = 8
#     status = solver.Solve(model)

#     status_name = solver.StatusName(status)
#     if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
#         return {
#             "status": status_name,
#             "timetable": {},
#             "message": "No feasible timetable found with these constraints. "
#                        "Try reducing hours/lab sessions or spreading staff load.",
#         }

#     timetable = {b: [[None] * periods for _ in range(days)] for b in batches}
#     for s, subj in enumerate(subjects):
#         b = subj["batch"]
#         for d in range(days):
#             for p in range(periods):
#                 if solver.Value(theory_y[s, d, p]):
#                     timetable[b][d][p] = {"subject": subj["name"], "staff": subj["staff"], "type": "theory"}
#                 if solver.Value(lab_y[s, d, p]):
#                     timetable[b][d][p] = {"subject": subj["name"], "staff": subj["staff"], "type": "lab"}

#     return {"status": status_name, "timetable": timetable, "message": "ok"}


# def main():
#     raw = sys.stdin.read()
#     data = json.loads(raw)
#     result = solve(data)
#     sys.stdout.write(json.dumps(result))


# if __name__ == "__main__":
#     main()





import sys
import json

from ortools.sat.python import cp_model

from solver_modules.model.model_loader import load_model_data
from solver_modules.model.variables import create_variables

from solver_modules.constraints.theory_constraints import (
    add_theory_constraints
)
from solver_modules.constraints.lab_constraints import (
    add_lab_constraints
)
from solver_modules.constraints.batch_constraints import (
    add_batch_constraints
)
from solver_modules.constraints.staff_constraints import (
    add_staff_constraints
)
from solver_modules.constraints.day_constraints import (
    add_day_constraints
)
from solver_modules.constraints.special_constraints import (
    add_special_subject_constraints
)
from solver_modules.constraints.resource_constraints import (
    add_resource_constraints
)
from solver_modules.constraints.library_constraints import (
    add_library_constraints
)
from solver_modules.constraints.workload_constraints import (
    add_workload_constraints
)

from solver_modules.objective.optimization import (
    add_optimization_objective
)

from solver_modules.output.timetable_formatter import (
    format_timetable
)

from solver_modules.utils.validation import (
    validate_input
)


def solve(data):

    # -------------------------------------------------
    # 1. Load and normalize input
    # -------------------------------------------------

    model_data = load_model_data(data)

    # -------------------------------------------------
    # 2. Validate input
    # -------------------------------------------------

    validate_input(model_data)

    # -------------------------------------------------
    # 3. Create CP-SAT model
    # -------------------------------------------------

    model = cp_model.CpModel()

    # -------------------------------------------------
    # 4. Create all variables
    # -------------------------------------------------

    variables = create_variables(
        model,
        model_data
    )

    # -------------------------------------------------
    # 5. Add HARD constraints
    # -------------------------------------------------

    add_theory_constraints(
        model,
        model_data,
        variables
    )

    add_lab_constraints(
        model,
        model_data,
        variables
    )

    add_batch_constraints(
        model,
        model_data,
        variables
    )

    add_staff_constraints(
        model,
        model_data,
        variables
    )

    add_day_constraints(
        model,
        model_data,
        variables
    )

    add_special_subject_constraints(
        model,
        model_data,
        variables
    )

    add_resource_constraints(
        model,
        model_data,
        variables
    )

    add_library_constraints(
        model,
        model_data,
        variables
    )

    add_workload_constraints(
        model,
        model_data,
        variables
    )

    # -------------------------------------------------
    # 6. Add optimization objective
    # -------------------------------------------------

    add_optimization_objective(
        model,
        model_data,
        variables
    )

    # -------------------------------------------------
    # 7. Create solver
    # -------------------------------------------------

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = (
        model_data["solver_time_limit_seconds"]
    )

    solver.parameters.num_search_workers = (
        model_data["solver_workers"]
    )

    solver.parameters.log_search_progress = False

    # -------------------------------------------------
    # 8. Solve
    # -------------------------------------------------

    status = solver.Solve(model)

    status_name = solver.StatusName(status)

    # -------------------------------------------------
    # 9. No solution
    # -------------------------------------------------

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):

        return {
            "status": status_name,
            "timetable": {},
            "message": (
                "No feasible timetable found with the "
                "given constraints."
            )
        }

    # -------------------------------------------------
    # 10. Format timetable
    # -------------------------------------------------

    timetable = format_timetable(
        solver,
        model_data,
        variables
    )

    return {
        "status": status_name,
        "timetable": timetable,
        "message": "Timetable generated successfully.",
        "objective_value": solver.ObjectiveValue(),
        "wall_time_seconds": solver.WallTime()
    }


def main():

    try:

        raw = sys.stdin.read()

        if not raw.strip():

            print(
                json.dumps({
                    "status": "ERROR",
                    "timetable": {},
                    "message": "No JSON input received."
                })
            )

            return

        data = json.loads(raw)

        result = solve(data)

        print(
            json.dumps(
                result,
                ensure_ascii=False
            )
        )

    except Exception as error:

        print(
            json.dumps({
                "status": "ERROR",
                "timetable": {},
                "message": str(error)
            })
        )


if __name__ == "__main__":
    main()