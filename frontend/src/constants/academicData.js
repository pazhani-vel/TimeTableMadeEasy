export const DEFAULT_STAFF = [
  "Dr. Radha Senthilkumar",
  "Dr. P. AnandhaKumar",
  "Dr. Dhananjay Kumar",
  "Dr. M.R. Sumalatha",
  "Dr. R. Geetha Ramani",
  "Dr. P. Kola Sujatha",
  "Dr. S. Umamaheswari",
  "Dr. G. Rajesh",
  "Dr. J. Dhalia Sweetlin",
  "Dr. B. Lydia Elizabeth",
  "M. Hemalatha",
  "S.K. Lavanya",
  "C. Sunil Retmin Raj",
  "E. Pugazhendi",
  "Dr. D. Vivekanandan",
  "P. Seethalakshmi",
  "Kannan sir",
  "CN Mam",
  "Prathiba",
  "Durga Devi",
  "Industry Person",
  "Guest Faculty"
];

export const YEARS = [
  { value: 2, label: "2nd Year" },
  { value: 3, label: "3rd Year" },
  { value: 4, label: "4th Year" }
];

export const BATCH_OPTIONS = [
  { value: "B1", label: "IT Batch B1" },
  { value: "B2", label: "IT Batch B2" },
  { value: "AIDS_B1", label: "AIDS Batch B1" }
];

export const YEAR_TO_SEMESTERS = {
  2: [3, 4],
  3: [5, 6],
  4: [7, 8],
};

export const SEMESTER_OPTIONS = [
  { value: 3, label: "Semester 3" },
  { value: 4, label: "Semester 4" },
  { value: 5, label: "Semester 5" },
  { value: 6, label: "Semester 6" },
  { value: 7, label: "Semester 7" },
  { value: 8, label: "Semester 8" },
];

export const ALL_IT_BATCHES = [
  { id: "IT_2_B1", department: "IT", year: 2, batch: "B1", label: "2nd Year - IT Batch B1" },
  { id: "IT_2_B2", department: "IT", year: 2, batch: "B2", label: "2nd Year - IT Batch B2" },
  { id: "AIDS_2_B1", department: "AIDS", year: 2, batch: "AIDS_B1", label: "2nd Year - AIDS Batch B1" },
  { id: "IT_3_B1", department: "IT", year: 3, batch: "B1", label: "3rd Year - IT Batch B1" },
  { id: "IT_3_B2", department: "IT", year: 3, batch: "B2", label: "3rd Year - IT Batch B2" },
  { id: "AIDS_3_B1", department: "AIDS", year: 3, batch: "AIDS_B1", label: "3rd Year - AIDS Batch B1" },
  { id: "IT_4_B1", department: "IT", year: 4, batch: "B1", label: "4th Year - IT Batch B1" },
  { id: "IT_4_B2", department: "IT", year: 4, batch: "B2", label: "4th Year - IT Batch B2" },
  { id: "AIDS_4_B1", department: "AIDS", year: 4, batch: "AIDS_B1", label: "4th Year - AIDS Batch B1" }
];

export const DEFAULT_LABS = [
  { id: "IT_LAB1", name: "IT Lab 1", department: "IT", type: "AC", capacity: 1 },
  { id: "IT_LAB2", name: "IT Lab 2", department: "IT", type: "AC", capacity: 1 },
  { id: "IT_LAB3", name: "IT Lab 3", department: "IT", type: "NON_AC", capacity: 1 },
  { id: "AIDS_LAB1", name: "AIDS Lab 1", department: "AIDS", type: "AC", capacity: 1 },
  { id: "AIDS_LAB2", name: "AIDS Lab 2", department: "AIDS", type: "AC", capacity: 1 }
];

export const PERIOD_TIME_SLOTS = [
  { index: 0, label: "P1", time: "08:30 – 09:20" },
  { index: 1, label: "P2", time: "09:20 – 10:10" },
  { index: 2, label: "P3", time: "10:25 – 11:15" },
  { index: 3, label: "P4", time: "11:15 – 12:05" },
  { lunch: true, label: "LUNCH", time: "12:05 – 01:00" },
  { index: 4, label: "P5", time: "01:00 – 01:50" },
  { index: 5, label: "P6", time: "01:50 – 02:40" },
  { index: 6, label: "P7", time: "02:55 – 03:45" },
  { index: 7, label: "P8", time: "03:45 – 04:35" }
];

