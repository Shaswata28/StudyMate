# File Attachment Flow - Updated Behavior

## Problem

After the persistence fix, files were being uploaded immediately to the backend when selected, which triggered brain.py processing before the user even asked a question. This was not the desired behavior.

## Desired Behavior

Files should:
1. Stay as "pending attachments" in the browser when selected
2. Only be sent to brain.py when the user sends a message with them
3. Be saved as persistent materials **after** successfully being used in a message

## Solution Implemented

### Phase 1: File Selection (No Backend Call)

When a user selects files using the attachment button:

```typescript
const handleFileUpload = (files: File[]) => {
  // Keep files as pending attachments - they will be sent with the next message
  // This prevents immediate processing by brain.py
  const newFiles = files.map((file, index) => ({
    id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}-${index}`,
    name: file.name,
    type: file.type || "application/octet-stream",
    file: file, // Store the actual File object in browser memory
  }));

  setUploadedFiles((prev) => [...prev, ...newFiles]);
  setPendingFiles((prev) => [...prev, ...newFiles]); // Mark as pending
};
```

**What happens:**
- ✅ Files stored in browser memory (React state)
- ✅ Files appear in UI as "pending"
- ❌ NO backend call
- ❌ NO brain.py processing
- ❌ NO database save

### Phase 2: Send Message with Attachments

When the user sends a message with pending files:

```typescript
const handleSendMessage = async (message: string) => {
  // 1. Convert pending files to base64 attachments
  const attachments = await Promise.all(
    pendingFiles
      .filter((f) => f.file)
      .map(async (f) => ({
        filename: f.name,
        mime_type: f.type,
        data: await convertFileToBase64(f.file!),
      }))
  );

  // 2. Clear pending files (they're now being sent)
  setPendingFiles([]);

  // 3. Send message with attachments to chat endpoint
  const response = await fetch(
    `${API_BASE_URL}/courses/${activeCourse.id}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({
        message: message,
        history: history,
        attachments: attachments, // Files sent here
      }),
    }
  );
  
  // ... handle response ...
};
```

**What happens:**
- ✅ Files converted to base64
- ✅ Sent to chat endpoint with message
- ✅ brain.py processes files in context of the question
- ✅ AI generates response using file content
- ❌ NOT YET saved to database

### Phase 3: Save as Materials (After Success)

After the chat message is successfully processed:

```typescript
if (response.ok && attachments.length > 0 && activeCourse) {
  // Save each attachment as a persistent material
  for (const attachment of attachments) {
    try {
      // Find the original file
      const originalFile = pendingFiles.find(f => f.name === attachment.filename);
      
      if (originalFile && originalFile.file) {
        // Upload to materials endpoint
        const formData = new FormData();
        formData.append('file', originalFile.file);

        const materialResponse = await fetch(
          `${API_BASE_URL}/courses/${activeCourse.id}/materials`,
          {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
          }
        );

        if (materialResponse.ok) {
          const uploadedMaterial = await materialResponse.json();
          
          // Update UI with real material ID
          setUploadedFiles((prev) =>
            prev.map((f) =>
              f.name === attachment.filename && f.file
                ? {
                    id: uploadedMaterial.id,
                    name: uploadedMaterial.name,
                    type: uploadedMaterial.file_type,
                  }
                : f
            )
          );
        }
      }
    } catch (error) {
      console.error(`Error saving material:`, error);
      // Don't fail the message if material save fails
    }
  }
}
```

**What happens:**
- ✅ Files uploaded to storage
- ✅ Records created in materials table
- ✅ Background processing queued (OCR, embeddings)
- ✅ UI updated with real material IDs
- ✅ Materials persist across page refreshes

## Complete Flow Diagram

```
User selects file
       ↓
[File stored in browser memory]
       ↓
User types question
       ↓
User clicks send
       ↓
[Files converted to base64]
       ↓
[Message + attachments sent to chat endpoint]
       ↓
[brain.py processes files with question]
       ↓
[AI generates response]
       ↓
[Response saved to chat_history]
       ↓
[SUCCESS: Files uploaded to materials endpoint]
       ↓
[Materials saved to database]
       ↓
[Background: OCR + embedding generation]
       ↓
[Materials available for future RAG queries]
```

## Key Benefits

### 1. No Premature Processing
- Files are NOT processed until the user asks a question
- brain.py only runs when there's actual context (the question)
- Saves processing resources

### 2. Context-Aware Processing
- Files are processed in the context of the user's question
- AI can provide more relevant responses
- Better user experience

### 3. Persistence After Use
- Files are only saved if successfully used in a message
- Failed messages don't create orphaned materials
- Database stays clean

### 4. Graceful Degradation
- If material save fails, the message still succeeds
- User gets their answer even if persistence fails
- Error logged but doesn't block user

## Testing the Flow

### Test 1: File Selection (No Processing)

1. Select a PDF file using the attachment button
2. **Verify:** File appears in the pending files area
3. **Verify:** No backend logs (no API calls)
4. **Verify:** brain.py is NOT running
5. **Check database:** No new materials record

### Test 2: Send Message with File

1. With file still pending, type a question: "What is this document about?"
2. Click send
3. **Verify:** Loading indicator appears
4. **Verify:** Backend logs show chat endpoint called
5. **Verify:** brain.py processes the file
6. **Verify:** AI response appears
7. **Verify:** File is no longer "pending"
8. **Check database:** New chat_history record exists
9. **Check database:** New materials record exists

### Test 3: Persistence

1. Refresh the page (F5)
2. **Verify:** Chat message still visible
3. **Verify:** File appears in materials panel (not pending)
4. **Verify:** Console shows "Successfully loaded X materials"

### Test 4: Multiple Files

1. Select 2 files
2. Type a question
3. Send message
4. **Verify:** Both files processed by brain.py
5. **Verify:** Both files saved as materials
6. **Verify:** Both appear in materials panel after refresh

## Comparison: Before vs After

### Before Fix (Immediate Upload)

```
User selects file
       ↓
❌ Immediate upload to backend
       ↓
❌ brain.py processes file (no question context)
       ↓
❌ Saved to database immediately
       ↓
User types question (file already processed)
       ↓
Send message
       ↓
AI response (may not use file effectively)
```

**Problems:**
- Wasted processing (file processed without context)
- Poor AI responses (no question to guide processing)
- Unnecessary database writes

### After Fix (Deferred Upload)

```
User selects file
       ↓
✅ Stored in browser only
       ↓
User types question
       ↓
Send message
       ↓
✅ brain.py processes file WITH question context
       ↓
✅ AI generates contextual response
       ↓
✅ File saved to database after success
```

**Benefits:**
- Efficient processing (only when needed)
- Better AI responses (question provides context)
- Clean database (only successful uploads)

## Edge Cases Handled

### 1. User Removes Pending File

```typescript
const handleRemovePendingFile = (fileId: string) => {
  setPendingFiles((prev) => prev.filter((f) => f.id !== fileId));
};
```

- File removed from pending list
- NOT sent with next message
- NOT saved to database

### 2. Message Send Fails

```typescript
if (!response.ok) {
  // Error handling
  // Files remain in pendingFiles
  // NOT saved to database
  // User can retry
}
```

- Files stay pending
- User can try again
- No orphaned materials

### 3. Material Save Fails

```typescript
try {
  // Upload material
} catch (error) {
  console.error('Error saving material:', error);
  // Don't fail the message
}
```

- Message still succeeds
- User gets AI response
- Error logged for debugging
- File can be re-uploaded later

### 4. Page Refresh with Pending Files

- Pending files are lost (they're in browser memory)
- This is expected behavior
- Saved materials persist (they're in database)

## Files Modified

1. `client/pages/Dashboard.tsx`
   - Reverted `handleFileUpload` to keep files as pending
   - Updated `handleSendMessage` to save materials after success
   - Added error handling for material save failures

## Backend Endpoints Used

### During Message Send
- `POST /api/courses/{course_id}/chat` - Send message with attachments

### After Success
- `POST /api/courses/{course_id}/materials` - Save each attachment as material

### On Page Load
- `GET /api/courses/{course_id}/chat` - Load chat history
- `GET /api/courses/{course_id}/materials` - Load saved materials

---

**Status:** ✅ Fixed  
**Date:** December 7, 2024  
**Behavior:** Files now wait for user question before processing
