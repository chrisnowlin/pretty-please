# Add Lesson Editability

**Status:** Proposed  
**Change ID:** `add-lesson-editability`

## Summary

Enables teachers to manually edit saved lesson plans through a PATCH API endpoint and frontend markdown editor. Teachers can modify lesson content and key metadata fields (title, duration, teaching style, learning objective) after generation.

## Key Changes

### Backend
- **New PATCH endpoint:** `/api/lessons/{lesson_id}` for partial updates
- **Request model:** `UpdateLessonRequest` with optional fields for content and metadata
- **Validation:** Field-level validation with helpful error messages
- **Auto-timestamps:** `updated_at` automatically set on any update

### Frontend
- **Edit mode toggle:** Switch between view and edit modes
- **Markdown editor:** Simple textarea for editing lesson content
- **Metadata inputs:** Editable fields for title, duration, teaching style, and objective
- **Unsaved changes warning:** Confirmation dialog before discarding edits
- **Error handling:** Display backend validation errors inline

## Scope

**Includes:**
- Manual editing of lesson markdown and metadata
- Client and server-side validation
- Timestamp tracking (updated_at)

**Excludes:**
- AI re-generation
- Version history/undo
- Rich WYSIWYG editor
- Multi-user collaboration

## Files

- `proposal.md` - Problem statement and high-level solution
- `design.md` - Architecture decisions and detailed design
- `tasks.md` - Ordered implementation tasks with dependencies
- `specs/lesson-update-api/spec.md` - Backend API requirements
- `specs/lesson-editor-ui/spec.md` - Frontend UI requirements

## Dependencies

- Existing lesson persistence (Phase 3) ✅
- Database `updated_at` field ✅
- No breaking changes to existing API

## Validation

```bash
openspec validate add-lesson-editability --strict
```

✅ **Status:** Valid

## Next Steps

1. Review proposal with team/stakeholders
2. Approve or request changes
3. Begin implementation following `tasks.md`
4. Run `openspec apply add-lesson-editability` when complete
