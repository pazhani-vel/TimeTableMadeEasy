import React from "react";
import { DEFAULT_STAFF, YEARS, BATCH_OPTIONS } from "../constants/academicData";
import BatchStatsCard from "./BatchStatsCard";
import coursesData from "../constants/courses.json";

// Map academic year → semesters (2nd Year = sem 3-4, 3rd = sem 5-6, 4th = sem 7-8)
const YEAR_TO_SEMESTERS = {
  2: [3, 4],
  3: [5, 6],
  4: [7, 8],
};

function getCoursesForYear(year) {
  const semesters = YEAR_TO_SEMESTERS[Number(year)] || [];
  return coursesData.courses.filter((c) => semesters.includes(c.semester));
}

export default function SubjectConfigTable({
  year,
  batch,
  batchId,
  rows,
  updateRow,
  removeRow,
  addRow,
  days,
  periods,
}) {
  const currentBatchId = batchId || `IT_${year}_${batch}`;
  const yearCourses = getCoursesForYear(year);

  const batchRows = rows
    .map((r, i) => ({ ...r, originalIndex: i }))
    .filter((r) => {
      if (r.batch_id) return r.batch_id === currentBatchId;
      return Number(r.year) === Number(year) && r.batch === batch;
    });

  const yearLabel =
    YEARS.find((y) => y.value === Number(year))?.label || `${year}th Year`;

  // When user picks a course from the dropdown, auto-fill hours & credits
  const handleCourseSelect = (idx, subCode) => {
    const course = coursesData.courses.find((c) => c.sub_code === subCode);
    if (!course) return;

    const { lecture, practical, credits } = course.ltpc;
    updateRow(idx, "name", course.sub_name);
    updateRow(idx, "sub_code", course.sub_code);
    updateRow(idx, "theory_hours", lecture > 0 ? lecture : 1);
    updateRow(idx, "has_lab", practical > 0);
    updateRow(idx, "lab_hours", practical > 0 ? (practical % 2 === 0 ? practical : practical + 1) : 0);
    updateRow(idx, "lab_type", practical > 0 ? "AC" : null);
    updateRow(idx, "credits", credits);
  };

  return (
    <div className="batch-card">
      <div className="batch-card-header">
        <div className="batch-title-wrap">
          <div
            className={`batch-icon-badge batch-icon-${
              batch?.toLowerCase() || "b1"
            }`}
          >
            {yearLabel} — Batch {batch}
          </div>
          <div>
            <h3 className="batch-title">
              {yearLabel} (Batch {batch}) Curriculum &amp; Faculty Allocation
            </h3>
            <p className="batch-subtitle">
              Select courses from the official syllabus for{" "}
              <strong>{currentBatchId}</strong> and assign faculty
            </p>
          </div>
        </div>

        <BatchStatsCard
          batchId={currentBatchId}
          year={year}
          batch={batch}
          rows={rows}
          days={days}
          periods={periods}
        />
      </div>

      <div className="subject-table-wrap">
        <table className="subject-table">
          <thead>
            <tr>
              <th style={{ width: "5%" }}>Code</th>
              <th style={{ width: "22%" }}>Course Name</th>
              <th style={{ width: "8%" }}>Year</th>
              <th style={{ width: "8%" }}>Batch</th>
              <th style={{ width: "20%" }}>Faculty / Staff</th>
              <th style={{ width: "7%", textAlign: "center" }}>L hrs/wk</th>
              <th style={{ width: "6%", textAlign: "center" }}>Credits</th>
              <th style={{ width: "6%", textAlign: "center" }}>Lab?</th>
              <th style={{ width: "12%" }}>P hrs / Type</th>
              <th style={{ width: "2%" }}></th>
            </tr>
          </thead>
          <tbody>
            {batchRows.length === 0 ? (
              <tr>
                <td colSpan="10" className="empty-table-msg">
                  No courses added for {yearLabel} - Batch {batch}. Click "Add
                  Course" below or load a preset.
                </td>
              </tr>
            ) : (
              batchRows.map((r) => {
                const idx = r.originalIndex;
                const isLabInvalid =
                  r.has_lab &&
                  (Number(r.lab_hours) <= 0 ||
                    Number(r.lab_hours) % 2 !== 0);

                return (
                  <tr key={idx} className="subject-row">
                    {/* Sub Code — read-only display */}
                    <td>
                      <span
                        className="text-xs text-muted"
                        style={{
                          fontFamily: "monospace",
                          fontSize: "0.75rem",
                          display: "block",
                          padding: "4px",
                        }}
                      >
                        {r.sub_code || "—"}
                      </span>
                    </td>

                    {/* Course Name Dropdown */}
                    <td>
                      <select
                        className="form-control"
                        value={r.sub_code || ""}
                        onChange={(e) =>
                          handleCourseSelect(idx, e.target.value)
                        }
                        style={{ fontSize: "0.82rem" }}
                      >
                        <option value="">— Select Course —</option>
                        {yearCourses.map((c) => (
                          <option key={c.sub_code} value={c.sub_code}>
                            [{c.sub_code}] {c.sub_name}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Year selector */}
                    <td>
                      <select
                        className="form-control"
                        value={r.year}
                        onChange={(e) => {
                          const newYear = Number(e.target.value);
                          updateRow(idx, "year", newYear);
                          updateRow(
                            idx,
                            "batch_id",
                            `IT_${newYear}_${r.batch}`
                          );
                          // Clear course selection on year change
                          updateRow(idx, "sub_code", "");
                          updateRow(idx, "name", "");
                        }}
                      >
                        {YEARS.map((y) => (
                          <option key={y.value} value={y.value}>
                            {y.label}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Batch selector */}
                    <td>
                      <select
                        className="form-control"
                        value={r.batch}
                        onChange={(e) => {
                          const newBatch = e.target.value;
                          updateRow(idx, "batch", newBatch);
                          updateRow(
                            idx,
                            "batch_id",
                            `IT_${r.year}_${newBatch}`
                          );
                        }}
                      >
                        {BATCH_OPTIONS.map((b) => (
                          <option key={b.value} value={b.value}>
                            {b.label}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Faculty */}
                    <td>
                      <select
                        className="form-control"
                        value={r.staff}
                        onChange={(e) =>
                          updateRow(idx, "staff", e.target.value)
                        }
                      >
                        {DEFAULT_STAFF.map((name) => (
                          <option key={name} value={name}>
                            {name}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Lecture hours */}
                    <td>
                      <input
                        type="number"
                        min="1"
                        max="10"
                        className="form-control text-center"
                        value={r.theory_hours}
                        onChange={(e) =>
                          updateRow(idx, "theory_hours", e.target.value)
                        }
                      />
                    </td>

                    {/* Credits — editable */}
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        className="form-control text-center"
                        value={r.credits ?? ""}
                        placeholder="—"
                        onChange={(e) =>
                          updateRow(idx, "credits", e.target.value)
                        }
                        title="Credits"
                      />
                    </td>

                    {/* Has Lab checkbox */}
                    <td className="text-center">
                      <label className="checkbox-wrap">
                        <input
                          type="checkbox"
                          checked={r.has_lab}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            updateRow(idx, "has_lab", checked);
                            if (checked && !r.lab_type) {
                              updateRow(idx, "lab_type", "AC");
                            }
                          }}
                        />
                        <span className="checkbox-custom"></span>
                        <span className="checkbox-label">Lab</span>
                      </label>
                    </td>

                    {/* Lab hours + lab type */}
                    <td>
                      <div
                        style={{ display: "flex", gap: "4px" }}
                      >
                        <input
                          type="number"
                          min="2"
                          max="8"
                          step="2"
                          disabled={!r.has_lab}
                          className={`form-control text-center ${
                            isLabInvalid ? "input-error" : ""
                          }`}
                          value={r.has_lab ? r.lab_hours : ""}
                          onChange={(e) =>
                            updateRow(idx, "lab_hours", e.target.value)
                          }
                          placeholder={r.has_lab ? "2,4…" : "—"}
                          style={{ width: "52px" }}
                        />
                        {r.has_lab && (
                          <select
                            className="form-control"
                            value={r.lab_type || "AC"}
                            onChange={(e) =>
                              updateRow(idx, "lab_type", e.target.value)
                            }
                            style={{ padding: "2px 4px", fontSize: "0.78rem" }}
                          >
                            <option value="AC">AC Lab</option>
                            <option value="NON_AC">Non-AC</option>
                          </select>
                        )}
                      </div>
                    </td>

                    {/* Remove */}
                    <td className="text-center">
                      <button
                        className="btn-icon-danger"
                        title="Remove Course"
                        onClick={() => removeRow(idx)}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="batch-card-footer">
        <button
          className="btn btn-secondary btn-sm"
          onClick={() =>
            addRow({
              year: Number(year),
              batch,
              batch_id: currentBatchId,
            })
          }
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Course for {yearLabel} - Batch {batch}
        </button>
      </div>
    </div>
  );
}
