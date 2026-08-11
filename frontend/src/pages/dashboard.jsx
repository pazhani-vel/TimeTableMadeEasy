import React, { useState } from "react";
import "./dashboard.css";

import {
  ALL_IT_BATCHES,
  DEFAULT_LABS,
  DEFAULT_STAFF,
  SAMPLE_CURRICULUM_PRESET,
  YEARS,
  BATCH_OPTIONS,
} from "../constants/academicData";

import { generateTimetable } from "../api/timetableApi";

import Header from "../components/Header";
import MetaSettings from "../components/MetaSettings";
import SubjectConfigTable from "../components/SubjectConfigTable";
import TimetableGrid from "../components/TimetableGrid";
import FacultyWorkloadView from "../components/FacultyWorkloadView";
import PrintLayout from "../components/PrintLayout";

function createEmptyRow(year = 2, batch = "B1") {
  const batchId = `IT_${year}_${batch}`;
  return {
    year: Number(year),
    batch,
    batch_id: batchId,
    sub_code: "",
    name: "",
    credits: "",
    staff: DEFAULT_STAFF[0],
    theory_hours: 3,
    has_lab: false,
    lab_hours: 2,
    lab_type: "AC",
    subject_type: "regular",
  };
}

export default function DashBoard() {
  const [days, setDays] = useState(5);
  const [periods, setPeriods] = useState(8);

  const [selectedYear, setSelectedYear] = useState(2);
  const [selectedBatch, setSelectedBatch] = useState("B1");

  const [rows, setRows] = useState(() =>
    SAMPLE_CURRICULUM_PRESET.map((item) => ({ ...item }))
  );

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("CONFIG"); // CONFIG | TIMETABLE | FACULTY

  // Row operations
  const updateRow = (i, field, value) => {
    const copy = [...rows];
    copy[i] = { ...copy[i], [field]: value };
    // Maintain batch_id invariant if year or batch changes
    if (field === "year" || field === "batch") {
      const yr = field === "year" ? value : copy[i].year;
      const bt = field === "batch" ? value : copy[i].batch;
      copy[i].batch_id = `IT_${yr}_${bt}`;
    }
    setRows(copy);
  };

  const addRow = (params = {}) => {
    const yr = params.year || selectedYear;
    const bt = params.batch || selectedBatch;
    setRows([...rows, createEmptyRow(yr, bt)]);
  };

  const removeRow = (i) => setRows(rows.filter((_, idx) => idx !== i));

  // Presets & Reset
  const handleLoadPreset = () => {
    setRows(SAMPLE_CURRICULUM_PRESET.map((item) => ({ ...item })));
    setError("");
  };

  const handleReset = () => {
    const defaultRows = [];
    ALL_IT_BATCHES.forEach((b) => {
      defaultRows.push(createEmptyRow(b.year, b.batch));
    });
    setRows(defaultRows);
    setResult(null);
    setError("");
  };

  const handlePrint = () => {
    window.print();
  };

  // Generate timetable via backend solver service
  const generate = async () => {
    // Client-side checks & validations
    if (rows.length === 0) {
      setError("Please add at least one subject to generate a timetable.");
      return;
    }

    const invalidRow = rows.find(
      (r) => !r.name.trim() || !r.staff || !r.theory_hours || Number(r.theory_hours) <= 0
    );
    if (invalidRow) {
      setError(
        "Every subject requires a valid name, assigned staff, and at least 1 lecture hour."
      );
      return;
    }

    const invalidLab = rows.find(
      (r) =>
        r.has_lab &&
        (!r.lab_hours || Number(r.lab_hours) <= 0 || Number(r.lab_hours) % 2 !== 0)
    );
    if (invalidLab) {
      setError(
        `Subject "${invalidLab.name}" has practical enabled, but lab (P) hours must be a positive multiple of 2 (e.g. 2, 4).`
      );
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = {
        days: Number(days),
        periods_per_day: Number(periods),
        batches: ALL_IT_BATCHES,
        labs: DEFAULT_LABS,
        subjects: rows.map((r) => ({
          name: r.name.trim(),
          sub_code: r.sub_code || undefined,
          credits: r.credits !== "" ? Number(r.credits) : undefined,
          batch_id: r.batch_id || `IT_${r.year}_${r.batch}`,
          year: Number(r.year),
          batch: r.batch,
          department: "IT",
          staff: r.staff,
          theory_hours: Number(r.theory_hours),
          has_lab: Boolean(r.has_lab),
          lab_hours: r.has_lab ? Number(r.lab_hours) : 0,
          lab_type: r.has_lab ? r.lab_type || "AC" : null,
          subject_type: r.subject_type || "regular",
        })),
      };

      const data = await generateTimetable(payload);

      if (data.status === "OPTIMAL" || data.status === "FEASIBLE") {
        setResult(data);
        setActiveTab("TIMETABLE");
      } else {
        setError(
          data.message ||
            "No feasible timetable found. Try adjusting period allocations or staff assignments."
        );
      }
    } catch (e) {
      setError("An unexpected error occurred while communicating with the solver backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-app">
      {/* Printable Output View */}
      <PrintLayout result={result} days={days} periods={periods} />

      {/* Screen Interactive View */}
      <div className="screen-layout">
        <Header
          onLoadPreset={handleLoadPreset}
          onReset={handleReset}
          onPrint={handlePrint}
          hasResult={!!result}
        />

        <main className="dashboard-main-content">
          {/* Global Year & Batch Controls */}
          <div className="year-batch-toolbar" style={{ display: "flex", gap: "16px", alignItems: "center", marginBottom: "16px", background: "var(--card-bg, #ffffff)", padding: "12px 20px", borderRadius: "10px", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
            <div className="selector-item" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label htmlFor="year-select" style={{ fontWeight: 600, fontSize: "0.95rem" }}>Year:</label>
              <select
                id="year-select"
                className="form-control"
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                style={{ width: "130px" }}
              >
                {YEARS.map((y) => (
                  <option key={y.value} value={y.value}>
                    {y.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="selector-item" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label htmlFor="batch-select" style={{ fontWeight: 600, fontSize: "0.95rem" }}>Batch:</label>
              <select
                id="batch-select"
                className="form-control"
                value={selectedBatch}
                onChange={(e) => setSelectedBatch(e.target.value)}
                style={{ width: "130px" }}
              >
                {BATCH_OPTIONS.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginLeft: "auto", fontSize: "0.85rem", color: "#666" }}>
              Active Department: <strong>Information Technology (IT)</strong> | Selected: <strong>{YEARS.find(y => y.value === selectedYear)?.label} - {selectedBatch}</strong>
            </div>
          </div>

          {/* Main Navigation Tabs */}
          <div className="app-subnav">
            <button
              className={`subnav-btn ${activeTab === "CONFIG" ? "active" : ""}`}
              onClick={() => setActiveTab("CONFIG")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
              1. Subject & Faculty Setup
            </button>

            <button
              className={`subnav-btn ${activeTab === "TIMETABLE" ? "active" : ""} ${!result ? "disabled" : ""}`}
              onClick={() => result && setActiveTab("TIMETABLE")}
              disabled={!result}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              2. Generated Timetable
              {result && <span className="subnav-badge">Ready</span>}
            </button>

            <button
              className={`subnav-btn ${activeTab === "FACULTY" ? "active" : ""} ${!result ? "disabled" : ""}`}
              onClick={() => result && setActiveTab("FACULTY")}
              disabled={!result}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              3. Faculty Workload Matrix
            </button>
          </div>

          {/* Alert Banner */}
          {error && (
            <div className="alert-banner alert-banner-error">
              <span className="alert-icon">⚠️</span>
              <div className="alert-content">
                <strong>Schedule Generation Error</strong>
                <p>{error}</p>
              </div>
              <button className="alert-close" onClick={() => setError("")}>✕</button>
            </div>
          )}

          {result && activeTab === "CONFIG" && (
            <div className="alert-banner alert-banner-success">
              <span className="alert-icon">✓</span>
              <div className="alert-content">
                <strong>Timetable Successfully Generated!</strong>
                <p>Status: {result.status}. Switch to the "Generated Timetable" or "Faculty Workload Matrix" tab to view schedules.</p>
              </div>
            </div>
          )}

          {/* TAB 1: CONFIGURATION */}
          {activeTab === "CONFIG" && (
            <div className="tab-content fade-in">
              <MetaSettings
                days={days}
                setDays={setDays}
                periods={periods}
                setPeriods={setPeriods}
                loading={loading}
                onGenerate={generate}
              />

              <div className="batches-grid">
                <SubjectConfigTable
                  year={selectedYear}
                  batch={selectedBatch}
                  batchId={`IT_${selectedYear}_${selectedBatch}`}
                  rows={rows}
                  updateRow={updateRow}
                  removeRow={removeRow}
                  addRow={addRow}
                  days={days}
                  periods={periods}
                />
              </div>

              <div className="bottom-generate-bar">
                <button
                  className="btn btn-primary btn-lg"
                  disabled={loading}
                  onClick={generate}
                >
                  {loading ? "Solving Constraints…" : "Generate Department Timetable"}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: TIMETABLE GRID */}
          {activeTab === "TIMETABLE" && (
            <div className="tab-content fade-in">
              <TimetableGrid
                result={result}
                selectedYear={selectedYear}
                selectedBatch={selectedBatch}
                periods={periods}
              />
            </div>
          )}

          {/* TAB 3: FACULTY WORKLOAD MATRIX */}
          {activeTab === "FACULTY" && (
            <div className="tab-content fade-in">
              <FacultyWorkloadView
                result={result}
                days={days}
                periods={periods}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}