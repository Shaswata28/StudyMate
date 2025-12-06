/**
 * Shared code between client and server
 * Useful to share types between client and server
 * and/or small pure JS functions that can be used on both client and server
 */

/**
 * Example response type for /api/demo
 */
export interface DemoResponse {
  message: string;
}

/**
 * Response type for /api/transcribe
 */
export interface TranscriptionResponse {
  text: string;
  success: boolean;
  error?: string;
}
