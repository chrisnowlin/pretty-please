# Proposal: Add Lesson Editability

## Problem Statement

Teachers generate lesson plans using the RAG pipeline, but once saved to the library, lessons cannot be modified. Teachers need to edit lessons to:
- Refine learning objectives after reviewing student needs
- Adjust timing and activities based on classroom realities
- Fix typos or clarify instructions
- Customize content for specific student populations

Currently, the system only supports:
- Generating new lessons
- Viewing saved lessons
- Deleting lessons
- Toggling favorite status

There is no way to edit the markdown content or metadata of saved lessons.

## Proposed Solution

Add lesson editing capabilities to both backend and frontend:

**Backend:**
- Add PATCH endpoint at `/api/lessons/{lesson_id}` to update lesson content and metadata
- Support partial updates (only changed fields)
- Automatically update `updated_at` timestamp
- Validate markdown content and metadata before saving

**Frontend:**
- Add edit mode to lesson detail view with markdown editor
- Allow editing of both content and key metadata fields (title, duration, etc.)
- Show save/cancel controls when editing
- Display last updated timestamp

## Scope

This change focuses on **manual editing** of already-generated lessons. It does NOT include:
- Re-generation using AI
- Version history or undo
- Collaborative editing or multi-user features
- Rich text WYSIWYG editor (markdown only)

## Benefits

- Teachers can refine AI-generated content to match their needs
- Reduces need to regenerate entire lessons for small changes
- Makes saved lessons truly reusable across semesters
- Improves practical utility of the lesson library

## Dependencies

- Requires existing lesson persistence (Phase 3) - ✅ Already implemented
- Database model already has `updated_at` field - ✅ Ready to use
- No breaking changes to existing API or data model

## Success Criteria

- [ ] Backend API accepts PATCH requests to update lesson content
- [ ] Validation ensures data integrity (markdown format, metadata constraints)
- [ ] Frontend displays edit mode with markdown textarea
- [ ] Changes are persisted and reflected immediately
- [ ] Updated timestamp shows when lesson was last modified
