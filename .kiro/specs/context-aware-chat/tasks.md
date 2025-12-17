# Implementation Plan

- [x] 1. Create context service module




  - Create `python-backend/services/context_service.py` with ContextService class
  - Implement data models (UserPreferences, AcademicInfo, UserContext) in `models/schemas.py`
  - Add default preferences constant
  - _Requirements: 2.1, 3.1, 8.1_

- [x] 2. Implement preference retrieval



  - Implement `get_preferences()` method to query personalized table
  - Handle case when preferences don't exist (return None)
  - Add error handling and logging
  - _Requirements: 2.1, 2.2, 2.3, 8.1_

- [x] 3. Implement academic info retrieval




  - Implement `get_academic_info()` method to query academic table
  - Handle case when academic info doesn't exist (return None)
  - Add error handling and logging
  - _Requirements: 3.1, 3.2, 3.3, 8.2_

- [x] 4. Implement chat history retrieval




  - Implement `get_chat_history()` method to query chat_history table
  - Order by created_at ascending (chronological)
  - Limit to 10 most recent messages
  - Flatten JSONB arrays into Message list
  - Handle empty history case
  - Add error handling and logging
  - _Requirements: 1.1, 1.2, 1.4, 6.2, 8.3_

- [x] 5. Implement parallel context retrieval





  - Implement `get_user_context()` method
  - Use asyncio.gather() to fetch preferences, academic, and history in parallel
  - Combine results into UserContext object
  - Set boolean flags (has_preferences, has_academic, has_history)
  - Add performance logging
  - _Requirements: 6.1, 6.4, 7.1, 7.2_

- [x] 6. Implement context prompt formatting




  - Implement `format_context_prompt()` method
  - Create user profile section with preferences
  - Create academic profile section
  - Create previous conversation section with history
  - Include material context if provided
  - Add current question at the end
  - Omit sections when context is missing
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Integrate context service into chat endpoint





  - Import ContextService in `routers/chat.py`
  - Instantiate context service
  - Modify `save_chat_message()` to call `get_user_context()`
  - Pass user_id, course_id, and access_token
  - Handle context retrieval errors gracefully
  - _Requirements: 1.1, 2.1, 3.1, 7.1_

- [x] 8. Enhance AI prompt with user context





  - After retrieving context, call `format_context_prompt()`
  - Pass UserContext, user message, and material context (from existing RAG)
  - Replace simple message with enhanced prompt
  - Pass enhanced prompt to `local_ai_service.generate_response()`
  - _Requirements: 4.2, 4.4, 5.1, 5.3_

- [x] 9. Add comprehensive logging





  - Log context retrieval start with user_id and course_id
  - Log successful retrieval with counts (preferences, academic, history length, materials)
  - Log warnings for missing context components
  - Log errors with full stack traces
  - Log total context size in characters
  - Log performance metrics (retrieval time)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Handle missing data gracefully




  - When preferences missing, use DEFAULT_PREFERENCES
  - When academic info missing, omit academic section from prompt
  - When history empty, omit history section from prompt
  - When materials not found, omit materials section
  - Ensure chat works even if all context is missing
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Add error handling and timeouts





  - Wrap context retrieval in try-except blocks
  - Set 2-second timeout for context retrieval
  - On timeout, use partial context retrieved
  - On complete failure, proceed with just user message
  - Log all errors appropriately
  - _Requirements: 1.5, 2.5, 3.5, 4.5, 6.4_

- [ ]* 12. Test context service methods
  - Test `get_preferences()` with existing and missing preferences
  - Test `get_academic_info()` with existing and missing academic info
  - Test `get_chat_history()` with various history lengths (0, 5, 15 messages)
  - Test `get_user_context()` with complete and partial profiles
  - Test `format_context_prompt()` with all combinations of context
  - Verify default preferences are applied correctly
  - Verify history ordering is chronological
  - Verify history limit is respected (max 10 messages)
  - _Requirements: 1.2, 2.3, 3.3, 8.1, 8.2, 8.3_

- [ ]* 13. Test end-to-end chat with context
  - Create test user with complete profile (preferences + academic)
  - Create test course with materials
  - Send multiple messages to build history
  - Verify AI responses reflect user preferences
  - Verify AI responses reference academic level
  - Verify AI responses reference previous conversation
  - Verify AI responses reference course materials
  - _Requirements: 1.3, 2.4, 3.4, 4.2, 5.3_

- [ ]* 14. Test graceful degradation
  - Test chat with user missing preferences (should use defaults)
  - Test chat with user missing academic info (should work without)
  - Test chat with no history (should work as first message)
  - Test chat with no materials (should work without RAG)
  - Test chat with all context missing (should still respond)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Final checkpoint - Verify complete implementation





  - Ensure all tests pass
  - Verify context retrieval is performant (< 2 seconds)
  - Verify logging is comprehensive
  - Verify error handling works correctly
  - Test with real user profiles and conversations
  - Document any known limitations
  - _Requirements: All_
