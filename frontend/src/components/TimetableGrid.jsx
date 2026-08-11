import React, { useState } from "react";
import { PERIOD_TIME_SLOTS, YEARS, BATCH_OPTIONS } from "../constants/academicData";

export default function TimetableGrid({
  result,
  selectedYear: initialYear = 2,
  selectedBatch: initialBatch = "B1",
  periods = 8,
}) {
  const [currentYear, setCurrentYear] = useState(initialYear);
  const [currentBatch, setCurrentBatch] = useState(initialBatch);
  const [viewMode, setViewMode] = useState("SINGLE"); // "SINGLE" | "ALL"

  if (!result || !result.timetable) return null;

  const periodsCount = Number(periods) || 8;
  const half = Math.floor(periodsCount / 2);

  // Construct table column headers with lunch gap
  const displayCols = [];
  for (let p = 0; p < periodsCount; p++) {
    const slotInfo = PERIOD_TIME_SLOTS.find((s) => !s.lunch && s.index === p) || {
      index: p,
      label: `P${p + 1}`,
      time: "",
    };
    displayCols.push({ ...slotInfo, isLunch: false });

    // Insert lunch column after first half of periods
    if (p === half - 1) {
      displayCols.push({
        isLunch: true,
        label: "LUNCH BREAK",
        time: "12:05 – 01:00 PM",
      });
    }
  }

  const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  // Determine which batch IDs to render
  const selectedBatchId = `IT_${currentYear}_${currentBatch}`;
  
  const batchesToDisplay =
    viewMode === "ALL"
      ? Object.keys(result.timetable)
      : [selectedBatchId];

  return (
    <div className="timetable-section">
      <div className="section-header">
        <div>
          <h2>Generated Department Timetable</h2>
          <p>
            CP-SAT Solver Status:{" "}
            <span className="status-tag status-tag-success">
              {result.status}
            </span>
            {result.wall_time_seconds && (
              <span className="text-muted text-sm ml-2">
                (Solved in {Number(result.wall_time_seconds).toFixed(2)}s)
              </span>
            )}
          </p>
        </div>

        {/* Year and Batch Selectors for Timetable View */}
        <div className="timetable-controls" style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div className="control-group" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <label className="text-sm font-semibold">Year:</label>
            <select
              className="form-control text-sm"
              value={currentYear}
              onChange={(e) => {
                setCurrentYear(Number(e.target.value));
                setViewMode("SINGLE");
              }}
              style={{ padding: "4px 8px", width: "auto" }}
            >
              {YEARS.map((y) => (
                <option key={y.value} value={y.value}>
                  {y.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <label className="text-sm font-semibold">Batch:</label>
            <select
              className="form-control text-sm"
              value={currentBatch}
              onChange={(e) => {
                setCurrentBatch(e.target.value);
                setViewMode("SINGLE");
              }}
              style={{ padding: "4px 8px", width: "auto" }}
            >
              {BATCH_OPTIONS.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label}
                </option>
              ))}
            </select>
          </div>

          <div className="tab-switcher">
            <button
              className={`tab-btn ${viewMode === "SINGLE" ? "active" : ""}`}
              onClick={() => setViewMode("SINGLE")}
            >
              Selected Timetable ({currentYear}nd/rd/th Yr {currentBatch})
            </button>
            <button
              className={`tab-btn ${viewMode === "ALL" ? "active" : ""}`}
              onClick={() => setViewMode("ALL")}
            >
              All 6 Schedules Side-by-Side
            </button>
          </div>
        </div>
      </div>

      {batchesToDisplay.map((batchId) => {
        const grid = result.timetable[batchId];
        if (!grid) return null;

        // Extract year and batch from batchId (format: IT_2_B1)
        const parts = batchId.split("_");
        const yrVal = parts[1] || currentYear;
        const batchVal = parts[2] || currentBatch;
        const yearLabel = YEARS.find((y) => y.value === Number(yrVal))?.label || `${yrVal}th Year`;

        return (
          <div className="grid-card" key={batchId} style={{ marginBottom: "24px" }}>
            <div className="grid-card-header">
              <div className="grid-card-title">
                <span className={`batch-pill batch-pill-${batchVal.toLowerCase()}`}>
                  {yearLabel} — {batchVal}
                </span>
                <h3>
                  Timetable Schedule — {yearLabel} ({batchVal})
                </h3>
              </div>
              <span className="text-muted text-sm">
                Department of Information Technology ({batchId})
              </span>
            </div>

            <div className="grid-scroll-container">
              <table className="timetable-grid">
                <thead>
                  <tr>
                    <th className="th-day">Day</th>
                    {displayCols.map((c, idx) =>
                      c.isLunch ? (
                        <th key={"lunch-head-" + idx} className="th-lunch">
                          <div>{c.label}</div>
                          <div className="time-sub">{c.time}</div>
                        </th>
                      ) : (
                        <th key={"p-head-" + c.index} className="th-period">
                          <div>{c.label}</div>
                          <div className="time-sub">{c.time}</div>
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {grid.map((dayRow, dayIdx) => (
                    <tr key={dayIdx}>
                      <td className="td-day">
                        <div className="day-name">
                          {DAY_NAMES[dayIdx] || `Day ${dayIdx + 1}`}
                        </div>
                        <div className="day-sub">Day {dayIdx + 1}</div>
                      </td>

                      {displayCols.map((c, colIdx) => {
                        if (c.isLunch) {
                          return (
                            <td key={"lunch-cell-" + colIdx} className="td-lunch">
                              <div className="lunch-box">
                                <span className="lunch-icon">☕</span>
                                <span className="lunch-text">LUNCH</span>
                              </div>
                            </td>
                          );
                        }

                        const cell = dayRow[c.index];
                        if (!cell) {
                          return (
                            <td key={"cell-" + c.index} className="td-empty">
                              <span className="empty-dash">—</span>
                            </td>
                          );
                        }

                        const isTheory = cell.type === "theory";
                        const isLab = cell.type === "lab";
                        const isLibrary = cell.type === "library";

                        let slotClass = "slot-theory";
                        let badgeClass = "type-theory";
                        let badgeText = "Lecture (L)";

                        if (isLab) {
                          slotClass = "slot-lab";
                          badgeClass = "type-lab";
                          badgeText = cell.lab ? `Practical (${cell.lab})` : "Practical (P)";
                        } else if (isLibrary) {
                          slotClass = "slot-library";
                          badgeClass = "type-library";
                          badgeText = "Library Hour";
                        }

                        return (
                          <td key={"cell-" + c.index} className="td-slot">
                            <div className={`slot-card ${slotClass}`}>
                              <div className="slot-subject">{cell.subject}</div>
                              {cell.staff && (
                                <div className="slot-staff">{cell.staff}</div>
                              )}
                              <div className="slot-type-row">
                                <span className={`type-badge ${badgeClass}`}>
                                  {badgeText}
                                </span>
                              </div>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
