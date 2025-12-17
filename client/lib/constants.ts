/**
 * Application Constants
 * 
 * Centralized constants to ensure consistency across the application.
 * These should match the backend constants in python-backend/constants.py
 */

// Academic Profile Constants

export const VALID_GRADES = ['Bachelor', 'Masters'] as const;
export type Grade = typeof VALID_GRADES[number];

export const VALID_SEMESTER_TYPES = ['double', 'tri'] as const;
export type SemesterType = typeof VALID_SEMESTER_TYPES[number];

export const MIN_SEMESTER = 1;
export const MAX_SEMESTER = 12;

// Subject options (must match backend)
export const SUBJECTS = [
  { value: 'computer science', label: 'CS' },
  { value: 'electrical and electronics engineering', label: 'EEE' },
  { value: 'english', label: 'English' },
  { value: 'business administration', label: 'BA' },
  { value: 'economics', label: 'Economics' },
] as const;

export type SubjectValue = typeof SUBJECTS[number]['value'];

// User Preferences Constants

export const LEARNING_PACE_OPTIONS = [
  { value: 'slow', label: 'Slow - Take my time' },
  { value: 'moderate', label: 'Moderate - Steady pace' },
  { value: 'fast', label: 'Fast - Move quickly' },
] as const;

export type LearningPace = typeof LEARNING_PACE_OPTIONS[number]['value'];

export const PRIOR_EXPERIENCE_OPTIONS = [
  { value: 'beginner', label: "I'm just starting / struggling with basics" },
  { value: 'intermediate', label: 'I have moderate understanding' },
  { value: 'advanced', label: "I'm confident with the material" },
  { value: 'expert', label: "I'm advanced / helping others" },
] as const;

export type PriorExperience = typeof PRIOR_EXPERIENCE_OPTIONS[number]['value'];

// File Upload Constants

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB in bytes
export const MAX_FILE_SIZE_MB = 50;

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/plain',
  'text/markdown',
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
] as const;

export const ALLOWED_FILE_EXTENSIONS = [
  '.pdf',
  '.doc',
  '.docx',
  '.ppt',
  '.pptx',
  '.txt',
  '.md',
  '.jpg',
  '.jpeg',
  '.png',
  '.gif',
  '.webp',
] as const;

// Validation Constants

export const MIN_PASSWORD_LENGTH = 8;
export const MAX_PASSWORD_LENGTH = 100;

export const MIN_NAME_LENGTH = 2;
export const MAX_NAME_LENGTH = 255;

export const MIN_COURSE_NAME_LENGTH = 1;
export const MAX_COURSE_NAME_LENGTH = 255;

// API Constants

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Storage Constants

export const STORAGE_BUCKET_NAME = 'course-materials';

// Helper Functions

/**
 * Get subject label from value
 */
export function getSubjectLabel(value: string): string {
  const subject = SUBJECTS.find(s => s.value === value);
  return subject?.label || value;
}

/**
 * Check if file type is allowed
 */
export function isFileTypeAllowed(mimeType: string): boolean {
  return ALLOWED_FILE_TYPES.includes(mimeType as any);
}

/**
 * Check if file size is within limit
 */
export function isFileSizeValid(sizeInBytes: number): boolean {
  return sizeInBytes <= MAX_FILE_SIZE;
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
