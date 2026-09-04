import React from "react";

export default function BatchStatsCard({ batchId, batch, year, rows, days, periods }) {
  const batchRows = rows;
  
  const totalTheory = batchRows.reduce((acc, r) => acc + (Number(r.theory_hours) || 0), 0);
  const totalLab = batchRows.reduce((acc, r) => acc + (r.has_lab ? Number(r.lab_hours) || 0 : 0), 0);
  const totalPeriodsUsed = totalTheory + totalLab;
  const maxWeeklyPeriods = (Number(days) || 5) * (Number(periods) || 8);
  const loadPercentage = maxWeeklyPeriods > 0 ? Math.round((totalPeriodsUsed / maxWeeklyPeriods) * 100) : 0;

  // Check for any invalid lab hours (odd numbers)
  const hasInvalidLabHours = batchRows.some((r) => r.has_lab && (Number(r.lab_hours) <= 0 || Number(r.lab_hours) % 2 !== 0));
  const isOverCapacity = totalPeriodsUsed > maxWeeklyPeriods;

  return (
    <div className="batch-stats-bar">
      <div className="stats-group">
        <div className="stat-pill">
          <span className="stat-label">Subjects</span>
          <span className="stat-val">{batchRows.length}</span>
        </div>
        <div className="stat-pill">
          <span className="stat-label">Lecture (L)</span>
          <span className="stat-val">{totalTheory} hrs/wk</span>
        </div>
        <div className="stat-pill">
          <span className="stat-label">Practical (P)</span>
          <span className="stat-val">{totalLab} hrs/wk</span>
        </div>
        <div className="stat-pill">
          <span className="stat-label">Total Load</span>
          <span className={`stat-val ${isOverCapacity ? "text-danger" : ""}`}>
            {totalPeriodsUsed} / {maxWeeklyPeriods} slots ({loadPercentage}%)
          </span>
        </div>
      </div>

      <div className="stats-health">
        {hasInvalidLabHours && (
          <span className="alert-badge alert-warning" title="Lab (P) hours must be even multiples of 2 (e.g. 2, 4)">
            ⚠️ Lab hours must be multiples of 2
          </span>
        )}
        {isOverCapacity && (
          <span className="alert-badge alert-danger">
            ❌ Exceeds max slot capacity ({maxWeeklyPeriods})
          </span>
        )}
        {!hasInvalidLabHours && !isOverCapacity && totalPeriodsUsed > 0 && (
          <span className="alert-badge alert-success">
            ✓ Load balanced
          </span>
        )}
      </div>
    </div>
  );
}
