const express = require("express");

const {
    generateTimetable,
    validateTimetableInput,
    getSolverStatus
} = require("../controllers/timetableController");

const router = express.Router();


// ================================================================
// GENERATE TIMETABLE
// ================================================================
//
// POST /api/timetable/generate
//
// Sends timetable input to the Python CP-SAT solver.
//

router.post(
    "/generate",
    generateTimetable
);


// ================================================================
// VALIDATE INPUT
// ================================================================
//
// POST /api/timetable/validate
//
// Validates timetable input without running the solver.
//

router.post(
    "/validate",
    validateTimetableInput
);


// ================================================================
// SOLVER STATUS
// ================================================================
//
// GET /api/timetable/status
//
// Simple API to check whether the timetable service is available.
//

router.get(
    "/status",
    getSolverStatus
);


// ================================================================
// EXPORT ROUTER
// ================================================================

module.exports = router;