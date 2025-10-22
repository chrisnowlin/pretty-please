# Design: Lesson Editability

## Overview

Enable teachers to manually edit saved lesson plans through a straightforward PATCH API and markdown editor interface.

## Architecture Decisions

### 1. Update Strategy: PATCH over PUT

**Decision:** Use PATCH for partial updates, not PUT for full replacement.

**Rationale:**
- Teachers typically want to edit content OR metadata, not both
- Partial updates reduce payload size
- Safer: only specified fields are changed
- Follows REST best practices for partial updates

**Implementation:**
```python
# Allow updating any combination of these fields:
- markdown_content
- title
- duration_minutes
- teaching_style
- learning_objective
```

### 2. Pydantic Partial Update Pattern

**Decision:** Use Pydantic's `exclude_unset=True` pattern for partial updates.

**Rationale:**
- Best practice from FastAPI docs for PATCH endpoints
- Cleanly distinguishes between "not provided" and "provided as None"
- Prevents accidental null overwrites
- Works seamlessly with SQLAlchemy updates

**Implementation Pattern (from FastAPI docs):**
```python
@app.patch("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    lesson_update: UpdateLessonRequest,
    db: Session = Depends(get_db)
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get only the fields that were actually set in the request
    update_data = lesson_update.model_dump(exclude_unset=True)
    
    # Check if any fields were provided
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Apply updates to the model
    for key, value in update_data.items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    
    return LessonDetailResponse.model_validate(lesson)
```

### 3. Markdown Validation

**Decision:** Minimal validation - accept any valid string as markdown content.

**Rationale:**
- Teachers may use non-standard markdown
- Over-validation blocks legitimate edits
- Trust users to maintain content quality
- YAML frontmatter parsing is optional (best effort)

**Validation rules:**
- Content must be non-empty
- Max length: 100KB (reasonable for lesson plans)
- No schema enforcement on markdown structure

### 4. Frontend State Management with React Query

**Decision:** Use TanStack Query (React Query) `useMutation` with optimistic updates disabled.

**Rationale:**
- Already used throughout the frontend (see SearchPage, RAGConfigPanel, CollectionConfigPanel)
- Provides automatic error handling, loading states, and cache invalidation
- Optimistic updates are overkill for lesson editing (not time-critical)
- Clearer error handling with explicit waiting for server response

**Implementation Pattern (from existing codebase + Context7):**
```typescript
// In api.ts, add updateLesson method
async updateLesson(
  lessonId: number,
  updates: Partial<{
    markdown_content: string;
    title: string;
    duration_minutes: number;
    teaching_style: string;
    learning_objective: string;
  }>
): Promise<LessonDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/lessons/${lessonId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update lesson');
  }

  return response.json();
}

// In LessonDetail.tsx component
const queryClient = useQueryClient();

const updateMutation = useMutation({
  mutationFn: (updates: UpdateLessonData) => 
    apiClient.updateLesson(lessonId, updates),
  
  onSuccess: (updatedLesson) => {
    // Invalidate and refetch the lesson query
    queryClient.invalidateQueries({ queryKey: ['lessons', lessonId] });
    queryClient.invalidateQueries({ queryKey: ['lessons'] }); // Refresh list
    
    setIsEditing(false);
    // Optional: Show success toast
  },
  
  onError: (error: Error) => {
    setError(error.message);
    // Stay in edit mode, preserve user's edits
  },
});

// Usage in save handler
const handleSave = () => {
  const updates: any = {};
  if (editedContent !== lesson.markdown_content) {
    updates.markdown_content = editedContent;
  }
  if (editedTitle !== lesson.title) {
    updates.title = editedTitle;
  }
  // ... other fields
  
  updateMutation.mutate(updates);
};
```

### 5. Frontend Editing Interface

**Decision:** Simple controlled textarea with monospace font, not a rich markdown editor.

**Rationale:**
- Teachers are comfortable with plain text
- Avoids dependency on heavy markdown editor libraries
- Simpler UX with fewer edge cases
- Can upgrade to richer editor later if needed
- Follows React controlled component pattern (from React docs)

**UI Flow:**
1. View lesson → Click "Edit" button
2. Show textarea with markdown content
3. Show editable fields for key metadata
4. "Save" commits changes via PATCH
5. "Cancel" reverts to view mode

