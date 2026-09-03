const path = require("path");
const { spawn } = require("child_process");


// ================================================================
// PYTHON CONFIGURATION
// ================================================================

const PYTHON_COMMAND =
    process.env.PYTHON_COMMAND || "python";


// ================================================================
// SOLVER PATH
// ================================================================

const SOLVER_DIRECTORY = path.join(
    __dirname,
    "..",
    "solver"
);

const MAIN_PY = path.join(
    SOLVER_DIRECTORY,
    "main.py"
);


// ================================================================
// GENERATE TIMETABLE
// ================================================================

const generateTimetable = async (
    req,
    res
) => {

    try {

        const inputData = req.body;


        // ========================================================
        // BASIC REQUEST VALIDATION
        // ========================================================

        if (
            !inputData ||
            typeof inputData !== "object" ||
            Array.isArray(inputData)
        ) {

            return res.status(400).json({
                success: false,
                message: "Invalid timetable input."
            });

        }


        // ========================================================
        // RUN PYTHON SOLVER
        // ========================================================

        const result =
            await runPythonSolver(
                inputData
            );


        // ========================================================
        // SOLVER FAILED
        // ========================================================

        if (!result.success) {

            return res.status(
                result.statusCode || 500
            ).json({
                success: false,
                message: result.message,
                error: result.error || null
            });

        }


        // ========================================================
        // RETURN TIMETABLE
        // ========================================================

        return res.status(200).json({
            success: true,
            message:
                result.message ||
                "Timetable generated successfully.",

            data: result.data,

            solver: result.solver || null,

            validation: result.validation || null
        });

    }

    catch (error) {

        console.error(
            "Generate timetable error:",
            error
        );

        return res.status(500).json({
            success: false,
            message:
                "Failed to generate timetable.",
            error: error.message
        });

    }

};


// ================================================================
// VALIDATE TIMETABLE INPUT
// ================================================================

const validateTimetableInput = async (
    req,
    res
) => {

    try {

        const inputData = req.body;


        // ========================================================
        // BASIC VALIDATION
        // ========================================================

        if (
            !inputData ||
            typeof inputData !== "object" ||
            Array.isArray(inputData)
        ) {

            return res.status(400).json({
                success: false,
                message: "Invalid timetable input."
            });

        }


        // ========================================================
        // RUN PYTHON VALIDATION MODE
        // ========================================================

        const result =
            await runPythonSolver(
                inputData,
                "validate"
            );


        // ========================================================
        // RETURN VALIDATION RESULT
        // ========================================================

        if (!result.success) {

            return res.status(
                result.statusCode || 400
            ).json({
                success: false,
                message: result.message,
                validation:
                    result.validation || null,
                error:
                    result.error || null
            });

        }


        return res.status(200).json({
            success: true,
            message:
                "Timetable input is valid.",

            validation:
                result.validation || null
        });

    }

    catch (error) {

        console.error(
            "Validation error:",
            error
        );

        return res.status(500).json({
            success: false,
            message:
                "Failed to validate timetable input.",
            error: error.message
        });

    }

};


// ================================================================
// SOLVER STATUS
// ================================================================

const getSolverStatus = (
    req,
    res
) => {

    return res.status(200).json({
        success: true,

        service:
            "timetable-generator",

        python:
            PYTHON_COMMAND,

        solver:
            "OR-Tools CP-SAT",

        status:
            "available"
    });

};


// ================================================================
// RUN PYTHON SOLVER
// ================================================================

