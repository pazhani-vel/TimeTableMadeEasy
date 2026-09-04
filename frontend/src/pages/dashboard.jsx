import React, { useMemo, useState } from "react";
import "./dashboard.css";

import {
  ALL_IT_BATCHES,
  DEFAULT_LABS,
  YEARS,
  BATCH_OPTIONS,
  YEAR_TO_SEMESTERS,
  SEMESTER_OPTIONS,
  SAMPLE_CURRICULUM_PRESET,
} from "../constants/academicData";

import { generateTimetable } from "../api/timetableApi";

import Header from "../components/Header";
import MetaSettings from "../components/MetaSettings";
import SubjectConfigTable from "../components/SubjectConfigTable";
import TimetableGrid from "../components/TimetableGrid";
import FacultyWorkloadView from "../components/FacultyWorkloadView";
import PrintLayout from "../components/PrintLayout";

/*
 * =========================================================
 * ACADEMIC SCHEDULE ID
 *
 * Every Year + Batch + Semester combination is unique.
 *
 * Example:
 * IT_2_B1_S3
 * IT_2_B1_S4
 * IT_2_B2_S3
 *
 * Nothing is hardcoded here.
 * =========================================================
 */

const createScheduleId = (year, batch, semester) =>
  `${year}__${batch}__${semester}`;


/*
 * =========================================================
 * EMPTY COURSE
 *
 * IMPORTANT:
 * Nothing is prefilled.
 * =========================================================
 */

const createEmptyRow = (
  year,
  batch,
  semester
) => ({
  year: Number(year),
  batch,
  semester: Number(semester),

  /*
   * Keep this ID unique to the academic schedule.
   * Backend-facing batch_id is created separately during
   * payload construction.
   */
  schedule_id: createScheduleId(
    year,
    batch,
    semester
  ),

  sub_code: "",
  name: "",
  credits: "",

  staff: "",

  theory_hours: "",

  has_lab: false,
  lab_hours: "",
  lab_type: "",

  subject_type: "",
});


/*
 * =========================================================
 * VALID ACADEMIC COMBINATIONS
 *
 * Comes entirely from academicData.
 * =========================================================
 */

const getAcademicCombinations = () => {
  const combinations = [];

  ALL_IT_BATCHES.forEach((item) => {
    const year = Number(item.year);
    const batch = item.batch;

    const semesters =
      YEAR_TO_SEMESTERS[year] || [];

    semesters.forEach((semester) => {
      combinations.push({
        id: createScheduleId(
          year,
          batch,
          semester
        ),

        year,
        batch,
        semester: Number(semester),
      });
    });
  });

  return combinations;
};