**Controlled Component Pattern (from React docs):**
```typescript
const [editedContent, setEditedContent] = useState('');
const [editedTitle, setEditedTitle] = useState('');

// In edit mode, bind inputs to state
<textarea
  value={editedContent}
  onChange={(e) => setEditedContent(e.target.value)}
  className="font-mono w-full min-h-[400px] p-4"
/>

<input
  value={editedTitle}
  onChange={(e) => setEditedTitle(e.target.value)}
  maxLength={500}
/>
```

### 6. Dirty State Tracking

**Decision:** Track whether edits have been made to show confirmation dialog.

**Rationale:**
- Prevents accidental data loss
- Standard UX pattern for editors
- Simple to implement with comparison

**Implementation:**
```typescript
const [initialState, setInitialState] = useState({
  content: lesson.markdown_content,
  title: lesson.title,
  // ... other fields
});

const isDirty = useMemo(() => {
  return (
    editedContent !== initialState.content ||
    editedTitle !== initialState.title
    // ... other comparisons
  );
}, [editedContent, editedTitle, initialState]);

const handleCancel = () => {
  if (isDirty) {
    if (window.confirm('Discard unsaved changes?')) {
      setIsEditing(false);
    }
  } else {
    setIsEditing(false);
  }
};
```

### 7. Metadata Editability

**Decision:** Allow editing title, duration, teaching_style, learning_objective only.