const runPythonSolver = (
    inputData,
    mode = "generate"
) => {

    return new Promise(
        (
            resolve,
            reject
        ) => {

            // ====================================================
            // PYTHON ARGUMENTS
            // ====================================================

            const args = [
                MAIN_PY
            ];


            // ====================================================
            // OPTIONAL VALIDATION MODE
            // ====================================================

            if (
                mode === "validate"
            ) {

                args.push(
                    "--validate-only"
                );

            }


            // ====================================================
            // START PYTHON
            // ====================================================

            const pythonProcess =
                spawn(
                    PYTHON_COMMAND,
                    args,
                    {
                        cwd:
                            SOLVER_DIRECTORY,

                        env: {
                            ...process.env,
                            PYTHONUNBUFFERED:
                                "1"
                        }
                    }
                );


            // ====================================================
            // OUTPUT
            // ====================================================

            let stdout = "";
            let stderr = "";


            // ====================================================
            // PYTHON STDOUT
            // ====================================================

            pythonProcess.stdout.on(
                "data",
                (data) => {

                    stdout +=
                        data.toString();

                }
            );


            // ====================================================
            // PYTHON STDERR
            // ====================================================

            pythonProcess.stderr.on(
                "data",
                (data) => {

                    stderr +=
                        data.toString();

                }
            );


            // ====================================================
            // PYTHON PROCESS ERROR
            // ====================================================

            pythonProcess.on(
                "error",
                (error) => {

                    reject(
                        new Error(
                            `Failed to start Python solver: ${error.message}`
                        )
                    );

                }
            );


            // ====================================================
            // PROCESS COMPLETED
            // ====================================================

            pythonProcess.on(
                "close",
                (code) => {

                    // ============================================
                    // NO OUTPUT
                    // ============================================

                    if (
                        !stdout.trim()
                    ) {

                        resolve({
                            success: false,

                            statusCode:
                                code === 0
                                    ? 500
                                    : 500,

                            message:
                                "Python solver returned no output.",

                            error:
                                stderr.trim() ||
                                `Python process exited with code ${code}.`
                        });

                        return;
                    }


                    // ============================================
                    // PARSE JSON
                    // ============================================

                    let result;

                    try {

                        result =
                            JSON.parse(
                                stdout
                            );

                    }

                    catch (error) {

                        resolve({
                            success: false,

                            statusCode: 500,

                            message:
                                "Python solver returned invalid JSON.",

                            error: (
                                stderr.trim() ||
                                stdout.trim()
                            )
                        });

                        return;
                    }


                    // ============================================
                    // PYTHON REPORTED FAILURE
                    // ============================================

                    if (
                        code !== 0 ||
                        result.success === false
                    ) {

                        resolve({
                            success: false,

                            statusCode:
                                getStatusCode(
                                    result
                                ),

                            message:
                                result.message ||
                                "Timetable solver failed.",

                            error:
                                result.error ||
                                stderr.trim() ||
                                null,

                            validation:
                                result.validation ||
                                null
                        });

                        return;
                    }


                    // ============================================
                    // SUCCESS
                    // ============================================

                    resolve({
                        success: true,

                        message:
                            result.message ||
                            "Solver completed successfully.",

                        data:
                            result.data ||
                            result.timetable ||
                            null,

                        solver:
                            result.solver ||
                            null,

                        validation:
                            result.validation ||
                            null
                    });

                }
            );

            // ====================================================
            // SEND JSON TO PYTHON STDIN
            // ====================================================

            pythonProcess.stdin.write(
                JSON.stringify(
                    inputData
                )
            );

            pythonProcess.stdin.end();

        }
    );

};


// ================================================================
// DETERMINE HTTP STATUS CODE
// ================================================================

const getStatusCode = (
    result
) => {

    // ------------------------------------------------------------
    // Input error
    // ------------------------------------------------------------

    if (
        result.type === "VALIDATION_ERROR"
    ) {

        return 400;

    }


    // ------------------------------------------------------------
    // Infeasible timetable
    // ------------------------------------------------------------

    if (
        result.status === "INFEASIBLE" ||
        result.solver?.status === "INFEASIBLE"
    ) {

        return 422;

    }


    // ------------------------------------------------------------
    // Default
    // ------------------------------------------------------------

    return 500;

};


// ================================================================
// EXPORT
// ================================================================

module.exports = {
    generateTimetable,
    validateTimetableInput,
    getSolverStatus
};