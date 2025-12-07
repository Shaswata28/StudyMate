# Implementation Plan

- [x] 1. Create API service layer for data fetching





  - Create `client/lib/api.ts` with TypeScript interfaces for chat history and materials
  - Implement `getChatHistory(courseId)` function that calls `GET /api/courses/{courseId}/chat`
  - Implement `getMaterials(courseId)` function that calls `GET /api/courses/{courseId}/materials`
  - Include authentication headers using authService.getAccessToken()
  - Add proper error handling and type safety
  - _Requirements: 1.1, 2.1_

- [ ]* 1.1 Write unit tests for API service functions
  - Test getChatHistory with valid course ID
  - Test getMaterials with valid course ID
  - Test error handling for 401, 404, 500 responses
  - Test authentication header inclusion
  - _Requirements: 1.1, 2.1_

- [x] 2. Add data transformation utilities





  - Create transformation function to convert backend chat history records to frontend Message format
  - Create transformation function to convert backend material records to frontend UploadedFile format
  - Handle timestamp conversion and ID generation
  - Handle empty arrays and null values gracefully
  - _Requirements: 1.3, 2.3_

- [ ]* 2.1 Write unit tests for data transformation
  - Test chat history transformation with various input formats
  - Test material transformation with different processing statuses
  - Test handling of empty arrays and null values
  - Test timestamp conversion accuracy
  - _Requirements: 1.3, 2.3_

- [x] 3. Update Dashboard component with loading states





  - Add state variables: `isLoadingChatHistory`, `isLoadingMaterials`, `chatHistoryError`, `materialsError`
  - Create `loadChatHistory(courseId)` function that fetches and transforms chat history
  - Create `loadMaterials(courseId)` function that fetches and transforms materials
  - Update state with loading indicators during fetch operations
  - _Requirements: 3.1, 3.2_

- [x] 4. Implement useEffect hooks for data loading




  - Add useEffect hook to load chat history when activeCourse changes
  - Add useEffect hook to load materials when activeCourse changes
  - Ensure chat history is cleared when switching courses
  - Implement AbortController for cleanup to prevent memory leaks
  - _Requirements: 1.1, 1.5, 2.1, 3.4_

- [x] 5. Add error handling and user feedback





  - Implement try-catch blocks in data fetching functions
  - Display toast notifications for different error types (network, auth, server)
  - Handle 401/403 errors by redirecting to login
  - Add retry functionality for failed requests
  - Log errors for debugging purposes
  - _Requirements: 1.4, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Update Workspace component to show loading states




  - Pass loading state props to Workspace component
  - Display loading indicators in chat area when `isLoadingChatHistory` is true
  - Display loading indicators in materials panel when `isLoadingMaterials` is true
  - Show error messages with retry buttons when errors occur
  - _Requirements: 1.2, 2.2, 3.1_

- [x] 7. Ensure backward compatibility




  - Verify existing message sending functionality still works with loaded history
  - Verify existing file upload functionality still works with loaded materials
  - Test that new messages are appended to loaded history
  - Test that newly uploaded files are added to loaded materials list
  - _Requirements: 1.1, 2.5_

- [x] 8. Final checkpoint - Ensure all functionality works
  - Test full flow: refresh page → courses load → select course → chat history and materials load
  - Test course switching: verify data clears and new data loads
  - Test error scenarios: network failure, auth failure, server error
  - Test concurrent operations: send message while loading history, upload file while loading materials
  - Verify no console errors or warnings
  - Ensure all tests pass, ask the user if questions arise
  - **Status**: ✅ COMPLETE - All 5 backward compatibility tests passing
