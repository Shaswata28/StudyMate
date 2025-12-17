# Design Document

## Overview

This feature adds data persistence to the chat interface by loading chat history and materials from the database when users refresh the page or switch courses. The backend already provides the necessary API endpoints (`GET /api/courses/{course_id}/chat` and `GET /api/courses/{course_id}/materials`), so this is primarily a frontend enhancement to call these endpoints and manage the loading states.

The design follows React best practices with useEffect hooks for data fetching, proper loading state management, error handling, and cleanup to prevent memory leaks.

## Architecture

### Component Structure

```
Dashboard (main component)
├── useEffect: Load courses on mount
├── useEffect: Load chat history when activeCourse changes
├── useEffect: Load materials when activeCourse changes
└── Components:
    ├── Sidebar (course selection)
    ├── Header
    └── Workspace (chat + materials display)
```

### Data Flow

1. **Initial Load**: Dashboard mounts → Load courses → Set first course as active
2. **Course Selection**: User selects course → Trigger chat history and materials fetch
3. **Data Fetching**: Parallel requests to chat and materials endpoints
4. **State Updates**: Update messages and uploadedFiles state with fetched data
5. **Error Handling**: Display toast notifications for errors, allow retry

## Components and Interfaces

### API Service Layer

Create a new service module `client/lib/api.ts` to centralize API calls:

```typescript
// Chat History API
export interface ChatHistoryRecord {
  id: string;
  course_id: string;
  history: Array<{
    role: 'user' | 'model';
    content: string;
  }>;
  created_at: string;
}

export async function getChatHistory(courseId: string): Promise<ChatHistoryRecord[]> {
  // GET /api/courses/{courseId}/chat
}

// Materials API
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

export async function getMaterials(courseId: string): Promise<MaterialRecord[]> {
  // GET /api/courses/{courseId}/materials
}
```

### Dashboard Component Updates

Add new state variables:
```typescript
const [isLoadingChatHistory, setIsLoadingChatHistory] = useState(false);
const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);
const [chatHistoryError, setChatHistoryError] = useState<string | null>(null);
const [materialsError, setMaterialsError] = useState<string | null>(null);
```

Add data fetching functions:
```typescript
const loadChatHistory = async (courseId: string) => {
  // Fetch and transform chat history
}

const loadMaterials = async (courseId: string) => {
  // Fetch and transform materials
}
```

Add useEffect hooks:
```typescript
// Load chat history when active course changes
useEffect(() => {
  if (activeCourse) {
    loadChatHistory(activeCourse.id);
  }
}, [activeCourse?.id]);

// Load materials when active course changes
useEffect(() => {
  if (activeCourse) {
    loadMaterials(activeCourse.id);
  }
}, [activeCourse?.id]);
```

## Data Models

### Message Transformation

Backend chat history format:
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "model", "content": "Hi there!" }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

Frontend Message format:
```typescript
interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
  attachments?: { name: string; type: string }[];
}
```

Transformation logic:
- Flatten all history arrays into a single messages array
- Convert role 'user' → isAI: false, role 'model' → isAI: true
- Use created_at as timestamp for all messages in that record
- Generate unique IDs for each message

### Material Transformation

Backend material format:
```json
{
  "id": "uuid",
  "name": "document.pdf",
  "file_type": "application/pdf",
  "processing_status": "completed",
  ...
}
```

Frontend UploadedFile format:
```typescript
interface UploadedFile {
  id: string;
  name: string;
  type: string;
  file?: File;
}
```

Transformation logic:
- Map id → id
- Map name → name
- Map file_type → type
- Don't include file property (only used for pending uploads)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Chat history chronological ordering

*For any* course with chat history, when the chat history is loaded, the messages should be displayed in chronological order based on their created_at timestamps.

**Validates: Requirements 1.3**

### Property 2: Material list completeness

*For any* course with uploaded materials, when the materials are loaded, all materials from the database should be present in the uploadedFiles state.

**Validates: Requirements 2.3**

### Property 3: Loading state consistency

*For any* data fetch operation, the loading state should be true during the fetch and false after completion (success or failure).

