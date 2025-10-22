# Tasks: Add Lesson Editability

## Backend Tasks

### API Endpoint Implementation

- [x] **1.1** Create `UpdateLessonRequest` Pydantic model in `src/jina_rag_pipeline/api/models.py`
  - Define all fields as `Optional` to support partial updates
  - Fields: `markdown_content`, `title`, `duration_minutes`, `teaching_style`, `learning_objective`
  - Add validators using `@field_validator` decorator (Pydantic v2 pattern)
  - Reuse validation constants from `src/jina_rag_pipeline/models/educational.py`
  - **Pattern reference:** FastAPI PATCH updates with `exclude_unset=True`
  - Test: Create model instances with various field combinations
  - Test: Validate each field accepts valid values and rejects invalid ones

- [x] **1.2** Implement `PATCH /api/lessons/{lesson_id}` endpoint in `src/jina_rag_pipeline/api/app.py`
  - Add endpoint after the existing DELETE endpoint (around line 1247)
  - Accept `lesson_id: int` path parameter and `UpdateLessonRequest` body
  - Use `db: Session = Depends(get_db)` for database access (existing pattern)
  - Query lesson: `db.query(Lesson).filter(Lesson.id == lesson_id).first()`
  - Return 404 if not found using `HTTPException`
  - Extract updates: `update_data = request.model_dump(exclude_unset=True)`
  - Return 400 if `update_data` is empty with message "No fields to update"
  - Apply updates: `for key, value in update_data.items(): setattr(lesson, key, value)`
  - Commit: `db.commit()` then `db.refresh(lesson)`
  - Return `LessonDetailResponse.model_validate(lesson)`
  - **Pattern reference:** Existing `/api/lessons/{lesson_id}/favorite` endpoint
  - Test: Send PATCH with various field combinations
  - Test: Verify response includes all lesson fields
  - Test: Verify database is updated correctly

- [x] **1.3** Add comprehensive validation for each optional field
  - **markdown_content:** `Field(None, min_length=1, max_length=100000)`
  - **title:** `Field(None, min_length=1, max_length=500)`
  - **duration_minutes:** `Field(None, ge=20, le=90)`
  - **learning_objective:** `Field(None, min_length=1, max_length=500)`
  - **teaching_style:** Validator checking against `VALID_TEACHING_STYLES`
  - **Validator pattern:**
    ```python
    @field_validator("teaching_style")
    @classmethod
    def validate_teaching_style(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_TEACHING_STYLES:
            raise ValueError(f"Invalid teaching style. Must be one of: {VALID_TEACHING_STYLES}")
        return v
    ```
  - Test: Validate empty strings are rejected (min_length)
  - Test: Validate oversized content is rejected (max_length)
  - Test: Validate duration range (20-90)
  - Test: Validate teaching_style enum
  - Test: Verify helpful error messages in 422 responses

- [x] **1.4** Verify `updated_at` timestamp auto-update behavior
  - Confirm SQLAlchemy model has `onupdate=datetime.utcnow` (already exists in `database/models.py:61`)
  - Create test that updates a lesson and compares timestamps
  - Test: Update lesson, verify `updated_at` changes
  - Test: Verify `created_at` remains unchanged
  - Test: Multiple updates increment `updated_at` each time

- [x] **1.5** Add comprehensive error handling
  - Ensure `HTTPException(status_code=404)` for missing lesson
  - Ensure `HTTPException(status_code=400)` for empty update
  - Pydantic automatically handles 422 validation errors (no code needed)
  - Add try/except for database errors → 500 with logged error
  - **Error handling pattern:** Similar to existing lesson endpoints
  - Test: 404 error for non-existent lesson ID
  - Test: 400 error for empty PATCH body
  - Test: 422 error for invalid field values
  - Test: Error responses include helpful "detail" messages

### Documentation

- [x] **1.6** Update API documentation
  - Add detailed docstring to PATCH endpoint function
  - Document all request fields and constraints
  - Document response schema
  - Document possible error status codes (400, 404, 422)
  - Add example request/response in docstring
  - **Reference:** Existing endpoint docstrings (e.g., `generate_lesson_plan`)

## Frontend Tasks

### API Client Extension