**Rationale:**
- These fields are most likely to need adjustment
- Grade/subject should remain stable (search/filter keys)
- Sources/images tied to original generation (shouldn't change)

**Non-editable fields:**
- `grade` - core identifier
- `subject` - core identifier  
- `topic` - historical record of generation
- `sources_count`, `images_count` - derived from generation
- `created_at` - immutable timestamp
- `lesson_id` - primary key

### 8. Timestamp Updates

**Decision:** SQLAlchemy's `onupdate` automatically sets `updated_at`.

**Rationale:**
- Already configured in database model
- Happens automatically on any UPDATE
- No manual timestamp management needed
- Consistent across all updates

## API Design

### Update Lesson Endpoint

```
PATCH /api/lessons/{lesson_id}
```

**Request Body (Pydantic Model):**
```python
class UpdateLessonRequest(BaseModel):
    markdown_content: Optional[str] = Field(None, min_length=1, max_length=100000)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    duration_minutes: Optional[int] = Field(None, ge=20, le=90)
    teaching_style: Optional[str] = None
    learning_objective: Optional[str] = Field(None, min_length=1, max_length=500)

    @field_validator("teaching_style")
    @classmethod
    def validate_teaching_style(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            from ..models.educational import VALID_TEACHING_STYLES
            if v not in VALID_TEACHING_STYLES:
                raise ValueError(
                    f"Invalid teaching style '{v}'. Must be one of: {', '.join(VALID_TEACHING_STYLES)}"
                )
        return v
```

**Response:** Full `LessonDetailResponse` with updated fields

**Status Codes:**
- 200: Success
- 400: Validation error or no fields provided
- 404: Lesson not found
- 422: Invalid field values (Pydantic validation)

**Error Response Format (FastAPI default):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

## Frontend Design

### Component Structure

```
LessonPlansPage
├── LessonList (existing, needs link to detail)
└── LessonDetail (new)
    ├── LessonViewMode
    │   ├── LessonMetadata (display)
    │   ├── MarkdownContent (read-only)
    │   └── EditButton
    └── LessonEditMode
        ├── MetadataInputs (controlled)
        ├── MarkdownTextarea (controlled)
        └── SaveCancelButtons
```

### State Management

**Edit Mode State:**
```typescript
const [isEditing, setIsEditing] = useState(false);
const [editedContent, setEditedContent] = useState('');
const [editedMetadata, setEditedMetadata] = useState({
  title: '',
  duration_minutes: 50,
  teaching_style: 'balanced',
  learning_objective: '',
});
const [error, setError] = useState<string | null>(null);
```

**React Query Integration:**
```typescript
// Fetch lesson data
const { data: lesson, isLoading } = useQuery({
  queryKey: ['lessons', lessonId],
  queryFn: () => apiClient.getLesson(lessonId),
});

// Update mutation
const updateMutation = useMutation({
  mutationFn: (updates) => apiClient.updateLesson(lessonId, updates),
  onSuccess: (updatedLesson) => {
    queryClient.invalidateQueries({ queryKey: ['lessons', lessonId] });
    setIsEditing(false);
  },
  onError: (error) => setError(error.message),
});
```

### UI Components

**View Mode:**
- "Edit" button (top right)
- Read-only markdown display using `react-markdown` (already in package.json)
- Metadata display (grid layout)

**Edit Mode:**
- Textarea for markdown content (monospace, resizable)
- Input fields for editable metadata
- "Save" button (primary, disabled while saving)
  - Shows "Saving..." text when `updateMutation.isPending`
- "Cancel" button (secondary)
- Loading spinner during save
- Error message display if mutation fails

**Loading State (from React Query):**
```typescript
{updateMutation.isPending && (
  <div className="flex items-center gap-2">
    <Spinner />
    <span>Saving...</span>
  </div>
)}

<button
  onClick={handleSave}
  disabled={updateMutation.isPending || !isDirty}
  className="..."
>
  {updateMutation.isPending ? 'Saving...' : 'Save'}
</button>
```

## Database Impact

**No schema changes required.** Existing `Lesson` model already supports:
- All editable fields as columns
- `updated_at` with `onupdate=datetime.utcnow`
- Proper indexing for queries

## Error Handling

### Backend (FastAPI Standard)

**Validation Errors (422):**
- FastAPI automatically returns detailed validation errors from Pydantic
- Include field location, error type, message, and input value

**Custom Errors:**
```python
# 404: Lesson not found
if not lesson:
    raise HTTPException(status_code=404, detail="Lesson not found")

# 400: No fields to update
if not update_data:
    raise HTTPException(status_code=400, detail="No fields to update")
```

### Frontend (React Query)

**Error Display:**
```typescript
{updateMutation.isError && (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
    <p className="font-bold">Error updating lesson</p>
    <p>{updateMutation.error.message}</p>
  </div>
)}
```

**Field-Specific Errors (Advanced):**
- Parse Pydantic validation errors from 422 response
- Map `loc` field to input components
- Highlight invalid fields in red

## Performance Considerations

- Update operations are simple UPDATE queries (fast)
- No expensive reprocessing or regeneration
- Markdown parsing only on read (display), not write
- Typical lesson size ~10KB, well within request limits
- React Query handles caching and prevents redundant requests

## Security Considerations

- Single-user app: no authorization needed (yet)
- Input validation prevents injection attacks
- Max content length prevents resource exhaustion
- SQLAlchemy ORM prevents SQL injection
- Pydantic validation prevents type confusion

## Testing Strategy

**Backend:**
- Unit tests for `UpdateLessonRequest` validation
- Integration tests for PATCH endpoint
- Test `exclude_unset` behavior
- Test `updated_at` is set correctly

**Frontend:**
- Component tests for edit mode toggle
- Test save/cancel behavior
- Test dirty state tracking
- Test React Query integration

## Dependencies

**Backend:**
- FastAPI (existing)
- Pydantic (existing)
- SQLAlchemy (existing)

**Frontend:**
- React 18 (existing)
- TanStack Query v5 (existing - `@tanstack/react-query`)
- Tailwind CSS (existing)

## Migration Path

**Phase 1:** Backend API
1. Add `UpdateLessonRequest` model
2. Implement PATCH endpoint
3. Add validation
4. Test with curl/Postman

**Phase 2:** Frontend Basic
1. Add `updateLesson` to APIClient
2. Create `LessonDetail` component with view mode
3. Add edit mode with basic textarea
4. Integrate React Query mutation

**Phase 3:** Frontend Polish
1. Add dirty state tracking
2. Add confirmation dialog
3. Improve error display
4. Add character counts
5. Style improvements

**Phase 4:** Testing & Docs
1. Write backend tests
2. Write frontend tests
3. Update API documentation
4. Update user guide

## Future Extensions (Out of Scope)

- Version history / revision tracking
- Auto-save drafts
- Rich markdown preview (side-by-side)
- Markdown toolbar (bold, italic, etc.)
- Undo/redo within editor
- Real-time collaborative editing
- Conflict resolution for concurrent edits
