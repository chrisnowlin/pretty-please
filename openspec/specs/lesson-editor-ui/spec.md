# lesson-editor-ui Specification

## Purpose
TBD - created by archiving change add-lesson-editability. Update Purpose after archive.
## Requirements
### Requirement: Display Edit Mode Toggle

The system SHALL provide a way to switch between view and edit modes for saved lessons.

#### Scenario: Show edit button in view mode

**Given** user is viewing a saved lesson  
**When** the lesson detail page renders  
**Then** an "Edit" button is displayed  
**And** the button is positioned in the top-right area near other actions

#### Scenario: Enter edit mode

**Given** user is viewing a saved lesson  
**When** user clicks "Edit" button  
**Then** the view switches to edit mode  
**And** editable fields become interactive  
**And** the "Edit" button is replaced with "Save" and "Cancel" buttons

#### Scenario: Exit edit mode via cancel

**Given** user is in edit mode  
**When** user clicks "Cancel" button  
**Then** the view returns to read-only mode  
**And** any unsaved changes are discarded  
**And** the "Save" and "Cancel" buttons are replaced with "Edit" button

### Requirement: Provide Markdown Content Editor

The system SHALL display a textarea for editing lesson markdown content.

#### Scenario: Show markdown textarea in edit mode

**Given** user enters edit mode  
**When** the edit view renders  
**Then** a textarea is displayed containing the current markdown content  
**And** the textarea uses a monospace font  
**And** the textarea is resizable (vertically)  
**And** the textarea has minimum height to show significant content

#### Scenario: Edit markdown content

**Given** user is in edit mode  
**When** user types or modifies text in the markdown textarea  
**Then** the changes are reflected in the local state  
**And** the "Save" button remains enabled

#### Scenario: Display markdown in view mode

**Given** user is in view mode  
**When** the lesson is displayed  
**Then** the markdown content is shown in a read-only formatted view  
**And** no textarea or editing controls are visible

### Requirement: Provide Metadata Field Editors

The system SHALL display input fields for editable metadata in edit mode.

#### Scenario: Show title input field

**Given** user is in edit mode  
**When** the metadata section renders  
**Then** a text input for "Title" is displayed  
**And** the input is pre-filled with the current title  
**And** the input accepts text up to 500 characters

#### Scenario: Show duration input field

**Given** user is in edit mode  
**When** the metadata section renders  
**Then** a number input for "Duration (minutes)" is displayed  
**And** the input is pre-filled with current duration  
**And** the input has min=20 and max=90 constraints

#### Scenario: Show teaching style selector

**Given** user is in edit mode  
**When** the metadata section renders  
**Then** a select dropdown for "Teaching Style" is displayed  
**And** the dropdown includes options: balanced, direct, inquiry, project  
**And** the current teaching_style is selected by default

#### Scenario: Show learning objective textarea

**Given** user is in edit mode  
**When** the metadata section renders  
**Then** a textarea for "Learning Objective" is displayed  
**And** the textarea is pre-filled with current objective  
**And** the textarea accepts text up to 500 characters

#### Scenario: Display non-editable metadata

**Given** user is in edit mode  
**When** the metadata section renders  
**Then** grade, subject, topic are displayed as read-only labels  
**And** these fields do not have input controls

### Requirement: Save Changes to Backend

The system SHALL send updated lesson data to the backend when user saves.

#### Scenario: Save successful edit

**Given** user has modified markdown content and/or metadata  
**When** user clicks "Save" button  
**Then** a PATCH request is sent to `/api/lessons/{lesson_id}`  
**And** the request body includes only modified fields  
**And** the UI shows a loading state during the request  
**And** on success, the UI returns to view mode with updated content  
**And** a success notification is displayed

#### Scenario: Handle save error

**Given** user clicks "Save" button  
**When** the PATCH request fails (network error or 4xx/5xx)  
**Then** the UI remains in edit mode  
**And** an error message is displayed describing the failure  
**And** the user's edits are preserved in the editor  
**And** the user can retry saving or cancel

#### Scenario: Disable save button during save

**Given** user clicks "Save" button  
**When** the PATCH request is in progress  
**Then** the "Save" button is disabled  
**And** a loading spinner is shown on or near the button  
**And** the "Cancel" button remains enabled

### Requirement: Display Validation Errors

The system SHALL show field-specific validation errors from the backend.

#### Scenario: Show empty content error

**Given** user clears all markdown content  
**When** user clicks "Save"  
**And** backend returns 400 with "Markdown content cannot be empty"  
**Then** an error message is displayed near the markdown textarea  
**And** the textarea is highlighted as invalid

#### Scenario: Show duration range error

**Given** user enters duration = 100  
**When** user clicks "Save"  
**And** backend returns 400 with duration range error  
**Then** an error message is displayed near the duration field  
**And** the field is highlighted as invalid

#### Scenario: Clear errors on edit

**Given** a validation error is displayed  
**When** user modifies the invalid field  
**Then** the error message is cleared  
**And** the field highlighting is removed

### Requirement: Update UI State After Save

The system SHALL refresh the lesson display with the saved changes.

#### Scenario: Reflect updated content

**Given** user successfully saves edited content  
**When** the view mode is re-entered  
**Then** the displayed lesson content matches the saved content  
**And** the displayed metadata matches the saved metadata

#### Scenario: Update timestamp display

**Given** user successfully saves edits  
**When** the view mode is re-entered  
**Then** the "Last updated" timestamp shows the new update time  
**And** the timestamp is formatted in a human-readable way

### Requirement: Preserve Unsaved Changes Warning

The system SHALL warn users about unsaved changes before discarding them.

#### Scenario: Warn on cancel with changes

**Given** user has modified content or metadata  
**And** user has not saved  
**When** user clicks "Cancel" button  
**Then** a confirmation dialog appears: "Discard unsaved changes?"  
**And** if user confirms, changes are discarded and view mode is entered  
**And** if user cancels the dialog, editing continues

#### Scenario: No warning when no changes made

**Given** user entered edit mode  
**And** user has not modified any fields  
**When** user clicks "Cancel" button  
**Then** no confirmation dialog appears  
**And** view mode is entered immediately

### Requirement: Responsive Layout for Editor

The system SHALL display the editor appropriately on different screen sizes.

#### Scenario: Desktop layout

**Given** user is on a desktop viewport (≥1024px wide)  
**When** edit mode is active  
**Then** the markdown textarea takes up at least 60% of viewport height  
**And** metadata fields are displayed in a 2-column grid  
**And** save/cancel buttons are positioned in the top-right

#### Scenario: Mobile layout

**Given** user is on a mobile viewport (<768px wide)  
**When** edit mode is active  
**Then** the markdown textarea takes up full width  
**And** metadata fields are stacked vertically (1 column)  
**And** save/cancel buttons are full-width at the bottom

