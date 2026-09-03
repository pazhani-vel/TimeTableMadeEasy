import React from "react";

import {
  DEFAULT_STAFF,
  YEARS,
  BATCH_OPTIONS,
} from "../constants/academicData";

import BatchStatsCard from "./BatchStatsCard";

import coursesData from "../constants/courses.json";


/*
 * =========================================================
 * COURSES FOR SELECTED SEMESTER
 * =========================================================
 */

function getCoursesForSemester(
  year,
  semester
) {
  return coursesData.courses.filter(
    (course) =>
      Number(course.semester) ===
      Number(semester)
  );
}


export default function SubjectConfigTable({

  year,

  batch,

  semester,

  batchId,

  rows,

  updateRow,

  removeRow,

  addRow,

  days,

  periods,

}) {

  /*
   * The tab ID is the identity of this
   * academic schedule.
   */

  const currentScheduleId =
    batchId || "";


  const semesterCourses =
    getCoursesForSemester(
      year,
      semester
    );


  /*
   * =======================================================
   * ONLY COURSES BELONGING TO THIS TAB
   * =======================================================
   */

  const batchRows =
    rows
      .map(
        (row, index) => ({
          ...row,
          originalIndex: index,
        })
      )
      .filter(
        (row) => {

          return (
            row.schedule_id ===
            currentScheduleId
          );

        }
      );


  const yearLabel =
    YEARS.find(
      (item) =>
        Number(item.value) ===
        Number(year)
    )?.label ||
    String(year);


  const batchLabel =
    BATCH_OPTIONS.find(
      (item) =>
        item.value ===
        batch
    )?.label ||
    String(batch);


  /*
   * =======================================================
   * COURSE SELECTION
   *
   * This only fills data from courses.json.
   * Faculty is NOT automatically selected.
   * =======================================================
   */

  const handleCourseSelect = (
    index,
    subCode
  ) => {

    const course =
      coursesData.courses.find(
        (item) =>
          item.sub_code ===
          subCode
      );


    if (!course) {
      return;
    }


    const {
      lecture,
      practical,
      credits,
    } = course.ltpc;


    updateRow(
      index,
      "name",
      course.sub_name
    );

    updateRow(
      index,
      "sub_code",
      course.sub_code
    );

    updateRow(
      index,
      "theory_hours",
      lecture > 0
        ? lecture
        : ""
    );

    updateRow(
      index,
      "has_lab",
      practical > 0
    );

    updateRow(
      index,
      "lab_hours",
      practical > 0
        ? practical % 2 === 0
          ? practical
          : ""
        : ""
    );

    updateRow(
      index,
      "lab_type",
      practical > 0
        ? ""
        : ""
    );

    updateRow(
      index,
      "credits",
      credits ?? ""
    );

    /*
     * IMPORTANT:
     * Staff remains empty.
     */
  };


  /*
   * =======================================================
   * RENDER
   * =======================================================
   */

  return (

    <div className="batch-card">

      <div className="batch-card-header">

        <div className="batch-title-wrap">

          <div
            className={`batch-icon-badge batch-icon-${
              batch
                ? String(
                    batch
                  ).toLowerCase()
                : "default"
            }`}
          >
            {yearLabel} — Batch{" "}
            {batchLabel}
          </div>


          <div>

            <h3 className="batch-title">

              {yearLabel}{" "}
              (Batch {batchLabel})
              {" "}
              — Semester{" "}
              {semester}

              {" "}
              Curriculum & Faculty Allocation

            </h3>


            <p className="batch-subtitle">

              Select courses for this academic
              schedule and assign faculty.

            </p>

          </div>

        </div>


        <BatchStatsCard
          batchId={
            currentScheduleId
          }

          year={
            year
          }

          batch={
            batch
          }

          rows={
            rows
          }

          days={
            days
          }

          periods={
            periods
          }
        />

      </div>


      <div className="subject-table-wrap">

        <table className="subject-table">

          <thead>

            <tr>

              <th style={{ width: "5%" }}>
                Code
              </th>

              <th style={{ width: "22%" }}>
                Course Name
              </th>

              <th style={{ width: "8%" }}>
                Year
              </th>

              <th style={{ width: "8%" }}>
                Batch
              </th>

              <th style={{ width: "20%" }}>
                Faculty / Staff
              </th>

              <th
                style={{
                  width: "7%",
                  textAlign: "center",
                }}
              >
                L hrs/wk
              </th>

              <th
                style={{
                  width: "6%",
                  textAlign: "center",
                }}
              >
                Credits
              </th>

              <th
                style={{
                  width: "6%",
                  textAlign: "center",
                }}
              >
                Lab?
              </th>

              <th style={{ width: "12%" }}>
                P hrs / Type
              </th>

              <th style={{ width: "2%" }} />

            </tr>

          </thead>


          <tbody>

            {batchRows.length === 0 ? (

              <tr>

                <td
                  colSpan="10"
                  className="empty-table-msg"
                >

                  No courses added for{" "}
                  {yearLabel} — Batch{" "}
                  {batchLabel} — Semester{" "}
                  {semester}.

                  <br />

                  Click
                  {" "}
                  <strong>
                    Add Course
                  </strong>
                  {" "}
                  below.

                </td>

              </tr>

            ) : (

              batchRows.map(
                (row) => {

                  const index =
                    row.originalIndex;


                  const isLabInvalid =
                    row.has_lab &&
                    (
                      Number(
                        row.lab_hours
                      ) <= 0 ||

                      Number(
                        row.lab_hours
                      ) % 2 !== 0
                    );


                  return (

                    <tr
                      key={index}
                      className="subject-row"
                    >

                      {/* CODE */}

                      <td>

                        <span
                          className="text-xs text-muted"
                          style={{
                            fontFamily:
                              "monospace",
                            fontSize:
                              "0.75rem",
                            display:
                              "block",
                            padding:
                              "4px",
                          }}
                        >
                          {row.sub_code ||
                            "—"}
                        </span>

                      </td>


                      {/* COURSE */}

                      <td>

                        <select
                          className="form-control"

                          value={
                            row.sub_code ||
                            ""
                          }

                          onChange={(event) =>
                            handleCourseSelect(
                              index,
                              event.target.value
                            )
                          }

                          style={{
                            fontSize:
                              "0.82rem",
                          }}
                        >

                          <option value="">
                            — Select Course —
                          </option>

                          {semesterCourses.map(
                            (course) => (

                              <option
                                key={
                                  course.sub_code
                                }

                                value={
                                  course.sub_code
                                }
                              >

                                [
                                {
                                  course.sub_code
                                }
                                ]{" "}
                                {
                                  course.sub_name
                                }

                              </option>

                            )
                          )}

                        </select>

                      </td>


                      {/* YEAR */}

                      <td>

                        <select
                          className="form-control"
                          value={year}
                          disabled
                        >

                          <option
                            value={year}
                          >
                            {yearLabel}
                          </option>

                        </select>

                      </td>


                      {/* BATCH */}

                      <td>

                        <select
                          className="form-control"
                          value={batch}
                          disabled
                        >

                          <option
                            value={batch}
                          >
                            {batchLabel}
                          </option>

                        </select>

                      </td>


                      {/* FACULTY */}

                      <td>

                        <select
                          className="form-control"

                          value={
                            row.staff ||
                            ""
                          }

                          onChange={(event) =>
                            updateRow(
                              index,
                              "staff",
                              event.target.value
                            )
                          }
                        >

                          <option value="">
                            — Select Faculty —
                          </option>

                          {DEFAULT_STAFF.map(
                            (name) => (

                              <option
                                key={name}
                                value={name}
                              >
                                {name}
                              </option>

                            )
                          )}

                        </select>

                      </td>


                      {/* LECTURE HOURS */}

                      <td>

                        <input
                          type="number"
                          min="1"

                          className="form-control text-center"

                          value={
                            row.theory_hours ||
                            ""
                          }

                          onChange={(event) =>
                            updateRow(
                              index,
                              "theory_hours",
                              event.target.value
                            )
                          }

                        />

                      </td>


                      {/* CREDITS */}

                      <td>

                        <input
                          type="number"
                          min="0"

                          className="form-control text-center"

                          value={
                            row.credits ??
                            ""
                          }

                          placeholder="—"

                          onChange={(event) =>
                            updateRow(
                              index,
                              "credits",
                              event.target.value
                            )
                          }

                        />

                      </td>


                      {/* LAB */}

                      <td className="text-center">

                        <label className="checkbox-wrap">

                          <input
                            type="checkbox"

                            checked={
                              Boolean(
                                row.has_lab
                              )
                            }

                            onChange={(event) => {

                              const checked =
                                event.target.checked;

                              updateRow(
                                index,
                                "has_lab",
                                checked
                              );

                              if (!checked) {

                                updateRow(
                                  index,
                                  "lab_hours",
                                  ""
                                );

                                updateRow(
                                  index,
                                  "lab_type",
                                  ""
                                );

                              }

                            }}
                          />

                          <span className="checkbox-custom" />

                          <span className="checkbox-label">
                            Lab
                          </span>

                        </label>

                      </td>


                      {/* LAB HOURS */}

                      <td>

                        <div
                          style={{
                            display:
                              "flex",
                            gap:
                              "4px",
                          }}
                        >

                          <input
                            type="number"
                            min="2"
                            step="2"

                            disabled={
                              !row.has_lab
                            }

                            className={`form-control text-center ${
                              isLabInvalid
                                ? "input-error"
                                : ""
                            }`}

                            value={
                              row.has_lab
                                ? row.lab_hours ||
                                  ""
                                : ""
                            }

                            onChange={(event) =>
                              updateRow(
                                index,
                                "lab_hours",
                                event.target.value
                              )
                            }

                            placeholder={
                              row.has_lab
                                ? "2, 4…"
                                : "—"
                            }

                            style={{
                              width:
                                "70px",
                            }}

                          />


                          {row.has_lab && (

                            <select
                              className="form-control"

                              value={
                                row.lab_type ||
                                ""
                              }

                              onChange={(event) =>
                                updateRow(
                                  index,
                                  "lab_type",
                                  event.target.value
                                )
                              }

                              style={{
                                padding:
                                  "2px 4px",
                                fontSize:
                                  "0.78rem",
                              }}
                            >

                              <option value="">
                                — Type —
                              </option>

                              <option value="AC">
                                AC Lab
                              </option>

                              <option value="NON_AC">
                                Non-AC
                              </option>

                            </select>

                          )}

                        </div>

                      </td>


                      {/* REMOVE */}

                      <td className="text-center">

                        <button
                          type="button"
                          className="btn-icon-danger"

                          title="Remove Course"

                          onClick={() =>
                            removeRow(
                              index
                            )
                          }
                        >
                          ✕
                        </button>

                      </td>

                    </tr>

                  );

                }
              )

            )}

          </tbody>

        </table>

      </div>


      {/* =================================================
          ADD COURSE
      ================================================= */}

      <div className="batch-card-footer">

        <button
          type="button"
          className="btn btn-secondary btn-sm"

          onClick={() =>
            addRow({
              year:
                Number(year),

              batch,

              semester:
                Number(semester),
            })
          }
        >

          +

          {" "}

          Add Course for{" "}
          {yearLabel} —
          {" "}
          {batchLabel} —
          {" "}
          Semester{" "}
          {semester}

        </button>

      </div>

    </div>
  );
}