export const SAMPLE_CURRICULUM_PRESET = [
  // 2nd Year - Batch B1 (Semester 3)
  { year: 2, batch: "B1", batch_id: "IT_2_B1", sub_code: "IT23302", name: "Data Structures", credits: 4, staff: "Dr. Radha Senthilkumar", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 2, batch: "B1", batch_id: "IT_2_B1", sub_code: "IT23304", name: "Object Oriented Programming", credits: 2, staff: "Dr. P. AnandhaKumar", theory_hours: 1, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 2, batch: "B1", batch_id: "IT_2_B1", sub_code: "IT23301", name: "Digital Logic and Design", credits: 4, staff: "M. Hemalatha", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },

  // 2nd Year - Batch B2 (Semester 3)
  { year: 2, batch: "B2", batch_id: "IT_2_B2", sub_code: "IT23302", name: "Data Structures", credits: 4, staff: "Dr. P. Kola Sujatha", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 2, batch: "B2", batch_id: "IT_2_B2", sub_code: "IT23304", name: "Object Oriented Programming", credits: 2, staff: "Dr. S. Umamaheswari", theory_hours: 1, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 2, batch: "B2", batch_id: "IT_2_B2", sub_code: "IT23303", name: "Database Management Systems", credits: 4, staff: "Dr. R. Geetha Ramani", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },

  // 3rd Year - Batch B1 (Semester 5)
  { year: 3, batch: "B1", batch_id: "IT_3_B1", sub_code: "IT23501", name: "Computer Networks", credits: 4, staff: "Dr. Dhananjay Kumar", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 3, batch: "B1", batch_id: "IT_3_B1", sub_code: "IT23502", name: "Web Programming", credits: 4, staff: "S.K. Lavanya", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "NON_AC" },
  { year: 3, batch: "B1", batch_id: "IT_3_B1", sub_code: "IT23503", name: "Compiler Design", credits: 3, staff: "E. Pugazhendi", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },

  // 3rd Year - Batch B2 (Semester 5)
  { year: 3, batch: "B2", batch_id: "IT_3_B2", sub_code: "IT23501", name: "Computer Networks", credits: 4, staff: "Dr. G. Rajesh", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 3, batch: "B2", batch_id: "IT_3_B2", sub_code: "IT23504", name: "Machine Learning", credits: 4, staff: "Dr. J. Dhalia Sweetlin", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "NON_AC" },
  { year: 3, batch: "B2", batch_id: "IT_3_B2", sub_code: "IT23503", name: "Compiler Design", credits: 3, staff: "C. Sunil Retmin Raj", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },

  // 4th Year - Batch B1 (Semester 7)
  { year: 4, batch: "B1", batch_id: "IT_4_B1", sub_code: "IT23701", name: "Cryptography and Network Security", credits: 4, staff: "Dr. M.R. Sumalatha", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 4, batch: "B1", batch_id: "IT_4_B1", sub_code: "PEC-IV", name: "Professional Elective IV", credits: 3, staff: "Dr. B. Lydia Elizabeth", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },
  { year: 4, batch: "B1", batch_id: "IT_4_B1", sub_code: "IT23702", name: "Software Development Project Laboratory", credits: 2, staff: "Dr. D. Vivekanandan", theory_hours: 0, has_lab: true, lab_hours: 4, lab_type: "NON_AC" },

  // 4th Year - Batch B2 (Semester 7)
  { year: 4, batch: "B2", batch_id: "IT_4_B2", sub_code: "IT23701", name: "Cryptography and Network Security", credits: 4, staff: "P. Seethalakshmi", theory_hours: 3, has_lab: true, lab_hours: 2, lab_type: "AC" },
  { year: 4, batch: "B2", batch_id: "IT_4_B2", sub_code: "PEC-V", name: "Professional Elective V", credits: 3, staff: "Kannan sir", theory_hours: 3, has_lab: false, lab_hours: 0, lab_type: null },
  { year: 4, batch: "B2", batch_id: "IT_4_B2", sub_code: "IT23702", name: "Software Development Project Laboratory", credits: 2, staff: "CN Mam", theory_hours: 0, has_lab: true, lab_hours: 4, lab_type: "NON_AC" }
];

