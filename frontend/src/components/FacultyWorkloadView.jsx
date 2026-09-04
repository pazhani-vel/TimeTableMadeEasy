import React, { useState } from "react";

export default function FacultyWorkloadView({ result, days, periods }) {
  const [selectedStaff, setSelectedStaff] = useState("ALL");

  if (!result || !result.timetable) return null;

  const staffMap = {};
  const periodsCount = Number(periods) || 8;
  const daysCount = Number(days) || 5;

  Object.entries(result.timetable).forEach(([batchName, grid]) => {
    grid.forEach((dayRow, dayIdx) => {
      dayRow.forEach((cell, periodIdx) => {
        if (cell && cell.staff) {
          const s = cell.staff;
          if (!staffMap[s]) {
            staffMap[s] = [];
          }
          staffMap[s].push({
            batchName,
            day: dayIdx,
            period: periodIdx,
            subject: cell.subject,
            type: cell.type,
          });
        }
      });
    });
  });

  const staffList = Object.keys(staffMap).sort();

  if (staffList.length === 0) return null;

  const activeStaffList = selectedStaff === "ALL" ? staffList : [selectedStaff];
  const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="faculty-matrix-section">
      <div className="section-header">
        <div>
          <h2>Faculty Workload & Schedule Matrix</h2>
          <p>Verify individual faculty period allocations and clash-free schedules across batches</p>
        </div>

        <div className="staff-filter-wrap">
          <label>Filter Faculty:</label>
          <select
            className="form-control form-control-sm"
            value={selectedStaff}
            onChange={(e) => setSelectedStaff(e.target.value)}
          >
            <option value="ALL">All Faculty Members ({staffList.length})</option>
            {staffList.map((s) => (
              <option key={s} value={s}>
                {s} ({staffMap[s].length} periods)
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="faculty-matrix-container">
        {activeStaffList.map((staffName) => {
          const assignments = staffMap[staffName] || [];

          return (
            <div className="faculty-card" key={staffName}>
              <div className="faculty-card-header">
                <div>
                  <h4 className="faculty-name">{staffName}</h4>
                  <span className="text-muted text-xs">Department Faculty</span>
                </div>
                <div className="faculty-load-badge">
                  Total Allocated: <strong>{assignments.length} periods/week</strong>
                </div>
              </div>

              <div className="grid-scroll-container">
                <table className="faculty-grid">
                  <thead>
                    <tr>
                      <th>Day</th>
                      {Array.from({ length: periodsCount }).map((_, pIdx) => (
                        <th key={pIdx}>P{pIdx + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from({ length: daysCount }).map((_, dIdx) => (
                      <tr key={dIdx}>
                        <td className="td-day-sm">{DAY_NAMES[dIdx] || `Day ${dIdx + 1}`}</td>
                        {Array.from({ length: periodsCount }).map((_, pIdx) => {
                          const match = assignments.find(
                            (a) => a.day === dIdx && a.period === pIdx
                          );

                          return (
                            <td key={pIdx} className="td-fac-slot">
                              {match ? (
                                <div className={`fac-pill fac-pill-${match.type}`}>
                                  <span className="fac-batch">{match.batchName}</span>
                                  <span className="fac-subj">{match.subject}</span>
                                </div>
                              ) : (
                                <span className="fac-free">📚 Library</span>
                              )}
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
    </div>
  );
}