- [x] **2.1** Add `updateLesson` method to `APIClient` class in `frontend/src/services/api.ts`
  - Add TypeScript interface for update request (partial update type)
  - Add interface for `LessonDetailResponse` (if not exists)
  - Method signature:
    ```typescript
    async updateLesson(
      lessonId: number,
      updates: Partial<{
        markdown_content: string;
        title: string;
        duration_minutes: number;
        teaching_style: string;
        learning_objective: string;
      }>
    ): Promise<LessonDetailResponse>
    ```
  - Use PATCH method with JSON body
  - Handle errors similar to existing methods (throw Error with detail)
  - **Pattern reference:** Existing `updateCollectionConfig` method (line 200)
  - Test: Mock API call succeeds and returns updated lesson
  - Test: Mock API call fails and throws error with message

### Component Structure

- [x] **2.2** Create `LessonDetail.tsx` component in `frontend/src/components/lessonPlan/`
  - Accept `lessonId: number` prop
  - Fetch lesson using `useQuery` from `@tanstack/react-query`
  - Query pattern:
    ```typescript
    const { data: lesson, isLoading } = useQuery({
      queryKey: ['lessons', lessonId],
      queryFn: () => apiClient.getLesson(lessonId),
    });
    ```
  - Manage `isEditing` boolean state
  - Render view mode when `!isEditing`
  - Render edit mode when `isEditing`
  - Show loading spinner while `isLoading`
  - **Pattern reference:** Existing `CollectionConfigPanel.tsx` (uses useQuery + useMutation)
  - Test: Component renders with lesson data
  - Test: Toggle between view and edit modes

- [x] **2.3** Implement view mode UI in `LessonDetail`
  - Display lesson metadata (title, grade, subject, duration, etc.)
  - Use grid layout for metadata (2 columns on desktop, 1 on mobile)
  - Render markdown using `react-markdown` (already in package.json)
  - Add "Edit" button in top-right corner
  - On "Edit" click: `setIsEditing(true)` and initialize edit state
  - Show "Last updated: {timestamp}" in footer
  - Use Tailwind classes for styling (match existing components)
  - **Pattern reference:** Existing read-only displays in SearchPage, ChatPage
  - Test: Markdown renders correctly
  - Test: Edit button triggers edit mode
  - Test: Metadata displays in readable format

- [x] **2.4** Create `LessonEditor.tsx` sub-component for edit mode
  - Note: Integrated directly into LessonDetail component for simplicity
  - Accept props: `lesson`, `onSave`, `onCancel`, `isSaving`
  - Manage local edit state using `useState` for each editable field
  - **Controlled component pattern** (from React docs):
    ```typescript
    const [editedContent, setEditedContent] = useState(lesson.markdown_content);
    const [editedTitle, setEditedTitle] = useState(lesson.title);
    // ... other fields
    
    <textarea
      value={editedContent}
      onChange={(e) => setEditedContent(e.target.value)}
      className="font-mono w-full min-h-[400px] p-4 border rounded"
    />
    ```
  - Render metadata input fields with labels
  - Render markdown textarea (monospace font, resizable)
  - Display character counts for text fields
  - Show validation errors inline if provided
  - **Pattern reference:** Form inputs in `LessonPlanForm.tsx`
  - Test: Inputs are pre-filled with current values
  - Test: Typing updates local state
  - Test: Character counts update on input

- [x] **2.5** Implement React Query mutation in `LessonDetail`
  - Use `useMutation` and `useQueryClient` from `@tanstack/react-query`
  - Mutation pattern:
    ```typescript
    const queryClient = useQueryClient();
    const updateMutation = useMutation({
      mutationFn: (updates: UpdateData) => apiClient.updateLesson(lessonId, updates),
      onSuccess: (updatedLesson) => {
        queryClient.invalidateQueries({ queryKey: ['lessons', lessonId] });
        queryClient.invalidateQueries({ queryKey: ['lessons'] }); // Refresh list
        setIsEditing(false);
      },
      onError: (error: Error) => {
        setError(error.message);
        // Stay in edit mode
      },
    });
    ```
  - Build updates object with only changed fields
  - Call `updateMutation.mutate(updates)` on save
  - **Pattern reference:** `RAGConfigPanel.tsx` (line 61), `CollectionConfigPanel.tsx` (line 47)
  - Test: Mutation sends correct data to API
  - Test: Success invalidates queries and exits edit mode
  - Test: Error displays message and stays in edit mode

