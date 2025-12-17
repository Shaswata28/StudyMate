/**
 * API Service Layer
 * 
 * Handles data fetching for chat history and materials
 */

import { authService } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Chat History Types
export interface ChatHistoryRecord {
  id: string;
  course_id: string;
  history: Array<{
    role: 'user' | 'model';
    content: string;
  }>;
  created_at: string;
}

// Material Types
export interface MaterialRecord {
  id: string;
  course_id: string;
  name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processed_at: string | null;
  error_message: string | null;
  has_embedding: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * API Service Class
 */
class ApiService {
  /**
   * Get chat history for a specific course
   * 
   * @param courseId - UUID of the course
   * @param signal - Optional AbortSignal for request cancellation
   * @returns Array of chat history records
   * @throws Error if request fails
   */
  async getChatHistory(courseId: string, signal?: AbortSignal): Promise<ChatHistoryRecord[]> {
    try {
      const response = await authService.fetchWithAuth(
        `${API_BASE_URL}/courses/${courseId}/chat`,
        { signal }
      );

      if (!response.ok) {
        const error = await this.extractErrorMessage(response);
        throw new Error(error);
      }

      const data: ChatHistoryRecord[] = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch chat history');
    }
  }

  /**
   * Get materials for a specific course
   * 
   * @param courseId - UUID of the course
   * @param signal - Optional AbortSignal for request cancellation
   * @returns Array of material records
   * @throws Error if request fails
   */
  async getMaterials(courseId: string, signal?: AbortSignal): Promise<MaterialRecord[]> {
    try {
      const response = await authService.fetchWithAuth(
        `${API_BASE_URL}/courses/${courseId}/materials`,
        { signal }
      );

      if (!response.ok) {
        const error = await this.extractErrorMessage(response);
        throw new Error(error);
      }

      const data: MaterialRecord[] = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch materials');
    }
  }

  /**
   * Extract error message from response
   * Handles various error response formats
   */
  private async extractErrorMessage(response: Response): Promise<string> {
    try {
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const error = await response.json();
        
        // Extract from detail field (FastAPI standard)
        if (error.detail) {
          if (typeof error.detail === 'string') {
            return error.detail;
          } else if (typeof error.detail === 'object' && error.detail.message) {
            return error.detail.message;
          }
        }
        
        // Fallback to message field
        if (error.message) {
          return error.message;
        }
        
        // Fallback to error field
        if (error.error) {
          return error.error;
        }
      }
    } catch (e) {
      console.error('Failed to parse error response:', e);
    }
    
    // Default error messages based on status code
    switch (response.status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'Session expired. Please log in again.';
      case 403:
        return 'You do not have permission to access this resource.';
      case 404:
        return 'Course not found.';
      case 500:
        return 'Something went wrong. Please try again.';
      case 503:
        return 'Service temporarily unavailable. Please try again.';
      default:
        return `Request failed with status ${response.status}`;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

/**
 * Frontend Data Types
 */
export interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
  attachments?: { name: string; type: string }[];
}

export interface UploadedFile {
  id: string;
  name: string;
  type: string;
  file?: File;
}

/**
 * Data Transformation Utilities
 */

/**
 * Transform backend chat history records to frontend Message format
 * 
 * Flattens all history arrays into a single messages array, converting:
 * - role 'user' → isAI: false
 * - role 'model' → isAI: true
 * - created_at timestamp for all messages in that record
 * - Generates unique IDs for each message
 * 
 * @param records - Array of chat history records from backend
 * @returns Array of Message objects for frontend
 */
export function transformChatHistory(records: ChatHistoryRecord[]): Message[] {
  // Handle null, undefined, or empty arrays
  if (!records || !Array.isArray(records) || records.length === 0) {
    return [];
  }

  const messages: Message[] = [];

  for (const record of records) {
    // Skip records with invalid or empty history
    if (!record.history || !Array.isArray(record.history) || record.history.length === 0) {
      continue;
    }

    // Parse timestamp once for all messages in this record
    const timestamp = record.created_at ? new Date(record.created_at) : undefined;

    // Transform each message in the history array
    for (let i = 0; i < record.history.length; i++) {
      const historyItem = record.history[i];
      
      // Skip invalid history items
      if (!historyItem || typeof historyItem.content !== 'string') {
        continue;
      }

      // Generate unique ID: record_id + index + timestamp
      const messageId = `${record.id}-${i}-${record.created_at || Date.now()}`;

      messages.push({
        id: messageId,
        text: historyItem.content,
        isAI: historyItem.role === 'model',
        timestamp: timestamp,
      });
    }
  }

  // Sort messages by timestamp (oldest first) for chronological order
  messages.sort((a, b) => {
    if (!a.timestamp && !b.timestamp) return 0;
    if (!a.timestamp) return -1;
    if (!b.timestamp) return 1;
    return a.timestamp.getTime() - b.timestamp.getTime();
  });

  return messages;
}

/**
 * Transform backend material records to frontend UploadedFile format
 * 
 * Converts backend material format to frontend format:
 * - Maps id → id
 * - Maps name → name
 * - Maps file_type → type
 * - Omits file property (only used for pending uploads)
 * 
 * @param records - Array of material records from backend
 * @returns Array of UploadedFile objects for frontend
 */
export function transformMaterials(records: MaterialRecord[]): UploadedFile[] {
  // Handle null, undefined, or empty arrays
  if (!records || !Array.isArray(records) || records.length === 0) {
    return [];
  }

  return records
    .filter(record => {
      // Filter out invalid records
      return record && 
             typeof record.id === 'string' && 
             typeof record.name === 'string' && 
             typeof record.file_type === 'string';
    })
    .map(record => ({
      id: record.id,
      name: record.name,
      type: record.file_type,
      // Note: file property is omitted - only used for pending uploads
    }));
}