export default function DashBoard() {

  /*
   * =======================================================
   * GENERAL SETTINGS
   * =======================================================
   */

  const [days, setDays] = useState(5);
  const [periods, setPeriods] = useState(8);


  /*
   * =======================================================
   * ACADEMIC COMBINATIONS
   * =======================================================
   */

  const academicCombinations = useMemo(
    () => getAcademicCombinations(),
    []
  );


  /*
   * =======================================================
   * NEW TAB SELECTION
   *
   * Start empty.
   * Nothing is automatically selected.
   * =======================================================
   */

  const [newTabYear, setNewTabYear] =
    useState("");

  const [newTabBatch, setNewTabBatch] =
    useState("");

  const [newTabSemester, setNewTabSemester] =
    useState("");


  /*
   * =======================================================
   * OPEN TABS
   *
   * Start with NO tab.
   *
   * User explicitly chooses what to add.
   * =======================================================
   */

  const [openTabs, setOpenTabs] =
    useState([]);

  const [activeOpenTabId, setActiveOpenTabId] =
    useState(null);


  /*
   * =======================================================
   * COURSES PER TAB
   * =======================================================
   */

  const [rowsByTab, setRowsByTab] =
    useState({});


  /*
   * =======================================================
   * GENERAL APP STATE
   * =======================================================
   */

  const [loading, setLoading] =
    useState(false);

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState("");

  const [activeTab, setActiveTab] =
    useState("CONFIG");


  /*
   * =======================================================
   * ACTIVE ACADEMIC TAB
   * =======================================================
   */

  const activeConfigTab =
    openTabs.find(
      (tab) =>
        tab.id === activeOpenTabId
    ) || null;


  const currentYear =
    activeConfigTab?.year ?? "";

  const currentBatch =
    activeConfigTab?.batch ?? "";

  const currentSemester =
    activeConfigTab?.semester ?? "";


  /*
   * =======================================================
   * CURRENT TAB COURSES
   * =======================================================
   */

  const rows =
    activeOpenTabId
      ? rowsByTab[activeOpenTabId] || []
      : [];


  /*
   * =======================================================
   * AVAILABLE BATCHES FOR SELECTED YEAR
   * =======================================================
   */

  const availableBatchesForYear =
    useMemo(() => {

      if (newTabYear === "") {
        return [];
      }

      const validBatches =
        new Set(
          ALL_IT_BATCHES
            .filter(
              (item) =>
                Number(item.year) ===
                Number(newTabYear)
            )
            .map(
              (item) =>
                item.batch
            )
        );

      /*
       * Filter out batches where ALL semesters
       * for that year+batch are already open.
       */

      return BATCH_OPTIONS.filter(
        (batch) => {
          if (!validBatches.has(batch.value)) {
            return false;
          }

          const semesters =
            YEAR_TO_SEMESTERS[
              Number(newTabYear)
            ] || [];

          const hasAvailable =
            semesters.some(
              (sem) =>
                !openTabs.some(
                  (tab) =>
                    Number(tab.year) ===
                      Number(newTabYear) &&
                    tab.batch ===
                      batch.value &&
                    Number(tab.semester) ===
                      Number(sem)
                )
            );

          return hasAvailable;
        }
      );

    }, [newTabYear, openTabs]);


  /*
   * =======================================================
   * AVAILABLE SEMESTERS FOR SELECTED YEAR
   * =======================================================
   */

  const availableSemesters =
    useMemo(() => {

      if (newTabYear === "") {
        return [];
      }

      const semesterValues =
        YEAR_TO_SEMESTERS[
          Number(newTabYear)
        ] || [];

      return SEMESTER_OPTIONS.filter(
        (option) => {
          if (
            !semesterValues.includes(
              Number(option.value)
            )
          ) {
            return false;
          }

          /*
           * Filter out semesters already open
           * for this year+batch combo.
           */

          if (newTabBatch) {
            return !openTabs.some(
              (tab) =>
                Number(tab.year) ===
                  Number(newTabYear) &&
                tab.batch ===
                  newTabBatch &&
                Number(tab.semester) ===
                  Number(option.value)
            );
          }

          return true;
        }
      );

    }, [newTabYear, newTabBatch, openTabs]);


  /*
   * =======================================================
   * YEAR CHANGE
   * =======================================================
   */

  const handleNewTabYearChange =
    (event) => {

      const value =
        event.target.value;

      if (value === "") {
        setNewTabYear("");
        setNewTabBatch("");
        setNewTabSemester("");
        return;
      }

      const year =
        Number(value);

      setNewTabYear(year);

      /*
       * Select the first AVAILABLE batch
       * from academicData.
       */

      const batches =
        ALL_IT_BATCHES.filter(
          (item) =>
            Number(item.year) ===
            year
        );

      const firstBatch =
        batches[0]?.batch ?? "";

      setNewTabBatch(
        firstBatch
      );

      /*
       * Select the first semester
       * available for that year.
       */

      const semesters =
        YEAR_TO_SEMESTERS[year] || [];

      setNewTabSemester(
        semesters.length > 0
          ? Number(semesters[0])
          : ""
      );
    };


  /*
   * =======================================================
   * BATCH CHANGE
   * =======================================================
   */

  const handleNewTabBatchChange =
    (event) => {

      setNewTabBatch(
        event.target.value
      );

    };


  /*
   * =======================================================
   * SEMESTER CHANGE
   * =======================================================
   */

  const handleNewTabSemesterChange =
    (event) => {

      const value =
        event.target.value;

      setNewTabSemester(
        value === ""
          ? ""
          : Number(value)
      );

    };


  /*
   * =======================================================
   * TAB LABEL
   * =======================================================
   */

  const getOpenTabLabel = (
    tab
  ) => {

    const yearLabel =
      YEARS.find(
        (year) =>
          Number(year.value) ===
          Number(tab.year)
      )?.label ||
      String(tab.year);

    const batchLabel =
      BATCH_OPTIONS.find(
        (batch) =>
          batch.value ===
          tab.batch
      )?.label ||
      String(tab.batch);

    const semesterLabel =
      SEMESTER_OPTIONS.find(
        (semester) =>
          Number(semester.value) ===
          Number(tab.semester)
      )?.label ||
      `Semester ${tab.semester}`;

    return `${yearLabel} - ${batchLabel} (${semesterLabel})`;
  };


  /*
   * =======================================================
   * ADD COURSE
   * =======================================================
   */

  const addRow = (
    params = {}
  ) => {

    if (!activeOpenTabId) {
      return;
    }

    const year =
      Number(
        params.year ??
        currentYear
      );

    const batch =
      params.batch ??
      currentBatch;

    const semester =
      Number(
        params.semester ??
        currentSemester
      );

    const newRow =
      createEmptyRow(
        year,
        batch,
        semester
      );

    setRowsByTab(
      (previous) => ({
        ...previous,

        [activeOpenTabId]: [
          ...(previous[
            activeOpenTabId
          ] || []),

          newRow,
        ],
      })
    );
  };


  /*
   * =======================================================
   * REMOVE COURSE
   * =======================================================
   */

  const removeRow = (
    index
  ) => {

    if (!activeOpenTabId) {
      return;
    }

    setRowsByTab(
      (previous) => ({

        ...previous,

        [activeOpenTabId]:
          (
            previous[
              activeOpenTabId
            ] || []
          ).filter(
            (_, rowIndex) =>
              rowIndex !== index
          ),
      })
    );
  };


  /*
   * =======================================================
   * UPDATE COURSE
   * =======================================================
   */

  const updateRow = (
    index,
    field,
    value
  ) => {

    if (!activeOpenTabId) {
      return;
    }

    setRowsByTab(
      (previous) => {

        const currentRows =
          previous[
            activeOpenTabId
          ] || [];

        if (!currentRows[index]) {
          return previous;
        }

        const updatedRows =
          [...currentRows];

        updatedRows[index] = {
          ...updatedRows[index],
          [field]: value,
        };

        /*
         * Academic identity is controlled
         * by the tab.
         *
         * Do NOT let the course row create
         * a different academic identity.
         */

        updatedRows[index].year =
          Number(currentYear);

        updatedRows[index].batch =
          currentBatch;

        updatedRows[index].semester =
          Number(currentSemester);

        updatedRows[index].schedule_id =
          activeOpenTabId;

        return {
          ...previous,

          [activeOpenTabId]:
            updatedRows,
        };
      }
    );
  };


  /*
   * =======================================================
   * CREATE NEW TAB
   * =======================================================
   */

  const createNewTab = () => {

    setError("");

    /*
     * Validate selectors.
     */

    if (
      newTabYear === "" ||
      newTabBatch === "" ||
      newTabSemester === ""
    ) {

      setError(
        "Please select Year, Batch and Semester before adding a new tab."
      );

      return;
    }


    const year =
      Number(newTabYear);

    const batch =
      newTabBatch;

    const semester =
      Number(newTabSemester);


    /*
     * Check that the combination
     * actually exists in academicData.
     */

    const validCombination =
      academicCombinations.find(
        (item) =>
          Number(item.year) ===
            year &&
          item.batch ===
            batch &&
          Number(item.semester) ===
            semester
      );


    if (!validCombination) {

      setError(
        "The selected Year, Batch and Semester combination is not available."
      );

      return;
    }


    /*
     * Check duplicate.
     */

    const alreadyOpen =
      openTabs.some(
        (tab) =>
          tab.id ===
          validCombination.id
      );


    if (alreadyOpen) {

      setActiveOpenTabId(
        validCombination.id
      );

      setActiveTab("CONFIG");

      setError("");

      return;
    }


    /*
     * Create new tab.
     */

    const newTab = {
      id:
        validCombination.id,

      year:
        validCombination.year,

      batch:
        validCombination.batch,

      semester:
        validCombination.semester,
    };


    const nextTabs = [
      ...openTabs,
      newTab,
    ];


    setOpenTabs(
      nextTabs
    );


    /*
     * AUTO-FILL FROM SAMPLE CURRICULUM PRESET.
     * Match year + batch + semester to preset entries
     * and pre-populate the subject rows.
     */

    const presetSubjects =
      SAMPLE_CURRICULUM_PRESET.filter(
        (item) =>
          Number(item.year) ===
            Number(year) &&
          item.batch === batch &&
          (
            Number(item.semester) ===
              Number(semester) ||
            !item.semester
          )
      );

    const presetRows =
      presetSubjects.map(
        (item) => ({
          year: Number(year),
          batch,
          semester: Number(semester),
          schedule_id: newTab.id,
          batch_id:
            ALL_IT_BATCHES.find(
              (b) =>
                Number(b.year) ===
                  Number(year) &&
                b.batch === batch
            )?.id ||
            `IT_${Number(year)}_${batch}`,
          sub_code:
            item.sub_code || "",
          name:
            item.name || "",
          credits:
            item.credits ?? "",
          staff:
            item.staff || "",
          theory_hours:
            item.theory_hours ?? "",
          has_lab:
            Boolean(item.has_lab),
          lab_hours:
            item.lab_hours ?? "",
          lab_type:
            item.lab_type || "",
          subject_type: "regular",
        })
      );

    setRowsByTab(
      (previous) => ({
        ...previous,
        [newTab.id]: presetRows,
      })
    );


    /*
     * Immediately activate it.
     */

    setActiveOpenTabId(
      newTab.id
    );

    setActiveTab(
      "CONFIG"
    );


    /*
     * Clear selectors so the user
     * explicitly chooses the next one.
     *
     * This also prevents accidentally
     * adding the same tab repeatedly.
     */

    setNewTabYear("");
    setNewTabBatch("");
    setNewTabSemester("");
  };


  /*
   * =======================================================
   * CLOSE TAB
   * =======================================================
   */

  const closeTab = (
    idToClose
  ) => {

    if (openTabs.length <= 1) {

      setError(
        "At least one academic schedule must remain open."
      );

      return;
    }


    const nextTabs =
      openTabs.filter(
        (tab) =>
          tab.id !==
          idToClose
      );


    setOpenTabs(
      nextTabs
    );


    setRowsByTab(
      (previous) => {

        const updated = {
          ...previous,
        };

        delete updated[
          idToClose
        ];

        return updated;
      }
    );


    if (
      activeOpenTabId ===
      idToClose
    ) {

      setActiveOpenTabId(
        nextTabs[0]?.id ||
        null
      );
    }

    setError("");
  };


  /*
   * =======================================================
   * LOAD PRESET
   *
   * Disabled intentionally because you requested
   * no automatic/pre-filled courses.
   * =======================================================
   */

  const handleLoadPreset = () => {

    setError(
      "Preset loading is disabled. Add courses manually to each academic schedule."
    );
  };


  /*
   * =======================================================
   * RESET
   *
   * Clears courses only.
   * Does NOT create courses.
   * =======================================================
   */

  const handleReset = () => {

    const emptyRows = {};

    openTabs.forEach(
      (tab) => {

        emptyRows[
          tab.id
        ] = [];

      }
    );

    setRowsByTab(
      emptyRows
    );

    setResult(null);
    setError("");
  };


  /*
   * =======================================================
   * PRINT
   * =======================================================
   */

  const handlePrint = () => {
    window.print();
  };


  /*
   * =======================================================
   * GENERATE TIMETABLE
   * =======================================================
   */

  const generate = async () => {

    /*
     * Collect ONLY actual courses.
     */

    const allRows =
      Object.values(
        rowsByTab
      )
        .flat()
        .filter(
          (row) =>
            row.name?.trim() ||
            row.sub_code?.trim()
        );


    /*
     * No courses.
     */

    if (
      allRows.length === 0
    ) {

      setError(
        "Please add at least one course before generating the timetable."
      );

      return;
    }


    /*
     * Validate every course.
     */

    const invalidRow =
      allRows.find(
        (row) => {

          const name =
            row.name?.trim();

          const staff =
            row.staff?.trim();

          const theoryHours =
            Number(
              row.theory_hours
            );

          return (
            !name ||
            !staff ||
            !row.theory_hours ||
            theoryHours <= 0
          );
        }
      );


    if (invalidRow) {

      setError(
        `Please complete the course "${
          invalidRow.name?.trim() ||
          invalidRow.sub_code ||
          "Unnamed Course"
        }". Every course requires a name, faculty, and at least 1 lecture hour.`
      );

      return;
    }


    /*
     * Validate labs.
     */

    const invalidLab =
      allRows.find(
        (row) =>
          row.has_lab &&
          (
            !row.lab_hours ||
            Number(row.lab_hours) <= 0 ||
            Number(row.lab_hours) % 2 !== 0
          )
      );


    if (invalidLab) {

      setError(
        `Course "${invalidLab.name}" has practical enabled, but lab hours must be a positive multiple of 2.`
      );

      return;
    }


    /*
     * Make sure every course belongs
     * to an OPEN academic schedule.
     */

    const invalidSchedule =
      allRows.find(
        (row) =>
          !openTabs.some(
            (tab) =>
              Number(tab.year) ===
                Number(row.year) &&
              tab.batch ===
                row.batch &&
              Number(tab.semester) ===
                Number(row.semester)
          )
      );


    if (invalidSchedule) {

      setError(
        `Course "${invalidSchedule.name}" is not associated with an open Year, Batch and Semester schedule.`
      );

      return;
    }


    setLoading(true);
    setError("");


    try {

      /*
       * ===================================================
       * IMPORTANT
       *
       * We create the backend batch list from the
       * ACTUAL academic schedules being used.
       *
       * We do not send every possible batch blindly.
       * ===================================================
       */

      const usedScheduleKeys =
        new Set(
          allRows.map(
            (row) =>
              createScheduleId(
                Number(row.year),
                row.batch,
                Number(row.semester)
              )
          )
        );


      const scheduleDefinitions =
        [...usedScheduleKeys]
          .map(
            (scheduleId) =>
              openTabs.find(
                (tab) =>
                  tab.id ===
                  scheduleId
              )
          )
          .filter(Boolean);


      /*
       * Backend-compatible batch objects.
       *
       * The important information is still kept separately:
       *
       * year
       * batch
       * semester
       *
       * No regex is used.
       */

      const batches =
        scheduleDefinitions.map(
          (schedule) => ({
            ...ALL_IT_BATCHES.find(
              (item) =>
                Number(item.year) ===
                  Number(schedule.year) &&
                item.batch ===
                  schedule.batch
            ),

            year:
              Number(schedule.year),

            batch:
              schedule.batch,

            semester:
              Number(schedule.semester),

            schedule_id:
              schedule.id,
          })
        );


      /*
       * Subjects.
       *
       * No fake values.
       */

      const subjects =
        allRows.map(
          (row) => ({

            name:
              row.name.trim(),

            sub_code:
              row.sub_code?.trim() ||
              undefined,

            credits:
              row.credits !== ""
                ? Number(
                    row.credits
                  )
                : undefined,

            year:
              Number(row.year),

            batch:
              row.batch,

            semester:
              Number(row.semester),

            schedule_id:
              createScheduleId(
                Number(row.year),
                row.batch,
                Number(row.semester)
              ),

            /*
             * Keep batch_id compatible with
             * the academic batch itself.
             *
             * Do NOT add semester to batch_id here.
             * Semester is already a separate field.
             */

            batch_id:
              ALL_IT_BATCHES.find(
                (item) =>
                  Number(item.year) ===
                    Number(row.year) &&
                  item.batch ===
                    row.batch
              )?.id ||
              `IT_${Number(
                row.year
              )}_${row.batch}`,

            department:
              "IT",

            staff:
              row.staff.trim(),

            theory_hours:
              Number(
                row.theory_hours
              ),

            has_lab:
              Boolean(
                row.has_lab
              ),

            lab_hours:
              row.has_lab
                ? Number(
                    row.lab_hours
                  )
                : 0,

            lab_type:
              row.has_lab
                ? row.lab_type ||
                  null
                : null,

            subject_type:
              row.subject_type ||
              "regular",
          })
        );


      const payload = {

        days: [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
  ].slice(0, Number(days)),

        periods:
          Number(periods),

        batches,

        labs:
          DEFAULT_LABS,

        subjects,
      };


      console.log(
        "TIMETABLE PAYLOAD:",
        payload
      );


      const data =
        await generateTimetable(
          payload
        );


      if (
        data.success ||
        data.status ===
          "OPTIMAL" ||
        data.status ===
          "FEASIBLE"
      ) {

        setResult(
          data
        );

        setActiveTab(
          "TIMETABLE"
        );

      } else {

        setError(
          data.message ||
          "No feasible timetable found. Try adjusting period allocations or faculty assignments."
        );

      }

    } catch (generationError) {

      console.error(
        generationError
      );

      setError(
        "An unexpected error occurred while communicating with the solver backend."
      );

    } finally {

      setLoading(false);

    }
  };


  /*
   * =======================================================
   * RENDER
   * =======================================================
   */

  return (

    <div className="dashboard-app">

      <PrintLayout
        result={result}
        days={days}
        periods={periods}
      />


      <div className="screen-layout">

        <Header
          onLoadPreset={
            handleLoadPreset
          }

          onReset={
            handleReset
          }

          onPrint={
            handlePrint
          }

          hasResult={
            !!result
          }
        />


        <main className="dashboard-main-content">


          {/* =================================================
              ACADEMIC SCHEDULE TABS
          ================================================= */}

          <div className="batch-tab-toolbar">

            <div className="batch-tabs-row">

              {openTabs.map(
                (tab) => (

                  <div
                    key={tab.id}
                    className={`batch-tab-btn ${
                      activeOpenTabId ===
                      tab.id
                        ? "active"
                        : ""
                    }`}

                    onClick={() => {

                      setActiveOpenTabId(
                        tab.id
                      );

                      setActiveTab(
                        "CONFIG"
                      );

                      setError("");

                    }}

                    role="button"
                    tabIndex={0}

                    onKeyDown={(event) => {

                      if (
                        event.key ===
                          "Enter" ||
                        event.key ===
                          " "
                      ) {

                        setActiveOpenTabId(
                          tab.id
                        );

                        setActiveTab(
                          "CONFIG"
                        );

                      }

                    }}
                  >

                    <span>
                      {getOpenTabLabel(
                        tab
                      )}
                    </span>


                    <button
                      type="button"
                      className="batch-tab-close"
                      onClick={(event) => {

                        event.stopPropagation();

                        closeTab(
                          tab.id
                        );

                      }}

                      aria-label={`Close ${getOpenTabLabel(
                        tab
                      )}`}
                    >
                      ×
                    </button>

                  </div>

                )
              )}


            </div>


            {/* =================================================
                NEW SCHEDULE SELECTORS
            ================================================= */}

            <div className="batch-tab-creator">


              {/* YEAR */}

              <div className="selector-item">

                <label htmlFor="new-tab-year">
                  Year
                </label>

                <select
                  id="new-tab-year"
                  className="form-control"
                  value={
                    newTabYear
                  }

                  onChange={
                    handleNewTabYearChange
                  }
                >

                  <option value="">
                    Select Year
                  </option>

                  {YEARS.map(
                    (year) => (

                      <option
                        key={
                          year.value
                        }
                        value={
                          year.value
                        }
                      >
                        {year.label}
                      </option>

                    )
                  )}

                </select>

              </div>


              {/* BATCH */}

              <div className="selector-item">

                <label htmlFor="new-tab-batch">
                  Batch
                </label>

                <select
                  id="new-tab-batch"
                  className="form-control"
                  value={
                    newTabBatch
                  }

                  onChange={
                    handleNewTabBatchChange
                  }

                  disabled={
                    !newTabYear
                  }
                >

                  <option value="">
                    Select Batch
                  </option>

                  {availableBatchesForYear.map(
                    (batch) => (

                      <option
                        key={
                          batch.value
                        }
                        value={
                          batch.value
                        }
                      >
                        {batch.label}
                      </option>

                    )
                  )}

                </select>

              </div>


              {/* SEMESTER */}

              <div className="selector-item">

                <label htmlFor="new-tab-semester">
                  Semester
                </label>

                <select
                  id="new-tab-semester"
                  className="form-control"
                  value={
                    newTabSemester
                  }

                  onChange={
                    handleNewTabSemesterChange
                  }

                  disabled={
                    !newTabYear
                  }
                >

                  <option value="">
                    Select Semester
                  </option>

                  {availableSemesters.map(
                    (semester) => (

                      <option
                        key={
                          semester.value
                        }
                        value={
                          semester.value
                        }
                      >
                        {semester.label}
                      </option>

                    )
                  )}

                </select>              </div>


              {/* ADD SCHEDULE BUTTON */}

              <div className="selector-item" style={{ justifyContent: "flex-end" }}>
                <label>&nbsp;</label>
                <button
                  type="button"
                  className="batch-tab-add"
                  onClick={createNewTab}
                  disabled={!newTabYear || !newTabBatch || !newTabSemester}
                >
                  + Add Schedule
                </button>
              </div>

            </div>


          </div>


          {/* =================================================
              MAIN NAVIGATION
          ================================================= */}

          <div className="app-subnav">

            <button
              type="button"
              className={`subnav-btn ${
                activeTab ===
                "CONFIG"
                  ? "active"
                  : ""
              }`}

              onClick={() =>
                setActiveTab(
                  "CONFIG"
                )
              }
            >
              ✎
              1. Subject & Faculty Setup
            </button>


            <button
              type="button"
              className={`subnav-btn ${
                activeTab ===
                "TIMETABLE"
                  ? "active"
                  : ""
              } ${
                !result
                  ? "disabled"
                  : ""
              }`}

              onClick={() =>
                result &&
                setActiveTab(
                  "TIMETABLE"
                )
              }

              disabled={!result}
            >
              📅
              2. Generated Timetable

              {result && (
                <span className="subnav-badge">
                  Ready
                </span>
              )}
            </button>


            <button
              type="button"
              className={`subnav-btn ${
                activeTab ===
                "FACULTY"
                  ? "active"
                  : ""
              } ${
                !result
                  ? "disabled"
                  : ""
              }`}

              onClick={() =>
                result &&
                setActiveTab(
                  "FACULTY"
                )
              }

              disabled={!result}
            >
              👥
              3. Faculty Workload Matrix
            </button>

          </div>


          {/* =================================================
              ERROR
          ================================================= */}

          {error && (

            <div className="alert-banner alert-banner-error">

              <span className="alert-icon">
                ⚠️
              </span>

              <div className="alert-content">

                <strong>
                  Schedule Generation Error
                </strong>

                <p>
                  {error}
                </p>

              </div>

              <button
                type="button"
                className="alert-close"
                onClick={() =>
                  setError("")
                }
              >
                ✕
              </button>

            </div>

          )}


          {/* =================================================
              SUCCESS
          ================================================= */}

          {result &&
            activeTab ===
              "CONFIG" && (

            <div className="alert-banner alert-banner-success">

              <span className="alert-icon">
                ✓
              </span>

              <div className="alert-content">

                <strong>
                  Timetable Successfully Generated!
                </strong>

                <p>
                  Status:{" "}
                  {result.status}.
                  Switch to the Generated
                  Timetable or Faculty Workload
                  Matrix to view the result.
                </p>

              </div>

            </div>

          )}


          {/* =================================================
              CONFIGURATION
          ================================================= */}

          {activeTab ===
            "CONFIG" && (

            <div className="tab-content fade-in">

              <MetaSettings
                days={days}
                setDays={setDays}
                periods={periods}
                setPeriods={
                  setPeriods
                }
                loading={loading}
                onGenerate={
                  generate
                }
              />


              <div className="batches-grid">

                {activeConfigTab ? (

                  <SubjectConfigTable

                    year={
                      currentYear
                    }

                    batch={
                      currentBatch
                    }

                    semester={
                      currentSemester
                    }

                    batchId={
                      activeConfigTab.id
                    }

                    rows={
                      rows
                    }

                    updateRow={
                      updateRow
                    }

                    removeRow={
                      removeRow
                    }

                    addRow={
                      addRow
                    }

                    days={
                      days
                    }

                    periods={
                      periods
                    }

                  />

                ) : (

                  <div className="empty-table-msg">

                    No academic schedule selected.

                    <br />

                    Choose Year, Batch and Semester
                    above and click
                    <strong>
                      {" "}Add Schedule
                    </strong>.

                  </div>

                )}

              </div>


              <div className="bottom-generate-bar">

                <button
                  type="button"
                  className="btn btn-primary btn-lg"

                  disabled={
                    loading ||
                    openTabs.length === 0
                  }

                  onClick={
                    generate
                  }
                >

                  {loading
                    ? "Solving Constraints…"
                    : "Generate Department Timetable"}

                </button>

              </div>

            </div>

          )}


          {/* =================================================
              TIMETABLE
          ================================================= */}

          {activeTab ===
            "TIMETABLE" && (

            <div className="tab-content fade-in">

              <TimetableGrid
                result={
                  result
                }

                periods={
                  periods
                }
              />

            </div>

          )}


          {/* =================================================
              FACULTY
          ================================================= */}

          {activeTab ===
            "FACULTY" && (

            <div className="tab-content fade-in">

              <FacultyWorkloadView
                result={
                  result
                }

                days={
                  days
                }

                periods={
                  periods
                }
              />

            </div>

          )}

        </main>

      </div>

    </div>
  );
}