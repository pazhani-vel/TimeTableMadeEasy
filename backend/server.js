// const express = require("express");
// const cors = require("cors");
// const { spawn } = require("child_process");
// const path = require("path");

// const app = express();
// app.use(cors());
// app.use(express.json());

// const PYTHON_BIN = process.env.PYTHON_BIN || "python";
// const SOLVER_PATH = path.join(__dirname, "solver.py");

// app.post("/api/generate", (req, res) => {
//   const { days, periods_per_day, batches, subjects } = req.body || {};

//   if (!Array.isArray(batches) || !Array.isArray(subjects) || subjects.length === 0) {
//     return res.status(400).json({ status: "ERROR", message: "Provide at least one subject row." });
//   }

//   // Basic LTP validation before we ever spawn the solver.
//   for (const s of subjects) {
//     if (!s.name || !s.staff || !s.batch) {
//       return res.status(400).json({ status: "ERROR", message: "Every subject needs a name, batch and staff." });
//     }
//     if (!s.theory_hours || Number(s.theory_hours) <= 0) {
//       return res.status(400).json({ status: "ERROR", message: `"${s.name}" needs at least 1 lecture (L) hour/week.` });
//     }
//     if (s.has_lab) {
//       const lh = Number(s.lab_hours || 0);
//       if (lh <= 0 || lh % 2 !== 0) {
//         return res.status(400).json({
//           status: "ERROR",
//           message: `"${s.name}" has lab enabled but lab (P) hours must be a positive multiple of 2.`,
//         });
//       }
//     }
//   }

//   const payload = JSON.stringify({
//     days: days || 5,
//     periods_per_day: periods_per_day || 8,
//     batches,
//     subjects,
//   });

//   const py = spawn(PYTHON_BIN, [SOLVER_PATH]);
//   let stdout = "";
//   let stderr = "";

//   py.stdout.on("data", (chunk) => (stdout += chunk));
//   py.stderr.on("data", (chunk) => (stderr += chunk));

//   py.on("close", (code) => {
//     if (code !== 0) {
//       console.error("solver.py failed:", stderr);
//       return res.status(500).json({ status: "ERROR", message: "Solver crashed. See server logs." });
//     }
//     try {
//       const result = JSON.parse(stdout);
//       res.json(result);
//     } catch (e) {
//       console.error("Bad solver output:", stdout, stderr);
//       res.status(500).json({ status: "ERROR", message: "Solver returned invalid output." });
//     }
//   });

//   py.stdin.write(payload);
//   py.stdin.end();
// });

// const PORT = process.env.PORT || 5000;
// app.listen(PORT, () => console.log(`IT Dept Timetable API listening on http://localhost:${PORT}`));



const express = require("express");
const cors = require("cors");
const { spawn } = require("child_process");
const path = require("path");

const app = express();

app.use(cors());
app.use(express.json());


// --------------------------------------------------
// Python configuration
// --------------------------------------------------

const PYTHON_BIN =
    process.env.PYTHON_BIN || "python";

const SOLVER_PATH =
    path.join(
        __dirname,
        "solver.py"
    );


// --------------------------------------------------
// Generate timetable
// --------------------------------------------------

app.post(
    "/api/generate",
    (req, res) => {

        const data = req.body || {};

        if (
            !Array.isArray(
                data.subjects
            )
            ||
            data.subjects.length === 0
        ) {

            return res.status(400).json({
                status: "ERROR",
                timetable: {},
                message:
                    "Provide at least one subject."
            });
        }

        const payload = JSON.stringify(
            data
        );

        const python = spawn(
            PYTHON_BIN,
            [
                SOLVER_PATH
            ]
        );

        let stdout = "";
        let stderr = "";

        python.stdout.on(
            "data",
            (chunk) => {

                stdout +=
                    chunk.toString();
            }
        );

        python.stderr.on(
            "data",
            (chunk) => {

                stderr +=
                    chunk.toString();
            }
        );

        python.on(
            "error",
            (error) => {

                console.error(
                    "Python process error:",
                    error
                );

                return res.status(500).json({
                    status: "ERROR",
                    timetable: {},
                    message:
                        "Unable to start Python solver."
                });
            }
        );

        python.on(
            "close",
            (code) => {

                if (code !== 0) {

                    console.error(
                        "solver.py failed:"
                    );

                    console.error(
                        stderr
                    );

                    return res.status(500).json({
                        status: "ERROR",
                        timetable: {},
                        message:
                            "Solver process failed."
                    });
                }

                try {

                    const result =
                        JSON.parse(
                            stdout
                        );

                    console.log(result);

                    return res.json(
                        result
                    );

                } catch (error) {

                    console.error(
                        "Invalid solver output:"
                    );

                    console.error(
                        stdout
                    );

                    console.error(
                        stderr
                    );

                    return res.status(500).json({
                        status: "ERROR",
                        timetable: {},
                        message:
                            "Solver returned invalid JSON."
                    });
                }
            }
        );

        python.stdin.write(
            payload
        );

        python.stdin.end();
    }
);


// --------------------------------------------------
// Health check
// --------------------------------------------------

app.get(
    "/",
    (req, res) => {

        res.json({
            status: "OK",
            message:
                "IT Timetable Solver API is running."
        });
    }
);


// --------------------------------------------------
// Server
// --------------------------------------------------

const PORT =
    process.env.PORT || 5000;

app.listen(
    PORT,
    () => {

        console.log(
            `IT Timetable API running on port ${PORT}`
        );
    }
);