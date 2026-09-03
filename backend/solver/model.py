from ortools.sat.python import cp_model


class TimetableModel:
    """
    Central CP-SAT model for timetable generation.

    This class:
        1. Creates the OR-Tools model.
        2. Stores input data.
        3. Creates all timetable decision variables.
        4. Provides a common structure for all constraint files.

    Constraint files should NOT create their own CP-SAT model.
    They should use:

        timetable.model

    and the variables created here.
    """

    def __init__(self, data):

        # =========================================================
        # OR-TOOLS MODEL
        # =========================================================

        self.model = cp_model.CpModel()

        # =========================================================
        # ORIGINAL INPUT
        # =========================================================

        self.data = data or {}

        # =========================================================
        # BASIC DATA
        # =========================================================

        self.subjects = self.data.get(
            "subjects",
            []
        )

        self.batches = self.data.get(
            "batches",
            []
        )

        self.faculties = self.data.get(
            "faculties",
            []
        )

        self.staff = self.data.get(
            "staff",
            self.faculties
        )

        self.labs = self.data.get(
            "labs",
            []
        )

        self.rooms = self.data.get(
            "rooms",
            []
        )

        # =========================================================
        # DAYS
        # =========================================================

        self.days = self.data.get(
            "days",
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ]
        )

        self.num_days = len(
            self.days
        )

        # =========================================================
        # PERIODS
        # =========================================================

        self.periods = self.data.get(
            "periods",
            []
        )

        # ---------------------------------------------------------
        # If periods are supplied as a number:
        #
        # "periods": 8
        #
        # create:
        #
        # P1 ... P8
        # ---------------------------------------------------------

        if isinstance(
            self.periods,
            int
        ):

            self.num_periods = (
                self.periods
            )

            self.periods = [
                f"P{i + 1}"
                for i in range(
                    self.num_periods
                )
            ]

        else:

            self.num_periods = len(
                self.periods
            )

        # ---------------------------------------------------------
        # Default if nothing is supplied.
        # ---------------------------------------------------------

        if self.num_periods == 0:

            self.num_periods = 8

            self.periods = [
                f"P{i + 1}"
                for i in range(8)
            ]

        # =========================================================
        # DECISION VARIABLES
        # =========================================================
        self.theory_y = {}
        self.lab_y = {}

        # Faculty/staff teaching variables
        self.staff_teach = {}

        # Theory constraint helper variables
        self.day_used = {}
        self.theory_block_start = {}

        self.naan_mudalvan = {}

        self.audit = {}

        self.ioc = {}

        self.lab_assignment = {}

        self.room_assignment = {}

        self.lab_start = {}

        # =========================================================
        # CREATE VARIABLES
        # =========================================================

        self._create_subject_variables()

        self._create_theory_helper_variables()

        self._create_lab_helper_variables()

        self._create_special_variables()

        self._create_resource_variables()

        self._create_staff_teach_variables()

        

    # =============================================================
    # SUBJECT VARIABLES
    # =============================================================

    # =============================================================
