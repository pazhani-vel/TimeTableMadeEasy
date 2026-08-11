# -------------------------------------------------
# Timetable
# -------------------------------------------------

DEFAULT_DAYS = 5

DEFAULT_PERIODS_PER_DAY = 8

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]


# -------------------------------------------------
# Sessions
# -------------------------------------------------

LAB_PERIODS = 2

MORNING_END = 4

AFTERNOON_START = 4


# -------------------------------------------------
# Special subjects
# -------------------------------------------------

AUDIT_LAST_PERIODS = 2

VALID_SUBJECT_TYPES = {
    "regular",
    "naan_mudalvan",
    "audit",
    "ioc"
}


# -------------------------------------------------
# Lab types
# -------------------------------------------------

VALID_LAB_TYPES = {
    "AC",
    "NON_AC",
    "AIDS"
}


# -------------------------------------------------
# IT batches
# -------------------------------------------------

DEFAULT_IT_BATCHES = [

    {
        "id": "IT_2_B1",
        "department": "IT",
        "year": 2,
        "batch": "B1"
    },

    {
        "id": "IT_2_B2",
        "department": "IT",
        "year": 2,
        "batch": "B2"
    },

    {
        "id": "IT_3_B1",
        "department": "IT",
        "year": 3,
        "batch": "B1"
    },

    {
        "id": "IT_3_B2",
        "department": "IT",
        "year": 3,
        "batch": "B2"
    },

    {
        "id": "IT_4_B1",
        "department": "IT",
        "year": 4,
        "batch": "B1"
    },

    {
        "id": "IT_4_B2",
        "department": "IT",
        "year": 4,
        "batch": "B2"
    }
]


# -------------------------------------------------
# Solver
# -------------------------------------------------

DEFAULT_SOLVER_TIME_LIMIT = (
    6 * 60 * 60
)

DEFAULT_SOLVER_WORKERS = 8