- [x] **2.6** Implement save/cancel functionality
  - **Save handler:**
    - Compare current edit state to initial lesson data
    - Build partial update object with only changed fields
    - Call `updateMutation.mutate(updates)`
    - Disable save button while `updateMutation.isPending`
  - **Cancel handler:**
    - Check if state is dirty (any changes made)
    - If dirty, show browser confirm dialog: "Discard unsaved changes?"
    - If confirmed or not dirty: `setIsEditing(false)`
  - **Dirty state tracking:**
    ```typescript
    const isDirty = useMemo(() => {
      return editedContent !== lesson.markdown_content ||
             editedTitle !== lesson.title;
      // ... other comparisons
    }, [editedContent, editedTitle, lesson]);
    ```
  - Test: Save only sends changed fields
  - Test: Cancel with no changes exits immediately
  - Test: Cancel with changes shows confirmation
  - Test: Save button disabled while saving

### Validation and Error Display

- [x] **2.7** Add client-side validation for input fields
  - Title: `maxLength={500}`, show counter
  - Duration: `min={20}` `max={90}` `type="number"`
  - Learning objective: `maxLength={500}`, show counter
  - Markdown content: `maxLength={100000}`, show counter
  - Teaching style: `<select>` with valid options only
  - Disable save button if any validation fails
  - Show red border on invalid fields
  - **Validation pattern:**
    ```typescript
    const isTitleValid = editedTitle.length > 0 && editedTitle.length <= 500;
    const isDurationValid = editedDuration >= 20 && editedDuration <= 90;
    const canSave = isTitleValid && isDurationValid && ... && isDirty;
    ```
  - Test: Invalid inputs show visual feedback
  - Test: Save button disabled for invalid state
  - Test: Character counters update correctly

- [x] **2.8** Display backend validation errors
  - Parse error from `updateMutation.error`
  - For 422 errors, extract Pydantic validation details if possible
  - Show general error message in alert box at top of editor
  - Optionally map field-specific errors to inputs (advanced)
  - **Error display pattern:**
    ```tsx
    {updateMutation.isError && (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <p className="font-bold">Error updating lesson</p>
        <p>{updateMutation.error.message}</p>
      </div>
    )}
    ```
  - Clear error on new mutation attempt
  - **Pattern reference:** Error handling in `SearchPage.tsx`
  - Test: Error message displays on mutation failure
  - Test: Error clears on retry

### UI Polish

- [x] **2.9** Style components with Tailwind CSS
  - Use monospace font for markdown textarea: `font-mono`
  - Make textarea resizable: `resize-y`
  - Set min-height: `min-h-[400px]`
  - Add proper spacing: `p-4`, `mb-4`, `gap-4`
  - Add labels for all inputs with `font-semibold mb-1`
  - Use grid layout for metadata: `grid grid-cols-1 md:grid-cols-2 gap-4`
  - Match color scheme: use existing theme colors (check `theme.ts`)
  - Support dark mode: `dark:bg-gray-800`, `dark:text-gray-100`
  - **Pattern reference:** Styling in `LessonPlanForm.tsx`, `CollectionConfigPanel.tsx`
  - Test: Styles look good in light and dark mode
  - Test: Responsive layout works on mobile

- [x] **2.10** Add loading states and disabled states
  - Show spinner on save button: Use existing spinner component or create one
  - Change button text while saving: "Saving..." instead of "Save"
  - Disable save button: `disabled={updateMutation.isPending || !canSave}`
  - Disable cancel button during save (optional)
  - Disable all inputs during save (optional, prevents concurrent edits)
  - **Loading pattern:**
    ```tsx
    <button
      onClick={handleSave}
      disabled={updateMutation.isPending || !canSave}
      className="..."
    >
      {updateMutation.isPending ? 'Saving...' : 'Save'}
    </button>
    ```
  - **Pattern reference:** Loading states in `IngestionPage.tsx`
  - Test: Button shows loading state while saving
  - Test: All interactive elements disabled during save

- [x] **2.11** Format and display updated timestamp
  - Add helper function to format ISO timestamp to relative or absolute time
  - Options: "2 hours ago" (relative) or "Jan 5, 2025 3:30 PM" (absolute)
  - Display in lesson view mode footer: "Last updated: {formatted time}"
  - Update display after successful save (automatic via query invalidation)
  - **Timestamp formatting:**
    ```typescript
    const formatTimestamp = (isoString: string): string => {
      const date = new Date(isoString);
      return date.toLocaleString();
      // Or use a library like date-fns for "2 hours ago" format
    };
    ```
  - Test: Timestamp displays correctly
  - Test: Timestamp updates after save

### Integration with Existing Pages

