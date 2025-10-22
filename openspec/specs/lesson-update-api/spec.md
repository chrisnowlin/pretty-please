# lesson-update-api Specification

## Purpose
TBD - created by archiving change add-lesson-editability. Update Purpose after archive.
## Requirements
### Requirement: Update Lesson Content via PATCH Endpoint

The system SHALL provide a PATCH endpoint at `/api/lessons/{lesson_id}` that accepts partial updates to saved lessons.

#### Scenario: Update only markdown content

**Given** a saved lesson with ID 123  
**When** client sends PATCH `/api/lessons/123` with body:
```json
{
  "markdown_content": "# Updated Lesson\n\nNew content here..."
}
```
**Then** the system updates only the `markdown_content` field  
**And** the `updated_at` timestamp is set to current time  
**And** returns 200 with full `LessonDetailResponse`

#### Scenario: Update only metadata fields

**Given** a saved lesson with ID 123  
**When** client sends PATCH `/api/lessons/123` with body:
```json
{
  "title": "Revised Lesson Title",
  "duration_minutes": 60
}
```
**Then** the system updates only `title` and `duration_minutes`  
**And** the `markdown_content` remains unchanged  
**And** the `updated_at` timestamp is updated  
**And** returns 200 with full `LessonDetailResponse`

#### Scenario: Update content and metadata together

**Given** a saved lesson with ID 123  
**When** client sends PATCH with both content and metadata changes  
**Then** all specified fields are updated atomically  
**And** the `updated_at` timestamp is updated once  
**And** returns 200 with updated lesson

#### Scenario: Attempt to update non-existent lesson

**Given** no lesson exists with ID 999  
**When** client sends PATCH `/api/lessons/999`  
**Then** the system returns 404  
**And** error message indicates "Lesson not found"

#### Scenario: Send empty update request

**Given** a saved lesson with ID 123  
**When** client sends PATCH with empty body `{}`  
**Then** the system returns 400  
**And** error message indicates "No fields to update"

### Requirement: Validate Markdown Content

The system SHALL validate `markdown_content` field when present in update request.

#### Scenario: Accept valid markdown content

**Given** a saved lesson  
**When** client sends markdown_content with length between 1 and 100,000 characters  
**Then** the system accepts and saves the content  
**And** returns 200

#### Scenario: Reject empty markdown content

**Given** a saved lesson  
**When** client sends `markdown_content: ""`  
**Then** the system returns 400  
**And** error message indicates "Markdown content cannot be empty"

#### Scenario: Reject oversized markdown content

**Given** a saved lesson  
**When** client sends `markdown_content` exceeding 100,000 characters  
**Then** the system returns 400  
**And** error message indicates "Markdown content exceeds maximum length"

### Requirement: Validate Metadata Fields

The system SHALL validate metadata fields when present in update request.

#### Scenario: Validate title length

**Given** a saved lesson  
**When** client sends `title` with length < 1 or > 500 characters  
**Then** the system returns 400  
**And** error message indicates title length constraint

#### Scenario: Validate duration range

**Given** a saved lesson  
**When** client sends `duration_minutes` < 20 or > 90  
**Then** the system returns 400  
**And** error message indicates valid duration range (20-90)

#### Scenario: Validate teaching style enum

**Given** a saved lesson  
**When** client sends `teaching_style: "invalid_style"`  
**Then** the system returns 400  
**And** error message lists valid styles: balanced, direct, inquiry, project

#### Scenario: Validate learning objective length

**Given** a saved lesson  
**When** client sends `learning_objective` with length < 1 or > 500 characters  
**Then** the system returns 400  
**And** error message indicates objective length constraint

### Requirement: Automatic Timestamp Management

The system SHALL automatically update the `updated_at` timestamp when any field is modified.

#### Scenario: Timestamp updated on content change

**Given** a lesson with `updated_at` = "2025-01-01T10:00:00"  
**When** client updates markdown_content at "2025-01-02T15:30:00"  
**Then** the system sets `updated_at` to "2025-01-02T15:30:00"  
**And** the `created_at` timestamp remains unchanged

#### Scenario: Timestamp updated on metadata change

**Given** a lesson with `updated_at` = "2025-01-01T10:00:00"  
**When** client updates title at "2025-01-02T15:30:00"  
**Then** the system sets `updated_at` to "2025-01-02T15:30:00"

### Requirement: Preserve Non-Editable Fields

The system SHALL ignore and preserve fields that are not editable.

#### Scenario: Ignore grade field in update

**Given** a lesson with `grade: "5"`  
**When** client sends PATCH with `{"grade": "6", "title": "New Title"}`  
**Then** the system updates only the `title`  
**And** the `grade` remains "5"  
**And** no error is returned (field is silently ignored)

#### Scenario: Ignore source counts

**Given** a lesson with `sources_count: 3`  
**When** client sends PATCH with `{"sources_count": 5}`  
**Then** the `sources_count` remains 3  
**And** the field is silently ignored

#### Scenario: Preserve created timestamp

**Given** a lesson with `created_at: "2025-01-01T10:00:00"`  
**When** client updates any field  
**Then** the `created_at` remains "2025-01-01T10:00:00"

### Requirement: Return Updated Lesson Data

The system SHALL return the complete updated lesson in the response.

#### Scenario: Response contains all lesson fields

**Given** a successful PATCH request  
**When** the update is applied  
**Then** the response body contains a `LessonDetailResponse` with:
  - `id` (database ID)
  - `lesson_id` (UUID)
  - `title`
  - `markdown_content`
  - `grade`
  - `subject`
  - `topic`
  - `learning_objective`
  - `duration_minutes`
  - `teaching_style`
  - `metadata_json`
  - `sources_count`
  - `images_count`
  - `is_favorite`
  - `created_at`
  - `updated_at` (newly updated timestamp)

#### Scenario: Response reflects all changes

**Given** client updates `title` and `duration_minutes`  
**When** the system returns the response  
**Then** the response contains the new `title` value  
**And** the response contains the new `duration_minutes` value  
**And** all other fields match the current database state