# THEORY HELPER VARIABLES
# =============================================================

    def _create_theory_helper_variables(self):
        """
        Create helper variables required by theory constraints.

        day_used[s,b,d]:
            1 if subject s is scheduled for theory
            for batch b on day d.

        theory_block_start[s,b,d,p]:
            1 if the theory block starts at period p.
        """

        for s in range(len(self.subjects)):

            for b in range(len(self.batches)):

                for d in range(self.num_days):

                    # ------------------------------------------------
                    # Whether subject uses this day
                    # ------------------------------------------------

                    self.day_used[
                        s, b, d
                    ] = self.model.NewBoolVar(
                        f"day_used"
                        f"_s{s}"
                        f"_b{b}"
                        f"_d{d}"
                    )

                    # ------------------------------------------------
                    # Theory block starting at each period
                    # ------------------------------------------------

                    for p in range(self.num_periods):

                        self.theory_block_start[
                            s, b, d, p
                        ] = self.model.NewBoolVar(
                            f"theory_block_start"
                            f"_s{s}"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )

    def _create_lab_helper_variables(self):
        """
        Create helper variables required by lab constraints.

        lab_start[s,b,d,p]:
            1 if a lab session starts at period p.

        A lab requires two consecutive periods, so a lab
        cannot start at the final period.
        """

        for s in range(len(self.subjects)):

            for b in range(len(self.batches)):

                for d in range(self.num_days):

                    for p in range(self.num_periods):

                        self.lab_start[
                            s, b, d, p
                        ] = self.model.NewBoolVar(
                            f"lab_start"
                            f"_s{s}"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )

                        # Last period cannot be the start
                        # of a two-period laboratory session.
                        if p == self.num_periods - 1:

                            self.model.Add(
                                self.lab_start[
                                    s, b, d, p
                                ] == 0
                            )

    def _create_subject_variables(self):
        """
        Create variables for normal theory/lab classes.

        theory_y[s,b,d,p]

            = 1
            if subject s is a theory class for batch b
            on day d / period p.

        lab_y[s,b,d,p]

            = 1
            if subject s is a lab class for batch b
            on day d / period p.
        """

        for s in range(
            len(self.subjects)
        ):

            for b in range(
                len(self.batches)
            ):

                for d in range(
                    self.num_days
                ):

                    for p in range(
                        self.num_periods
                    ):

                        self.theory_y[
                            s, b, d, p
                        ] = self.model.NewBoolVar(
                            (
                                f"theory"
                                f"_s{s}"
                                f"_b{b}"
                                f"_d{d}"
                                f"_p{p}"
                            )
                        )

                        self.lab_y[
                            s, b, d, p
                        ] = self.model.NewBoolVar(
                            (
                                f"lab"
                                f"_s{s}"
                                f"_b{b}"
                                f"_d{d}"
                                f"_p{p}"
                            )
                        )

    def _create_staff_teach_variables(self):
        """
        staff_teach[staff, batch, day, period] = 1
        if the staff member teaches that batch at that time.
        """

        for st in range(len(self.staff)):

            for b in range(len(self.batches)):

                for d in range(self.num_days):

                    for p in range(self.num_periods):

                        self.staff_teach[
                            st, b, d, p
                        ] = self.model.NewBoolVar(
                            (
                                f"staff_teach"
                                f"_st{st}"
                                f"_b{b}"
                                f"_d{d}"
                                f"_p{p}"
                            )
                        )

    # =============================================================
    # SPECIAL VARIABLES
    # =============================================================

    def _create_special_variables(self):
        """
        Create variables for special activities.

        Naan Mudalvan
        Audit
        IOC
        """

        for b in range(
            len(self.batches)
        ):

            for d in range(
                self.num_days
            ):

                for p in range(
                    self.num_periods
                ):

                    self.naan_mudalvan[
                        b, d, p
                    ] = self.model.NewBoolVar(
                        (
                            f"naan_mudalvan"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )
                    )

                    self.audit[
                        b, d, p
                    ] = self.model.NewBoolVar(
                        (
                            f"audit"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )
                    )

                    self.ioc[
                        b, d, p
                    ] = self.model.NewBoolVar(
                        (
                            f"ioc"
                            f"_b{b}"
                            f"_d{d}"
                            f"_p{p}"
                        )
                    )

    # =============================================================
    # LAB ASSIGNMENT VARIABLES
    # =============================================================

    def _create_resource_variables(self):
        """
        Create laboratory/room assignment variables.

        These are created only when resources exist.
        """

        if not self.labs:
            return

        for s in range(
            len(self.subjects)
        ):

            if not is_lab_subject(
                self.subjects[s]
            ):
                continue

            for b in range(
                len(self.batches)
            ):

                for d in range(
                    self.num_days
                ):

                    # ------------------------------------------------
                    # A lab normally occupies two consecutive periods.
                    # ------------------------------------------------

                    for p in range(
                        self.num_periods - 1
                    ):

                        for l in range(
                            len(self.labs)
                        ):

                            self.lab_assignment[
                                s,
                                b,
                                d,
                                p,
                                l
                            ] = self.model.NewBoolVar(
                                (
                                    f"lab_assign"
                                    f"_s{s}"
                                    f"_b{b}"
                                    f"_d{d}"
                                    f"_p{p}"
                                    f"_l{l}"
                                )
                            )

    # =============================================================
    # ROOM VARIABLES
    # =============================================================

    def create_room_variables(self):
        """
        Create optional room assignment variables.

        This is separated from the initial resource creation so
        room assignment can be enabled only when required.
        """

        if not self.rooms:
            return

        for s in range(
            len(self.subjects)
        ):

            for b in range(
                len(self.batches)
            ):

                for d in range(
                    self.num_days
                ):

                    for p in range(
                        self.num_periods
                    ):

                        for r in range(
                            len(self.rooms)
                        ):

                            self.room_assignment[
                                s,
                                b,
                                d,
                                p,
                                r
                            ] = self.model.NewBoolVar(
                                (
                                    f"room_assign"
                                    f"_s{s}"
                                    f"_b{b}"
                                    f"_d{d}"
                                    f"_p{p}"
                                    f"_r{r}"
                                )
                            )

    # =============================================================
    # GETTERS
    # =============================================================

    def get_theory_variable(
        self,
        subject,
        batch,
        day,
        period
    ):

        return self.theory_y[
            subject,
            batch,
            day,
            period
        ]

    def get_lab_variable(
        self,
        subject,
        batch,
        day,
        period
    ):

        return self.lab_y[
            subject,
            batch,
            day,
            period
        ]

    # =============================================================
    # SUBJECT INFORMATION
    # =============================================================

    def subject_name(
        self,
        index
    ):

        subject = self.subjects[
            index
        ]

        if isinstance(
            subject,
            dict
        ):

            return (
                subject.get("name")
                or subject.get("subject_name")
                or subject.get("code")
                or f"Subject {index + 1}"
            )

        return str(subject)

    # =============================================================
    # BATCH INFORMATION
    # =============================================================

    def batch_name(
        self,
        index
    ):

        batch = self.batches[
            index
        ]

        if isinstance(
            batch,
            dict
        ):

            return (
                batch.get("name")
                or batch.get("batch_name")
                or batch.get("code")
                or f"Batch {index + 1}"
            )

        return str(batch)

    # =============================================================
    # FACULTY INFORMATION
    # =============================================================

    def faculty_name(
        self,
        index
    ):

        faculty = self.faculties[
            index
        ]

        if isinstance(
            faculty,
            dict
        ):

            return (
                faculty.get("name")
                or faculty.get("faculty_name")
                or faculty.get("id")
                or f"Faculty {index + 1}"
            )

        return str(faculty)

    # =============================================================
    # LAB INFORMATION
    # =============================================================

    def lab_name(
        self,
        index
    ):

        lab = self.labs[
            index
        ]

        if isinstance(
            lab,
            dict
        ):

            return (
                lab.get("name")
                or lab.get("lab_name")
                or lab.get("code")
                or f"Lab {index + 1}"
            )

        return str(lab)


# =================================================================
# HELPER
# =================================================================

def is_lab_subject(subject):
    """
    Determine whether a subject contains a lab component.

    Supported examples:

        {
            "type": "lab"
        }

        {
            "is_lab": true
        }

        {
            "lab_periods": 2
        }

        {
            "lab_hours": 2
        }
    """

    if not isinstance(
        subject,
        dict
    ):
        return False

    if subject.get(
        "is_lab",
        False
    ):
        return True

    subject_type = str(
        subject.get(
            "type",
            ""
        )
    ).lower()

    if subject_type in (
        "lab",
        "laboratory",
        "practical"
    ):
        return True

    lab_periods = (
        subject.get(
            "lab_periods"
        )
        or
        subject.get(
            "lab_hours"
        )
    )

    try:

        return int(
            lab_periods or 0
        ) > 0

    except (
        TypeError,
        ValueError
    ):

        return False


# =================================================================
# BUILD FUNCTION
# =================================================================

def build_model(data):
    """
    Convenience function used by main.py.

    Example:

        timetable = build_model(data)

    """

    return TimetableModel(
        data
    )