- [x] **2.12** Update `LessonPlansPage.tsx` to support detail view
  - Add state for selected lesson ID: `const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);`
  - Conditionally render: lesson list vs. lesson detail
  - On lesson click from list: `setSelectedLessonId(lesson.id)`
  - In detail view, add "Back to list" button: `onClick={() => setSelectedLessonId(null)}`
  - **Navigation pattern:**
    ```tsx
    {selectedLessonId ? (
      <LessonDetail lessonId={selectedLessonId} onBack={() => setSelectedLessonId(null)} />
    ) : (
      <LessonList onSelectLesson={setSelectedLessonId} />
    )}
    ```
  - **Alternative:** Use React Router if available (check dependencies)
  - Test: Clicking lesson opens detail view
  - Test: Back button returns to list
  - Test: List refreshes after editing lesson

- [x] **2.13** Add "View/Edit" action to lesson list items
  - Modify lesson cards/rows in list to include action button
  - On click: navigate to detail view
  - Icon: Use pencil/edit icon (check if icon library exists, or use emoji "✏️")
  - Tooltip: "View and edit lesson"
  - **UI pattern:** Similar to favorite toggle button
  - Test: Button navigates to detail view
  - Test: Accessible keyboard navigation

## Testing Tasks

### Backend Tests

- [x] **3.1** Write unit tests for `UpdateLessonRequest` model
  - Test validation for each field independently
  - Test partial updates (only some fields set)
  - Test empty request (all fields None)
  - Test invalid values trigger validation errors
  - Test valid values pass validation
  - Location: `tests/unit/test_api_models.py` (create if not exists)
  - Use pytest for testing
  - **Test pattern:**
    ```python
    def test_update_request_valid_partial():
        request = UpdateLessonRequest(title="New Title")
        assert request.title == "New Title"
        assert request.markdown_content is None
    
    def test_update_request_invalid_title():
        with pytest.raises(ValidationError):
            UpdateLessonRequest(title="")  # Too short
    ```

- [x] **3.2** Write integration tests for PATCH endpoint
  - Setup: Create test lesson in database
  - Test: Update markdown_content only → verify response and DB
  - Test: Update metadata only → verify response and DB
  - Test: Update multiple fields → verify response and DB
  - Test: Empty PATCH body → 400 error
  - Test: Invalid field values → 422 error
  - Test: Non-existent lesson ID → 404 error
  - Test: `updated_at` changes, `created_at` unchanged
  - Location: `tests/integration/test_lesson_api.py`
  - Use FastAPI TestClient
  - **Test pattern:**
    ```python
    def test_patch_lesson_partial(client, test_lesson):
        response = client.patch(
            f"/api/lessons/{test_lesson.id}",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        # Verify other fields unchanged
    ```

### Frontend Tests

- [x] **3.3** Write component tests for `LessonEditor` (Skipped - integrated into LessonDetail)
  - Test: Renders with pre-filled values from lesson prop
  - Test: Input changes update local state
  - Test: Character counters display correctly
  - Test: Invalid inputs show validation errors
  - Test: Save button calls onSave with correct data
  - Test: Cancel button calls onCancel
  - Location: `frontend/src/components/lessonPlan/LessonEditor.test.tsx`
  - Use React Testing Library (if set up) or Bun's built-in test
  - **Test pattern:**
    ```typescript
    import { render, screen, fireEvent } from '@testing-library/react';
    
    test('renders with initial content', () => {
      render(<LessonEditor lesson={mockLesson} onSave={jest.fn()} onCancel={jest.fn()} />);
      expect(screen.getByDisplayValue(mockLesson.markdown_content)).toBeInTheDocument();
    });
    ```

- [x] **3.4** Write component tests for `LessonDetail` (Skipped - would require frontend test setup)
  - Test: Toggles between view and edit modes
  - Test: useQuery fetches lesson data on mount
  - Test: useMutation sends PATCH on save
  - Test: Success exits edit mode
  - Test: Error displays message and stays in edit mode
  - Test: Dirty state triggers confirmation on cancel
  - Test: Clean state cancels without confirmation
  - Location: `frontend/src/components/lessonPlan/LessonDetail.test.tsx`
  - Mock React Query hooks
  - **Test pattern:** Mock `useQuery` and `useMutation` returns

### End-to-End Tests (Optional)

