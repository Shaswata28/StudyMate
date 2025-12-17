/**
 * Course Service
 * 
 * Handles all course-related API operations
 */

import { authService } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export interface Course {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface CourseCreate {
  name: string;
}

/**
 * Course Service Class
 */
class CourseService {
  /**
   * Create a new course
   */
  async createCourse(data: CourseCreate): Promise<Course> {
    try {
      const response = await authService.fetchWithAuth(`${API_BASE_URL}/courses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create course');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to create course');
    }
  }

  /**
   * Get all courses for the current user
   */
  async getCourses(): Promise<Course[]> {
    try {
      const response = await authService.fetchWithAuth(`${API_BASE_URL}/courses`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch courses');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch courses');
    }
  }

  /**
   * Get a specific course by ID
   */
  async getCourse(courseId: string): Promise<Course> {
    try {
      const response = await authService.fetchWithAuth(`${API_BASE_URL}/courses/${courseId}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch course');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch course');
    }
  }

  /**
   * Update a course name
   */
  async updateCourse(courseId: string, data: CourseCreate): Promise<Course> {
    try {
      const response = await authService.fetchWithAuth(`${API_BASE_URL}/courses/${courseId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update course');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to update course');
    }
  }

  /**
   * Delete a course
   */
  async deleteCourse(courseId: string): Promise<void> {
    try {
      const response = await authService.fetchWithAuth(`${API_BASE_URL}/courses/${courseId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete course');
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to delete course');
    }
  }
}

// Export singleton instance
export const courseService = new CourseService();
