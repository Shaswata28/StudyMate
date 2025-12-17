# Subject List Configuration Guide

This guide shows you where the subject list is defined and how to update it across the application.

## 📍 Current Subject List

The subjects are now centralized in constants files:

```
- computer science (CS)
- electrical and electronics engineering (EEE)
- english (English)
- business administration (BA)
- economics (Economics)
```

---

## 🔧 Where to Make Changes

### 1. Backend Constants (Python)

**File**: `python-backend/constants.py`

```python
# Valid subjects (must match frontend options)
VALID_SUBJECTS = [
    'computer science',
    'electrical and electronics engineering',
    'english',
    'business administration',
    'economics'
]

# Subject display names (for frontend)
SUBJECT_DISPLAY_NAMES = {
    'computer science': 'CS',
    'electrical and electronics engineering': 'EEE',
    'english': 'English',
    'business administration': 'BA',
    'economics': 'Economics'
}
```

**To add a new subject**:
1. Add the value to `VALID_SUBJECTS` list
2. Add the display name to `SUBJECT_DISPLAY_NAMES` dict

---

### 2. Frontend Constants (TypeScript)

**File**: `client/lib/constants.ts`

```typescript
export const SUBJECTS = [
  { value: 'computer science', label: 'CS' },
  { value: 'electrical and electronics engineering', label: 'EEE' },
  { value: 'english', label: 'English' },
  { value: 'business administration', label: 'BA' },
  { value: 'economics', label: 'Economics' },
] as const;
```

**To add a new subject**:
1. Add a new object with `value` and `label` properties

---

### 3. Frontend Signup Form

**File**: `client/pages/Signup.tsx` (lines ~569-573)

```tsx
<select id="subject" value={subject} onChange={...}>
  <option value="" disabled>Subject</option>
  <option value="computer science">CS</option>
  <option value="electrical and electronics engineering">EEE</option>
  <option value="english">English</option>
  <option value="business administration">BA</option>
  <option value="economics">Economics</option>
</select>
```

**To add a new subject**:
1. Add a new `<option>` element

**Better approach**: Use the constants file:

```tsx
import { SUBJECTS } from '@/lib/constants';

<select id="subject" value={subject} onChange={...}>
  <option value="" disabled>Subject</option>
  {SUBJECTS.map(subject => (
    <option key={subject.value} value={subject.value}>
      {subject.label}
    </option>
  ))}
</select>
```

---

### 4. Database Migration (SQL)

**File**: `python-backend/migrations/002_create_tables.sql`

The database doesn't enforce specific subjects (it uses TEXT[] array), so no changes needed here. The validation happens at the application level.

---

## ✅ Recommended Workflow

### To Add a New Subject:

1. **Update Backend Constants** (`python-backend/constants.py`):
   ```python
   VALID_SUBJECTS = [
       'computer science',
       'electrical and electronics engineering',
       'english',
       'business administration',
       'economics',
       'mathematics',  # NEW
   ]
   
   SUBJECT_DISPLAY_NAMES = {
       # ... existing ...
       'mathematics': 'Math',  # NEW
   }
   ```

2. **Update Frontend Constants** (`client/lib/constants.ts`):
   ```typescript
   export const SUBJECTS = [
     // ... existing ...
     { value: 'mathematics', label: 'Math' },  // NEW
   ] as const;
   ```

3. **Update Signup Form** (`client/pages/Signup.tsx`):
   ```tsx
   <option value="mathematics">Math</option>  // NEW
   ```
   
   Or better, use the constants:
   ```tsx
   {SUBJECTS.map(subject => (
     <option key={subject.value} value={subject.value}>
       {subject.label}
     </option>
   ))}
   ```

4. **Test**:
   - Try signing up with the new subject
   - Verify it saves to the database
   - Verify validation works

---

## 🎯 Current Implementation Status

### ✅ What's Done:
- ✅ Backend constants file created
- ✅ Frontend constants file created
- ✅ Backend validation added (Pydantic schemas)
- ✅ Subject list matches between frontend and backend

### 📝 What You Can Improve:
- Update `Signup.tsx` to use the constants file instead of hardcoded options
- This makes it easier to maintain (only update constants file)

---

## 🔄 Example: Updating Signup.tsx to Use Constants

**Current code** (hardcoded):
```tsx
<option value="computer science">CS</option>
<option value="electrical and electronics engineering">EEE</option>
<option value="english">English</option>
<option value="business administration">BA</option>
<option value="economics">Economics</option>
```

**Better code** (using constants):
```tsx
import { SUBJECTS } from '@/lib/constants';

// In the JSX:
{SUBJECTS.map(subject => (
  <option key={subject.value} value={subject.value}>
    {subject.label}
  </option>
))}
```

**Benefits**:
- Single source of truth
- Easier to maintain
- Type-safe
- Automatically synced with constants

---

## 📚 Files Reference

| File | Purpose | What to Update |
|------|---------|----------------|
| `python-backend/constants.py` | Backend constants | Add to `VALID_SUBJECTS` and `SUBJECT_DISPLAY_NAMES` |
| `client/lib/constants.ts` | Frontend constants | Add to `SUBJECTS` array |
| `client/pages/Signup.tsx` | Signup form | Add `<option>` or use constants |
| `python-backend/models/schemas.py` | Validation | No change needed (uses constants) |

---

## 🎨 Subject Value Format

**Important**: Use lowercase with spaces for values:
- ✅ `'computer science'`
- ❌ `'Computer Science'`
- ❌ `'computer_science'`
- ❌ `'ComputerScience'`

This ensures consistency between frontend and backend.

---

## 🧪 Testing Changes

After updating subjects:

1. **Backend validation**:
   ```bash
   # Test with valid subject
   curl -X POST http://localhost:8000/api/academic \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"grade":["Bachelor"],"semester_type":"double","semester":1,"subject":["mathematics"]}'
   ```

2. **Frontend**:
   - Go to `/signup`
   - Check if new subject appears in dropdown
   - Try completing signup with new subject
   - Verify it saves correctly

---

## 💡 Pro Tips

1. **Keep values lowercase**: Easier to compare and validate
2. **Use descriptive labels**: Short but clear (CS, EEE, etc.)
3. **Update both files**: Backend and frontend must match
4. **Test thoroughly**: Ensure validation works both ways
5. **Consider using constants in Signup.tsx**: Reduces duplication

---

**Need to add a subject?** Update these 2 files:
1. `python-backend/constants.py`
2. `client/lib/constants.ts`
3. (Optional) `client/pages/Signup.tsx` if not using constants

That's it! 🎉
