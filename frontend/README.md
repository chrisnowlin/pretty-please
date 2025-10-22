# Jina RAG Pipeline Frontend

Web-based user interface for the Jina RAG Pipeline, built with React, TypeScript, and Bun 1.3.

## Features

- **Search Interface**: Query indexed documents with real-time results and relevance scores
- **Document Upload**: Drag-and-drop file upload with progress tracking
- **Collection Management**: View and manage document collections
- **Lesson Plan Generation**: Generate AI-powered lesson plans with customizable parameters
- **Lesson Editing**: Edit and update saved lesson plans with validation and auto-save
- **Real-time Updates**: WebSocket-based progress updates for document ingestion

## Development

### Prerequisites

- Bun 1.3 or higher
- Backend API running on `http://localhost:8000`

### Setup

```bash
# Install dependencies
bun install

# Start development server
bun run dev
```

The development server will start on `http://localhost:5173` and proxy API requests to the backend.

### Building for Production

```bash
# Build optimized production bundle
bun run build
```

The built files will be in the `dist/` directory and are served by the FastAPI backend.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Shared components (Layout, Navigation, LoadingSpinner)
│   │   ├── search/          # Search interface components
│   │   ├── ingestion/       # Document upload components
│   │   ├── collections/     # Collection management components
│   │   ├── lessonPlan/      # Lesson plan components
│   │   │   ├── LessonDetail.tsx       # View and edit lesson details
│   │   │   ├── LessonPlanForm.tsx     # Generate new lesson plans
│   │   │   └── ExportDropdown.tsx     # Export lesson to PDF/Markdown
│   │   └── chat/            # Chat interface components
│   ├── services/
│   │   ├── api.ts          # REST API client
│   │   └── websocket.ts    # WebSocket client for real-time updates
│   ├── pages/              # Main page components
│   │   ├── SearchPage.tsx
│   │   ├── IngestionPage.tsx
│   │   ├── LessonPlansPage.tsx        # Lesson generation and library
│   │   ├── ChatPage.tsx
│   │   └── SettingsPage.tsx
│   ├── App.tsx             # Root application component
│   └── index.tsx           # Application entry point
├── public/
│   └── index.html          # HTML template
└── dist/                   # Production build output
```

## API Integration

The frontend communicates with the backend through:

- REST API endpoints at `/api/*`
- WebSocket connections at `/ws/*`

All API calls are proxied through the development server and served directly by FastAPI in production.

## Lesson Editing Architecture

### Component Hierarchy

```
LessonPlansPage
└── LessonDetail (view/edit mode toggle)
    ├── View Mode: Display lesson with metadata
    └── Edit Mode: Editable form with validation
```

### State Management

The lesson editing feature uses React Query for server state management:

- **`useQuery`**: Fetches lesson data from `GET /api/lessons/{id}`
- **`useMutation`**: Updates lesson via `PATCH /api/lessons/{id}`
- **Query Invalidation**: Automatically refreshes data after successful updates

### Edit Flow

1. User clicks a lesson from the saved lessons list
2. `LessonDetail` component fetches lesson data
3. User clicks "Edit" button → toggles to edit mode
4. User modifies fields (controlled components with `useState`)
5. Dirty state tracking with `useMemo` detects changes
6. User clicks "Save" → builds partial update object (only changed fields)
7. `useMutation` sends `PATCH` request to backend
8. On success: queries invalidated, edit mode exits, UI updates
9. On error: error message displayed, stays in edit mode

### Validation

Client-side validation prevents invalid submissions:

- **Title**: 1-500 characters
- **Learning Objective**: 1-500 characters  
- **Markdown Content**: 1-100,000 characters
- **Duration**: 20-90 minutes (number input with min/max)
- **Teaching Style**: Dropdown with valid options only

Save button is disabled if validation fails or no changes detected.

### Editable vs. Read-Only Fields

**Editable** (via PATCH endpoint):
- `title`
- `learning_objective`
- `markdown_content`
- `duration_minutes`
- `teaching_style`

**Read-Only** (cannot be changed):
- `grade`, `subject`, `topic` (core identifiers)
- `sources_count`, `images_count` (derived from generation)
- `created_at` (immutable timestamp)
- `updated_at` (auto-updated by backend)

### Developer Notes

- Use `exclude_unset=True` pattern for partial updates to only send changed fields
- The backend PATCH endpoint auto-updates `updated_at` timestamp via SQLAlchemy `onupdate`
- Unsaved changes trigger a confirmation dialog on cancel
- Character counters provide real-time feedback for text fields
- Monospace font (`font-mono`) used for markdown textarea for better editing experience

## Testing

```bash
# Run tests
bun test
```

## Technology Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Bun 1.3**: Runtime, bundler, package manager, and test runner
- **TanStack Query**: Server state management
- **Native CSS**: Inline styles for simplicity

## Supported File Formats

The frontend supports uploading the following file types:
- `.txt` - Plain text files
- `.pdf` - PDF documents
- `.md` - Markdown files
- `.json` - JSON files
- `.csv` - CSV files

Maximum file size: 50MB per file