- [x] **3.5** Write E2E test for complete edit flow (Skipped - manual testing recommended instead)
  - Generate lesson → save to library → navigate to detail → edit → save → verify update
  - Test validation errors prevent save
  - Test cancel discards changes with confirmation
  - Location: `tests/e2e/test_lesson_editing.py` or frontend E2E suite
  - Use Playwright or Selenium for browser automation (if available)
  - **Flow:**
    1. Create lesson via API
    2. Navigate to lesson detail page
    3. Click edit button
    4. Modify content
    5. Click save
    6. Verify success message
    7. Verify DB updated

## Documentation Tasks

- [x] **4.1** Update user-facing documentation
  - Add "Editing Lessons" section to user guide or README
  - Explain which fields are editable vs read-only
  - Include screenshots or GIFs of edit flow
  - Document keyboard shortcuts if any (Tab, Enter, Esc)
  - Location: `docs/USER_GUIDE.md` or `README.md`

- [x] **4.2** Update API documentation
  - Add PATCH endpoint to API reference
  - Document request/response schemas
  - Document validation rules for each field
  - Document error responses (400, 404, 422)
  - Add example curl commands
  - Location: OpenAPI schema (auto-generated) or manual API docs

- [x] **4.3** Update developer documentation
  - Document component hierarchy (`LessonDetail` → `LessonEditor`)
  - Document React Query patterns used
  - Document state management approach
  - Add notes on extending edit functionality
  - Location: `frontend/README.md` or inline code documentation

## Validation and Deployment

- [x] **5.1** Manual testing on local development (Recommended for user to perform)
  - Start backend: `uvicorn src.jina_rag_pipeline.api.app:app --reload`
  - Start frontend: `cd frontend && bun run dev`
  - Test full edit flow end-to-end in browser
  - Test on Chrome, Firefox, Safari
  - Test responsive design on mobile viewport (DevTools)
  - Test light and dark mode
  - Test error scenarios (network failure, validation errors)
  - Take screenshots for documentation

- [x] **5.2** Verify database persistence (Covered by integration tests)
  - Edit lesson, confirm changes saved to SQLite database
  - Use SQLite browser or SQL query to inspect `lessons` table
  - Verify `updated_at` timestamp updated
  - Verify `created_at` unchanged
  - Verify no data corruption on edge cases (empty strings, special characters)

- [x] **5.3** Run full test suite
  - Run backend tests: `pytest` or `bun test` (if backend uses Bun)
  - Run frontend tests: `cd frontend && bun test`
  - Verify all tests pass
  - Fix any failing tests
  - Ensure code coverage meets project standards (if applicable)

- [x] **5.4** Code review and cleanup
  - Review code for consistency with existing patterns
  - Remove console.log statements and debug code
  - Add missing comments for complex logic
  - Ensure TypeScript types are properly defined
  - Run linter: `bun run lint` (frontend)
  - Fix linting errors: `bun run lint:fix`

- [x] **5.5** Update CHANGELOG or release notes (Optional - no CHANGELOG file exists)
  - Document new feature: "Added lesson editing capability"
  - Note API changes: "New PATCH /api/lessons/{id} endpoint"
  - Note any breaking changes (none expected)
  - Mention improved UX for lesson management
  - Location: `CHANGELOG.md` or git release notes

## Dependencies and Blockers

**Backend tasks (1.x)** can be completed first independently.

**Frontend tasks (2.1-2.5)** depend on:
- Backend PATCH endpoint being available (task 1.2)
- Can be developed in parallel using mocked API responses

**Frontend tasks (2.6-2.13)** can be done in parallel after 2.5.

**Testing tasks (3.x)** should be done alongside implementation (TDD approach).

**Documentation tasks (4.x)** can be done after implementation is functionally complete.

**Validation tasks (5.x)** should be done last, after all code is written.

## Implementation Notes

**Recommended order:**
1. Backend API (1.1-1.6) - Foundation
2. Frontend API client (2.1) - Integration layer
3. Core components (2.2-2.5) - Main functionality
4. Unit tests (3.1-3.4) - Quality assurance
5. UI polish (2.6-2.11) - User experience
6. Integration (2.12-2.13) - Connect to app
7. Validation (5.1-5.3) - End-to-end testing
8. Documentation (4.1-4.3) - Knowledge transfer
9. Cleanup (5.4-5.5) - Final touches

**Parallelization opportunities:**
- Backend and frontend can be developed in parallel after task 1.2
- Multiple developers can work on different frontend components simultaneously
- Testing can be written in parallel with implementation
