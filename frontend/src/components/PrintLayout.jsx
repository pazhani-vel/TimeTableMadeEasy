import React from "react";
import { PERIOD_TIME_SLOTS, YEARS } from "../constants/academicData";

export default function PrintLayout({ result, days, periods }) {
  if (!result || !result.timetable) return null;

  const periodsCount = Number(periods) || 8;
  const half = Math.floor(periodsCount / 2);
  const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  const displayCols = [];
  for (let p = 0; p < periodsCount; p++) {
    const slotInfo = PERIOD_TIME_SLOTS.find((s) => !s.lunch && s.index === p) || {
      index: p,
      label: `P${p + 1}`,
      time: "",
    };
    displayCols.push({ ...slotInfo, isLunch: false });

    if (p === half - 1) {
      displayCols.push({
        isLunch: true,
        label: "LUNCH",
        time: "12:05-01:00",
      });
    }
  }

  const currentDate = new Date().toLocaleDateString("en-IN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const getBatchLabel = (batchId) => {
    const parts = batchId.split("_");
    if (parts.length === 3) {
      const yrVal = parts[1];
      const batchVal = parts[2];
      const yearLabel = YEARS.find((y) => y.value === Number(yrVal))?.label || `${yrVal}th Year`;
      return `${yearLabel} - Batch ${batchVal}`;
    }
    return `BATCH ${batchId}`;
  };

  return (
    <div className="print-only-layout">
      {/* Official Header */}
      <div className="print-header">
        <div className="print-header-top">COLLEGE OF ENGINEERING AND TECHNOLOGY</div>
        <div className="print-header-dept">DEPARTMENT OF INFORMATION TECHNOLOGY</div>
        <div className="print-header-title">DEPARTMENT CLASS TIMETABLE — ACADEMIC YEAR 2026–2027</div>
        <div className="print-meta-line">
          <span><strong>Department:</strong> IT</span>
          <span><strong>Generated Date:</strong> {currentDate}</span>
          <span><strong>Status:</strong> {result.status}</span>
        </div>
      </div>

      {/* Batch Tables */}
      {Object.entries(result.timetable).map(([batchId, grid]) => (
        <div className="print-batch-block" key={batchId}>
          <h3 className="print-batch-heading">{getBatchLabel(batchId).toUpperCase()} ({batchId})</h3>
          <table className="print-table">
            <thead>
              <tr>
                <th>Day</th>
                {displayCols.map((c, idx) => (
                  <th key={idx}>
                    {c.label}
                    {c.time && <div className="print-th-time">{c.time}</div>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.map((dayRow, dayIdx) => (
                <tr key={dayIdx}>
                  <td className="print-td-day">{DAY_NAMES[dayIdx] || `Day ${dayIdx + 1}`}</td>
                  {displayCols.map((c, colIdx) => {
                    if (c.isLunch) {
                      return <td key={colIdx} className="print-td-lunch">LUNCH</td>;
                    }
                    const cell = dayRow[c.index];
                    if (!cell) {
                      return <td key={colIdx} className="print-td-empty">—</td>;
                    }
                    return (
                      <td key={colIdx} className="print-td-slot">
                        <div className="print-subj">{cell.subject}</div>
                        {cell.staff && <div className="print-staff">{cell.staff}</div>}
                        <div className="print-type">
                          [{cell.type === "theory" ? "L" : cell.type === "lab" ? `P (${cell.lab || "Lab"})` : "Lib"}]
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {/* Official Signature Footer */}
      <div className="print-signature-section">
        <div className="sig-box">
          <div className="sig-line"></div>
          <div className="sig-title">Timetable Coordinator</div>
        </div>
        <div className="sig-box">
          <div className="sig-line"></div>
          <div className="sig-title">Head of Department (HOD)</div>
        </div>
        <div className="sig-box">
          <div className="sig-line"></div>
          <div className="sig-title">Principal / Dean</div>
        </div>
      </div>
    </div>
  );
}
