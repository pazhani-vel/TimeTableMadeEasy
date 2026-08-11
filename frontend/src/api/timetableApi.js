const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api/generate";

/**
 * Sends timetable generation payload to backend Express/CP-SAT solver service.
 * @param {Object} payload Payload conforming to backend model expectations.
 * @returns {Promise<Object>} Backend response JSON
 */
export async function generateTimetable(payload) {
  try {
    const response = await fetch(API_BASE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        status: "ERROR",
        timetable: {},
        message:
          data.message ||
          `Server returned HTTP ${response.status}: ${response.statusText}`,
      };
    }
    console.log(data);
    return data;
  } catch (error) {
    console.error("Timetable API Request Error:", error);
    return {
      status: "ERROR",
      timetable: {},
      message:
        "Unable to connect to the Timetable Solver backend. Please check that the server is running on port 5000.",
    };
  }
}
