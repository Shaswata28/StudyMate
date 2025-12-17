# Material Delete Investigation

## Problem

Materials are not being deleted from the database when clicking the delete button in the materials modal. They disappear from the frontend but reappear after page refresh.

## Investigation Done

### 1. Backend Verification ✅

The DELETE endpoint is **properly implemented** in `python-backend/routers/materials.py`:

- Endpoint: `DELETE /api/materials/{material_id}`
- Verifies user ownership
- Deletes file from Supabase storage
- Deletes record from database
- Returns success message

**Status**: Backend implementation is correct.

### 2. Frontend Verification ✅

The delete function in `client/pages/Dashboard.tsx`:

- Optimistically removes from UI
- Checks if material is pending or saved
- Calls backend DELETE endpoint for saved materials
- Restores on error

**Status**: Frontend implementation looks correct.

### 3. Enhanced Logging ✅

Added detailed console logging to help debug:

**In `handleRemoveFile`**:
```typescript
console.log('Delete material:', { fileId, fileName, isPendingFile });
console.log('Calling DELETE endpoint:', url);
console.log('DELETE response:', { status, statusText, ok });
console.log('DELETE success:', result);
```

**In `loadMaterials`**:
```typescript
console.log('Material IDs:', transformedMaterials.map(m => ({ id: m.id, name: m.name })));
```

## What to Check Next

### Step 1: Verify Backend is Running

Make sure the Python backend is running on port 8000:

```bash
cd python-backend
python -m uvicorn main:app --reload --port 8000
```

### Step 2: Open Browser Console

1. Open your application in the browser
2. Open DevTools (F12)
3. Go to the Console tab
4. Select a course with materials

### Step 3: Check Material IDs

Look for the log message:
```
Material IDs: [{ id: "...", name: "..." }, ...]
```

**Check if the IDs are**:
- ✅ UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- ❌ Temporary IDs (e.g., `1733654321000-abc123-0`)

If they're temporary IDs, the materials weren't actually saved to the database.

### Step 4: Try to Delete a Material

1. Click the trash icon on a material
2. Watch the console for these logs:

```
Delete material: { fileId: "...", fileName: "...", isPendingFile: false }
Calling DELETE endpoint: /api/materials/...
DELETE response: { status: 200, statusText: "OK", ok: true }
DELETE success: { message: "Material deleted successfully" }
```

### Step 5: Check Network Tab

1. Go to Network tab in DevTools
2. Click delete on a material
3. Look for the DELETE request
4. Check:
   - **Request URL**: Should be `/api/materials/{uuid}`
   - **Status**: Should be 200
   - **Response**: Should have success message

### Step 6: Check Backend Logs

In the terminal running the Python backend, look for:

```
INFO - DELETE /api/materials/{material_id}
INFO - Material deleted: {material_id}
```

## Possible Issues

### Issue A: Materials Have Temporary IDs

**Symptom**: Material IDs look like `1733654321000-abc123-0`

**Cause**: Materials were never saved to the database. They're still "pending" files.

**Solution**: 
1. Upload a file
2. Send a message with that file attached
3. Wait for the message to complete
4. Check if the material ID changes to a UUID
5. Then try to delete

### Issue B: Backend Not Running

**Symptom**: Network error, connection refused

**Solution**: Start the Python backend on port 8000

### Issue C: Authentication Issue

**Symptom**: 401 Unauthorized response

**Solution**: 
- Log out and log back in
- Check if token is being sent in Authorization header

### Issue D: Material Doesn't Exist

**Symptom**: 404 Not Found response

**Cause**: Material was already deleted or doesn't exist

**Solution**: Refresh the page to sync with database state

## Expected Behavior

### Correct Flow:

1. **Upload file** → Gets temporary ID (e.g., `1733654321000-abc123-0`)
2. **Send message** → File sent to brain.py, then saved to database
3. **Material saved** → ID changes to UUID (e.g., `550e8400-...`)
4. **Click delete** → Calls backend, deletes from database
5. **Refresh page** → Material doesn't reappear

### Current Issue:

If materials reappear after refresh, it means:
- Either the DELETE request never reached the backend
- Or the DELETE request failed
- Or the materials have temporary IDs (not saved to DB)

## Action Items

Please run the application and:

1. ✅ Check browser console for material IDs
2. ✅ Try to delete a material
3. ✅ Check console logs during delete
4. ✅ Check Network tab for DELETE request
5. ✅ Check backend terminal for logs
6. ✅ Report back with:
   - Material IDs format (UUID or temporary?)
   - Console logs during delete
   - Network request status
   - Backend logs

This will help us identify exactly where the delete is failing.
