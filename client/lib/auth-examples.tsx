/**
 * Authentication Usage Examples
 * 
 * This file contains practical examples of how to use the authentication system
 * in your React components.
 */

import { useAuth } from '@/hooks/use-auth';
import { authService } from '@/lib/auth';
import { useNavigate } from 'react-router-dom';
import { toast } from '@/lib/toast';

// ============================================================================
// Example 1: Simple Login Component
// ============================================================================

export function SimpleLoginExample() {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (email: string, password: string) => {
    try {
      await login({ email, password });
      toast.success('Welcome back!');
      navigate('/app');
    } catch (error) {
      toast.error('Login failed', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  return (
    <button onClick={() => handleLogin('user@example.com', 'password')} disabled={isLoading}>
      {isLoading ? 'Logging in...' : 'Login'}
    </button>
  );
}

// ============================================================================
// Example 2: User Profile Display
// ============================================================================

export function UserProfileExample() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated || !user) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <h2>Profile</h2>
      <p>Email: {user.email}</p>
      <p>User ID: {user.id}</p>
      <p>Joined: {new Date(user.created_at).toLocaleDateString()}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

// ============================================================================
// Example 3: Fetching User's Courses (Authenticated Request)
// ============================================================================

export function UserCoursesExample() {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCourses() {
      try {
        const response = await authService.fetchWithAuth('/api/courses');
        
        if (!response.ok) {
          throw new Error('Failed to fetch courses');
        }
        
        const data = await response.json();
        setCourses(data);
      } catch (error) {
        toast.error('Error', 'Failed to load courses');
      } finally {
        setLoading(false);
      }
    }

    fetchCourses();
  }, []);

  if (loading) return <div>Loading courses...</div>;

  return (
    <div>
      <h2>My Courses</h2>
      {courses.map(course => (
        <div key={course.id}>{course.name}</div>
      ))}
    </div>
  );
}

// ============================================================================
// Example 4: Creating a New Course (POST Request)
// ============================================================================

export function CreateCourseExample() {
  const [courseName, setCourseName] = useState('');

  const handleCreateCourse = async () => {
    try {
      const response = await authService.fetchWithAuth('/api/courses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: courseName }),
      });

      if (!response.ok) {
        throw new Error('Failed to create course');
      }

      const newCourse = await response.json();
      toast.success('Course created!', newCourse.name);
      setCourseName('');
    } catch (error) {
      toast.error('Error', 'Failed to create course');
    }
  };

  return (
    <div>
      <input
        value={courseName}
        onChange={(e) => setCourseName(e.target.value)}
        placeholder="Course name"
      />
      <button onClick={handleCreateCourse}>Create Course</button>
    </div>
  );
}

// ============================================================================
// Example 5: Loading and Displaying User Preferences
// ============================================================================

export function UserPreferencesExample() {
  const { getPreferences } = useAuth();
  const [preferences, setPreferences] = useState<any>(null);

  useEffect(() => {
    async function loadPreferences() {
      const prefs = await getPreferences();
      setPreferences(prefs);
    }
    loadPreferences();
  }, [getPreferences]);

  if (!preferences) {
    return <div>Loading preferences...</div>;
  }

  return (
    <div>
      <h2>Your Learning Preferences</h2>
      <p>Detail Level: {(preferences.detail_level * 100).toFixed(0)}%</p>
      <p>Learning Pace: {preferences.learning_pace}</p>
      <p>Prior Experience: {preferences.prior_experience}</p>
    </div>
  );
}

// ============================================================================
// Example 6: Conditional Rendering Based on Auth State
// ============================================================================

export function ConditionalContentExample() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Checking authentication...</div>;
  }

  return (
    <div>
      {isAuthenticated ? (
        <div>
          <h1>Welcome to your dashboard!</h1>
          <p>You have access to all features</p>
        </div>
      ) : (
        <div>
          <h1>Welcome to StudyMate</h1>
          <p>Please log in to access your courses</p>
          <a href="/login">Login</a>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Example 7: Signup with Academic Profile
// ============================================================================

export function SignupWithProfileExample() {
  const { signup, saveAcademicProfile } = useAuth();
  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      // Step 1: Create account
      await signup({
        email: 'newuser@example.com',
        password: 'securepassword123',
      });

      // Step 2: Save academic profile
      await saveAcademicProfile({
        grade: ['Bachelor'],
        semester_type: 'double',
        semester: 3,
        subject: ['Computer Science', 'Mathematics'],
      });

      toast.success('Account created!');
      navigate('/onboarding');
    } catch (error) {
      toast.error('Signup failed', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  return <button onClick={handleSignup}>Complete Signup</button>;
}

// ============================================================================
// Example 8: Logout with Confirmation
// ============================================================================

export function LogoutWithConfirmationExample() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const confirmed = window.confirm('Are you sure you want to logout?');
    
    if (confirmed) {
      try {
        await logout();
        toast.success('Logged out successfully');
        navigate('/');
      } catch (error) {
        toast.error('Logout failed');
      }
    }
  };

  return <button onClick={handleLogout}>Logout</button>;
}

// ============================================================================
// Example 9: Check Session Validity
// ============================================================================

export function SessionCheckExample() {
  const [sessionValid, setSessionValid] = useState<boolean | null>(null);

  useEffect(() => {
    async function checkSession() {
      const session = await authService.getSession();
      setSessionValid(!!session);
    }
    checkSession();
  }, []);

  if (sessionValid === null) {
    return <div>Checking session...</div>;
  }

  return (
    <div>
      Session Status: {sessionValid ? '✅ Valid' : '❌ Invalid'}
    </div>
  );
}

// ============================================================================
// Example 10: Custom Hook for Authenticated Data Fetching
// ============================================================================

function useAuthenticatedFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const response = await authService.fetchWithAuth(url);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setData(null);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [url]);

  return { data, loading, error };
}

// Usage of the custom hook
export function CustomHookExample() {
  const { data: courses, loading, error } = useAuthenticatedFetch<any[]>('/api/courses');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!courses) return <div>No courses found</div>;

  return (
    <div>
      {courses.map(course => (
        <div key={course.id}>{course.name}</div>
      ))}
    </div>
  );
}