**Validates: Requirements 3.1, 3.3**

### Property 4: Error state isolation

*For any* failed data fetch, the error should only affect that specific data type (chat or materials) and not prevent other data from loading.

**Validates: Requirements 3.2**

### Property 5: State cleanup on course switch

*For any* course switch operation, the previous course's chat history should be cleared before the new course's history is loaded.

**Validates: Requirements 1.5**

## Error Handling

### Error Types and Responses

1. **Network Errors** (fetch fails)
   - Display: "Unable to connect. Please check your internet connection."
   - Action: Provide retry button
   - Log: Full error details

2. **Authentication Errors** (401, 403)
   - Display: "Session expired. Please log in again."
   - Action: Redirect to login page
   - Log: Error details

3. **Not Found Errors** (404)
   - Display: "Course not found."
   - Action: Refresh course list
   - Log: Course ID and error

4. **Server Errors** (500, 503)
   - Display: "Something went wrong. Please try again."
   - Action: Provide retry button
   - Log: Full error details

### Error Handling Strategy

```typescript
try {
  // Fetch data
} catch (error) {
  if (error.status === 401 || error.status === 403) {
    // Redirect to login
    authService.logout();
    navigate('/login');
  } else if (error.status === 404) {
    // Show not found message
    toast.error('Course not found');
  } else {
    // Generic error
    toast.error('Failed to load data. Please try again.');
  }
  // Log for debugging
  console.error('Data fetch error:', error);
}
```

### Graceful Degradation

- If chat history fails to load, show empty chat with error message
- If materials fail to load, show empty materials list with error message
- Allow users to continue using the app even if some data fails to load
- Provide retry buttons for failed operations

## Testing Strategy

### Unit Tests

1. **Message Transformation Tests**
   - Test converting backend chat history to frontend messages
   - Test handling empty history arrays
   - Test timestamp conversion
   - Test ID generation uniqueness

2. **Material Transformation Tests**
   - Test converting backend materials to frontend format
   - Test handling different processing statuses
   - Test handling missing optional fields

3. **Error Handling Tests**
   - Test different error status codes
   - Test network failure scenarios
   - Test error message display

### Property-Based Tests

Property-based tests will use `fast-check` library for TypeScript. Each test should run a minimum of 100 iterations.

1. **Property 1: Chat history chronological ordering**
   - Generate random chat history records with various timestamps
   - Load and transform them
   - Verify messages are in chronological order

2. **Property 2: Material list completeness**
   - Generate random material records
   - Load and transform them
   - Verify all materials are present in the result

3. **Property 3: Loading state consistency**
   - Generate random fetch scenarios (success/failure)
   - Track loading state changes
   - Verify loading is true during fetch and false after

4. **Property 4: Error state isolation**
   - Generate random error scenarios for chat and materials
   - Verify errors don't affect unrelated data

5. **Property 5: State cleanup on course switch**
   - Generate random course switches
   - Verify previous chat history is cleared before new history loads

### Integration Tests

1. Test full flow: mount → load courses → select course → load chat + materials
2. Test course switching: select course A → load data → select course B → verify data changes
3. Test error recovery: fail to load → retry → success
4. Test concurrent loading: verify chat and materials load independently

## Implementation Notes

### Authentication

All API calls must include the authentication token from the auth service:

```typescript
const token = authService.getAccessToken();
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Cleanup and Memory Leaks

Use AbortController to cancel pending requests when component unmounts or course changes:

```typescript
useEffect(() => {
  const abortController = new AbortController();
  
  loadChatHistory(courseId, abortController.signal);
  
  return () => {
    abortController.abort();
  };
}, [courseId]);
```

### Performance Considerations

- Load chat history and materials in parallel (not sequential)
- Consider pagination for large chat histories (future enhancement)
- Cache loaded data to avoid redundant fetches when switching back to a course
- Use React.memo for message components to prevent unnecessary re-renders

### Backward Compatibility

- Existing functionality (sending messages, uploading files) should continue to work
- New messages should be appended to loaded history
- Newly uploaded files should be added to loaded materials list
- No breaking changes to existing components
