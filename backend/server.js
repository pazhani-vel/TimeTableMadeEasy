const express = require("express");
const cors = require("cors");
const path = require("path");
require("dotenv").config();

const timetableRoutes = require("./routes/timetableRoutes");


// ================================================================
// CREATE EXPRESS APP
// ================================================================

const app = express();


// ================================================================
// PORT
// ================================================================

const PORT = process.env.PORT || 5000;


// ================================================================
// MIDDLEWARE
// ================================================================

// ---------------------------------------------------------------
// CORS
// ---------------------------------------------------------------

app.use(
    cors({
        origin: process.env.FRONTEND_URL || "*",
        methods: [
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS"
        ],
        allowedHeaders: [
            "Content-Type",
            "Authorization"
        ]
    })
);


// ---------------------------------------------------------------
// JSON BODY PARSER
// ---------------------------------------------------------------

app.use(
    express.json({
        limit: "10mb"
    })
);


// ---------------------------------------------------------------
// URL ENCODED DATA
// ---------------------------------------------------------------

app.use(
    express.urlencoded({
        extended: true,
        limit: "10mb"
    })
);


// ================================================================
// HEALTH CHECK
// ================================================================

app.get(
    "/",
    (req, res) => {

        res.status(200).json({
            success: true,
            message: "Timetable backend is running.",
            service: "timetable-generator",
            timestamp: new Date().toISOString()
        });

    }
);


// ================================================================
// API HEALTH CHECK
// ================================================================

app.get(
    "/api/health",
    (req, res) => {

        res.status(200).json({
            success: true,
            message: "API is healthy.",
            timestamp: new Date().toISOString()
        });

    }
);


// ================================================================
// TIMETABLE ROUTES
// ================================================================

app.use(
    "/api/timetable",
    timetableRoutes
);


// ================================================================
// 404 HANDLER
// ================================================================

app.use(
    (req, res) => {

        res.status(404).json({
            success: false,
            message: "Route not found.",
            path: req.originalUrl
        });

    }
);


// ================================================================
// GLOBAL ERROR HANDLER
// ================================================================

app.use(
    (err, req, res, next) => {

        console.error(
            "Server Error:",
            err
        );

        const statusCode =
            err.statusCode || 500;

        res.status(
            statusCode
        ).json({
            success: false,
            message:
                err.message ||
                "Internal server error."
        });

    }
);


// ================================================================
// START SERVER
// ================================================================

const server = app.listen(
    PORT,
    () => {

        console.log(
            "================================================"
        );

        console.log(
            `Timetable backend running on port ${PORT}`
        );

        console.log(
            `http://localhost:${PORT}`
        );

        console.log(
            `Timetable API: http://localhost:${PORT}/api/timetable`
        );

        console.log(
            "================================================"
        );

    }
);


// ================================================================
// GRACEFUL SHUTDOWN
// ================================================================

process.on(
    "SIGINT",
    () => {

        console.log(
            "\nShutting down server..."
        );

        server.close(
            () => {

                console.log(
                    "Server closed."
                );

                process.exit(0);

            }
        );

    }
);


process.on(
    "SIGTERM",
    () => {

        console.log(
            "\nSIGTERM received."
        );

        server.close(
            () => {

                console.log(
                    "Server closed."
                );

                process.exit(0);

            }
        );

    }
);