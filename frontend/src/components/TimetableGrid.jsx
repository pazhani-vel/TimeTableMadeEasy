import React, { useMemo, useState } from "react";

import {
  PERIOD_TIME_SLOTS,
} from "../constants/academicData";


export default function TimetableGrid({
  result,
  periods = 8,
}) {

  const batchNames = result?.timetable
    ? Object.keys(result.timetable)
    : [];

  const [selectedBatch, setSelectedBatch] =
    useState(batchNames[0] || "");

  const [viewMode, setViewMode] =
    useState("ALL");


  if (!result || !result.timetable) {
    return null;
  }

  const timetable = result.timetable;

  const periodsCount = Number(periods) || 8;

  const displayCols = useMemo(() => {
    return PERIOD_TIME_SLOTS
      .filter((slot) =>
        slot.lunch || Number(slot.index) < periodsCount
      )
      .map((slot) => ({
        ...slot,
        isLunch: Boolean(slot.lunch),
      }));
  }, [periodsCount]);

  const DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
  ];

  const batchesToDisplay =
    viewMode === "ALL"
      ? batchNames
      : selectedBatch
        ? [selectedBatch]
        : batchNames.length > 0
          ? [batchNames[0]]
          : [];

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
          </p>
        </div>

        <div className="timetable-controls" style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <div className="control-group" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <label className="text-sm font-semibold">Batch:</label>
            <select
              className="form-control text-sm"
              value={selectedBatch}
              onChange={(e) => { setSelectedBatch(e.target.value); setViewMode("SINGLE"); }}
              style={{ padding: "4px 8px", width: "auto" }}
            >
              {batchNames.map((name) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>

          <div className="tab-switcher">
            <button type="button" className={`tab-btn ${viewMode === "SINGLE" ? "active" : ""}`} onClick={() => setViewMode("SINGLE")}>
              Selected Batch
            </button>
            <button type="button" className={`tab-btn ${viewMode === "ALL" ? "active" : ""}`} onClick={() => setViewMode("ALL")}>
              All Batches
            </button>
          </div>
        </div>
      </div>

      {batchesToDisplay.length === 0 && (
        <div className="empty-table-msg">
          No generated timetable is available.
        </div>
      )}

      {batchesToDisplay.map((batchName) => {
        const grid = timetable[batchName];
        if (!grid) return null;

        return (
          <div className="grid-card" key={batchName} style={{ marginBottom: "24px" }}>
            <div className="grid-card-header">
              <div className="grid-card-title">
                <span className="batch-pill">{batchName}</span>
                <h3>Timetable Schedule — {batchName}</h3>
              </div>
            </div>

            <div className="grid-scroll-container">
              <table className="timetable-grid">
                <thead>
                  <tr>
                    <th className="th-day">Day</th>
                    {displayCols.map((col, idx) => {
                      if (col.isLunch) {
                        return (
                          <th key={`lh-${idx}`} className="th-lunch">
                            <div>{col.label || "Lunch"}</div>
                            {col.time && <div className="time-sub">{col.time}</div>}
                          </th>
                        );
                      }
                      return (
                        <th key={`ph-${col.index ?? idx}`} className="th-period">
                          <div>{col.label || `P${idx + 1}`}</div>
                          {col.time && <div className="time-sub">{col.time}</div>}
                        </th>
                      );
                    })}
                  </tr>
                </thead>

                <tbody>
                  {grid.map((dayRow, dayIdx) => (
                    <tr key={dayIdx}>
                      <td className="td-day">
                        <div className="day-name">{DAY_NAMES[dayIdx]}</div>
                        <div className="day-sub">Day {dayIdx + 1}</div>
                      </td>

                      {displayCols.map((col, colIdx) => {
                        if (col.isLunch) {
                          return (
                            <td key={`lc-${colIdx}`} className="td-lunch">
                              <div className="lunch-box">
                                <span className="lunch-icon">☕</span>
                                <span className="lunch-text">{col.label || "LUNCH"}</span>
                              </div>
                            </td>
                          );
                        }

                        const cell = dayRow[col.index];

                        if (!cell || cell.type === "free") {
                          return (
                            <td key={`ec-${col.index}`} className="td-empty">
                              <div className="slot-card slot-library">
                                <div className="slot-subject">Library</div>
                                <div className="slot-type-row">
                                  <span className="type-badge type-library">Free Period</span>
                                </div>
                              </div>
                            </td>
                          );
                        }

                        const isLab = cell.type === "lab";
                        const isSpecial = cell.type === "special";

                        let slotClass = "slot-theory";
                        let badgeClass = "type-theory";
                        let badgeText = "Lecture";

                        if (isLab) {
                          slotClass = "slot-lab";
                          badgeClass = "type-lab";
                          badgeText = "Practical";
                        } else if (isSpecial) {
                          slotClass = "slot-library";
                          badgeClass = "type-library";
                          badgeText = cell.subject || "Special";
                        }

                        return (
                          <td key={`sc-${col.index}`} className="td-slot">
                            <div className={`slot-card ${slotClass}`}>
                              <div className="slot-subject">{cell.subject || "—"}</div>
                              {cell.staff && <div className="slot-staff">{cell.staff}</div>}
                              <div className="slot-type-row">
                                <span className={`type-badge ${badgeClass}`}>{badgeText}</span>
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
