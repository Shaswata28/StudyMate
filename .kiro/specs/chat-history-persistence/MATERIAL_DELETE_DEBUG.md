# Material Delete Functionality - Debug Guide

## Issue Report

**Problem**: When clicking delete button in materials modal, the material disappears from the frontend but reappears after page refresh. This indicates the material is not being deleted from the database.

## Implementation Status

### Backend (Python FastAPI)

The DELETE endpoint is **properly implemented** in `python-backend/routers/materials.py`:

```python
@router.delete("/materials/{material_id}", response_model=MessageResponse)
async def delete_material(
    material_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """Delete a material and its file from storage."""
    # 1. Verifies user owns the material
    # 2. Deletes file from Supabase storage
    # 3. Deletes record from database
```

**Endpoint**: `DELETE /api/materials/{material_id}`

### Frontend (React)

The delete function is implemented in `client/pages/Dashboard.tsx`:

```typescript
const handleRemoveFile = async (fileId: string) => {
  // 1. Optimistically removes from UI
  // 2. Checks if it's a pending file or saved material
  // 3. Calls DELETE endpoint for saved materials
  // 4. Restores on error
}
```

**Endpoint Called**: `${API_BASE_URL}/materials/${fileId}`  
**API_BASE_URL**: `/api` (proxied to `http://localhost:8000`)

## Debugging Steps

### 1. Check Browser Console

Added detailed logging to the delete function. When you click delete, check the browser console for:

```
Delete material: { fileId: "...", fileName: "...", isPendingFile: false }
Calling DELETE endpoint: /api/materials/...
DELETE response: { status: 200, statusText: "OK", ok: true }
DELETE success: { message: "Material deleted successfully" }
```

### 2. Check Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click delete on a material
4. Look for the DELETE request to `/api/materials/{id}`
5. Check:
   - Request URL
   - Request Headers (Authorization header present?)
   - Response Status (200 = success, 401 = auth error, 404 = not found)
   - Response Body

### 3. Check Backend Logs

The Python backend logs all requests. Check the terminal running the backend for:

```
INFO - DELETE /api/materials/{material_id}
INFO - Material deleted: {material_id}
```

Or error messages if something failed.

### 4. Verify Material ID Format

**Pending Files** (not saved to DB):
- Format: `{timestamp}-{random}-{index}`
- Example: `1733654321000-abc123-0`
- These should NOT call the backend

**Saved Materials** (from database):
- Format: UUID
- Example: `550e8400-e29b-41d4-a716-446655440000`
- These SHOULD call the backend

### 5. Test Backend Directly

Use the test script to verify the backend endpoint works:

```bash
cd python-backend
python test_delete_material.py
```

You'll need:
1. Your access token (from browser localStorage or login response)
2. A material ID from your database

## Common Issues

### Issue 1: Authentication Token Missing/Invalid

**Symptoms**: 401 Unauthorized response

**Solution**: 
- Check if user is logged in
- Verify token is being sent in Authorization header
- Check token hasn't expired

### Issue 2: Material ID is Pending File ID

**Symptoms**: Material disappears but no backend call made

**Solution**:
- Check console logs for `isPendingFile: true`
- This is expected behavior for files not yet saved
- Files are only saved after sending a message

### Issue 3: CORS Error

**Symptoms**: Network error, CORS policy error in console

**Solution**:
- Verify Python backend is running on port 8000
- Check Vite proxy configuration in `vite.config.ts`
- Verify CORS settings in `python-backend/main.py`

### Issue 4: Material Not Found

**Symptoms**: 404 Not Found response

**Solution**:
- Material may have been deleted already
- Material ID may be incorrect
- User may not own the material

### Issue 5: Storage Delete Fails

**Symptoms**: 500 Internal Server Error

**Solution**:
- Check backend logs for detailed error
- Verify Supabase storage bucket exists
- Check file path is correct
- Verify Supabase credentials

## Expected Flow

### Successful Delete:

1. User clicks trash icon in materials modal
2. Frontend immediately removes material from UI (optimistic update)
3. Frontend checks if material is pending or saved
4. If saved: Frontend calls `DELETE /api/materials/{id}`
5. Backend verifies user owns material
6. Backend deletes file from Supabase storage
7. Backend deletes record from database
8. Backend returns success message
9. Frontend shows success toast
10. Material stays removed from UI

### Failed Delete:

1. User clicks trash icon
2. Frontend removes material from UI
3. Backend call fails (network, auth, etc.)
4. Frontend catches error
5. Frontend restores material to UI
6. Frontend shows error toast

## Testing Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 8080
- [ ] User is logged in
- [ ] Material exists in database
- [ ] Material belongs to logged-in user
- [ ] Browser console shows DELETE request
- [ ] Network tab shows 200 response
- [ ] Backend logs show successful delete
- [ ] Material doesn't reappear after refresh

## Next Steps

1. **Run the application** with both frontend and backend
2. **Open browser DevTools** and go to Console tab
3. **Click delete** on a material
4. **Check console logs** for the detailed output
5. **Check Network tab** for the DELETE request
6. **Report findings** with:
   - Console logs
   - Network request details
   - Backend logs
   - Material ID that was attempted to delete

This will help identify exactly where the delete is failing.
