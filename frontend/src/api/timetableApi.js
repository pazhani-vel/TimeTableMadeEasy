const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:5000/api/timetable/generate";


export async function generateTimetable(payload) {
  try {
    const response = await fetch(API_BASE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        status: "ERROR",
        timetable: {},
        message: data.message || `Server returned HTTP ${response.status}`,
      };
    }

    console.log("TIMETABLE RESPONSE:", data);
    return transformResponse(data);

  } catch (error) {
    console.error("Timetable API Request Error:", error);
    return {
      success: false,
      status: "ERROR",
      timetable: {},
      message: "Unable to connect to the Timetable Solver backend. Please check that the server is running.",
    };
  }
}


/*
 * Transform backend array response to frontend keyed object.
 *
 * Backend: { success, data: [{ batch, days: [{ day, periods: [{period, type, subject, faculty}] }] }] }
 * Frontend: { status, timetable: { "batch_name": [[cell, ...], ...] } }
 */
function transformResponse(backendResponse) {
  const timetableArray = backendResponse.data || backendResponse.timetable || [];
  const timetable = {};

  timetableArray.forEach((batchEntry) => {
    const batchName = batchEntry.batch || "Unknown Batch";
    const daysArray = (batchEntry.days || []).map(
      (dayEntry) => convertPeriods(dayEntry.periods || [])
    );
    timetable[batchName] = daysArray;
  });

  let status = "UNKNOWN";
  if (backendResponse.success) {
    status = backendResponse.status || "FEASIBLE";
  } else if (backendResponse.status) {
    status = backendResponse.status;
  }

  return {
    success: backendResponse.success !== false,
    status,
    timetable,
    validation: backendResponse.validation || null,
    message: backendResponse.message || "",
  };
}


/*
 * Convert 1-indexed period objects to 0-indexed array.
 * Also maps "faculty" field to "staff" for frontend compatibility.
 */
function convertPeriods(periods) {
  const maxPeriod = Math.max(...periods.map((p) => p.period || 0), 8);
  const result = new Array(maxPeriod).fill(null);

  periods.forEach((period) => {
    const index = (period.period || 1) - 1;
    if (index >= 0 && index < maxPeriod) {
      result[index] = {
        subject: period.subject || null,
        staff: period.faculty || period.staff || null,
        type: period.type || "free",
        lab: period.type === "lab" ? period.subject : undefined,
      };
    }
  });

  return result;
}
