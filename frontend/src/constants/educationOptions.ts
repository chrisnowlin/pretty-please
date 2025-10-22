/**
 * Educational options for lesson plan generation.
 */

export const GRADE_LEVELS = [
  { value: "K", label: "Kindergarten" },
  { value: "1", label: "1st Grade" },
  { value: "2", label: "2nd Grade" },
  { value: "3", label: "3rd Grade" },
  { value: "4", label: "4th Grade" },
  { value: "5", label: "5th Grade" },
  { value: "6", label: "6th Grade" },
  { value: "7", label: "7th Grade" },
  { value: "8", label: "8th Grade" },
  { value: "9", label: "9th Grade" },
  { value: "10", label: "10th Grade" },
  { value: "11", label: "11th Grade" },
  { value: "12", label: "12th Grade" },
  { value: "3-5", label: "Grades 3-5" },
  { value: "6-8", label: "Grades 6-8" },
  { value: "9-12", label: "Grades 9-12" },
  { value: "College", label: "College" },
] as const;

export const SUBJECTS = [
  { value: "Mathematics", label: "Mathematics" },
  { value: "Science", label: "Science" },
  { value: "English Language Arts", label: "English Language Arts" },
  { value: "Social Studies", label: "Social Studies" },
  { value: "History", label: "History" },
  { value: "Geography", label: "Geography" },
  { value: "Art", label: "Art" },
  { value: "Music", label: "Music" },
  { value: "Physical Education", label: "Physical Education" },
  { value: "Technology", label: "Technology" },
  { value: "Computer Science", label: "Computer Science" },
  { value: "Foreign Language", label: "Foreign Language" },
] as const;

export const TEACHING_STYLES = [
  { value: "balanced", label: "Balanced" },
  { value: "direct", label: "Direct Instruction" },
  { value: "inquiry", label: "Inquiry-Based" },
  { value: "project", label: "Project-Based" },
] as const;

export const DEFAULT_DURATION = 50;
export const MIN_DURATION = 20;
export const MAX_DURATION = 90;
