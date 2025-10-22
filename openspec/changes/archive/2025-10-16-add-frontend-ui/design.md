# Design for Frontend UI

## Architecture Overview

The frontend will be a single-page application (SPA) that communicates with the existing FastAPI backend. The architecture maintains the local-first approach with all processing happening on-device.

```
┌─────────────────────────────────────────────────┐
│           Frontend (Browser)                     │
│  ┌──────────────────────────────────────────┐  │
│  │  React/Vue.js SPA                        │  │
│  │  ├── Search Interface                    │  │
│  │  ├── Document Upload                     │  │
│  │  ├── Results Display                     │  │
│  │  └── Collection Management               │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                     │
                     │ HTTP/WebSocket
                     ↓
┌─────────────────────────────────────────────────┐
│           Backend (FastAPI)                      │
│  ┌──────────────────────────────────────────┐  │
│  │  Extended API Endpoints                  │  │
│  │  ├── /search (existing)                  │  │
│  │  ├── /ingest/* (new)                     │  │
│  │  ├── /ws/progress (new WebSocket)        │  │
│  │  └── Static File Serving                 │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Async Task Processing                   │  │
│  │  └── Document Ingestion Pipeline         │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Technology Choices

### Frontend Framework: React
**Rationale:**
- Mature ecosystem with extensive component libraries
- Strong TypeScript support for type safety
- Large community and documentation
- React Query for efficient API state management
- Good performance with virtual DOM

**Alternative Considered:** Vue.js
- Simpler learning curve
- Built-in state management
- Smaller bundle size
- Decision: React chosen for ecosystem maturity

### Styling: Tailwind CSS
**Rationale:**
- Utility-first approach reduces CSS bloat
- Consistent design system out-of-the-box
- Responsive design utilities built-in
- Good performance with PurgeCSS
- Works well with component-based architecture

### Build Tool & Runtime: Bun 1.3
**Rationale:**
- All-in-one JavaScript runtime, bundler, test runner, and package manager
- Significantly faster than Node.js and npm/yarn/pnpm
- Built-in TypeScript support with no additional configuration
- Native bundler (`Bun.build`) eliminates need for Vite/Webpack
- Fast development server with hot module reloading
- Zero-config builds with excellent defaults
- Smaller bundle sizes and faster cold starts
- Native support for JSX/TSX without additional plugins

### State Management
- **Local State:** React hooks (useState, useReducer)
- **Server State:** React Query (TanStack Query)
- **Global State:** Context API (minimal needs)

## Component Architecture

### Core Components

```
src/
├── components/
│   ├── common/
│   │   ├── Layout.tsx
│   │   ├── Navigation.tsx
│   │   └── LoadingSpinner.tsx
│   ├── search/
│   │   ├── SearchBar.tsx
│   │   ├── SearchFilters.tsx
│   │   ├── ResultCard.tsx
│   │   └── ResultsList.tsx
│   ├── ingestion/
│   │   ├── UploadZone.tsx
│   │   ├── FilePreview.tsx
│   │   ├── ProgressTracker.tsx
│   │   └── IngestionQueue.tsx
│   └── collections/
│       ├── CollectionSelector.tsx
│       └── CollectionStats.tsx
├── services/
│   ├── api.ts           # API client
│   ├── websocket.ts     # WebSocket handler
│   └── upload.ts        # File upload utilities
├── hooks/
│   ├── useSearch.ts
│   ├── useIngestion.ts
│   └── useCollections.ts
└── pages/
    ├── SearchPage.tsx
    ├── IngestionPage.tsx
    └── CollectionsPage.tsx
```

## Bun Configuration

### Project Setup

#### package.json
```json
{
  "name": "jina-rag-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "bun run src/dev-server.ts",
    "build": "bun run src/build.ts",
    "test": "bun test",
    "preview": "bun run src/preview-server.ts"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

#### Build Script (src/build.ts)
```typescript
const result = await Bun.build({
  entrypoints: ['./src/index.tsx'],
  outdir: './dist',
  target: 'browser',
  format: 'esm',
  splitting: true,
  minify: true,
  sourcemap: 'linked',
  jsx: {
    runtime: 'automatic',
    importSource: 'react'
  },
  naming: {
    entry: '[dir]/[name].[hash].[ext]',
    chunk: '[name].[hash].[ext]',
    asset: 'assets/[name].[hash].[ext]'
  },
  define: {
    'process.env.NODE_ENV': '"production"'
  }
});

if (!result.success) {
  console.error('Build failed');
  for (const message of result.logs) {
    console.error(message);
  }
  process.exit(1);
}

console.log('Build completed successfully');
for (const output of result.outputs) {
  console.log(`  ${output.path}`);
}
```

#### Development Server (src/dev-server.ts)
```typescript
const server = Bun.serve({
  port: 5173,
  async fetch(req) {
    const url = new URL(req.url);
    
    // Proxy API requests to backend
    if (url.pathname.startsWith('/api/')) {
      return fetch(`http://localhost:8000${url.pathname}`, {
        method: req.method,
        headers: req.headers,
        body: req.body
      });
    }
    
    // Serve static files
    const filePath = url.pathname === '/' ? '/index.html' : url.pathname;
    const file = Bun.file(`./public${filePath}`);
    
    if (await file.exists()) {
      return new Response(file);
    }
    
    // SPA fallback
    return new Response(Bun.file('./public/index.html'));
  },
  development: true
});

console.log(`Development server running at http://localhost:${server.port}`);
```

### TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "lib": ["ESNext", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "noEmit": true,
    "types": ["bun-types"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

## API Design Extensions

### New Endpoints

#### Document Ingestion
```typescript
POST /api/ingest/upload
Content-Type: multipart/form-data
Body: FormData with files

Response: {
  task_id: string,
  files: Array<{
    name: string,
    status: "queued" | "processing" | "completed" | "failed",
    size: number
  }>
}
```

#### Progress Tracking
```typescript
GET /api/ingest/status/{task_id}

Response: {
  task_id: string,
  status: "pending" | "processing" | "completed" | "failed",
  progress: number, // 0-100
  current_file: string,
  processed_files: number,
  total_files: number,
  errors: Array<{file: string, error: string}>
}
```

#### WebSocket Progress
```typescript
WS /ws/progress/{task_id}

Messages: {
  type: "progress" | "complete" | "error",
  progress: number,
  message: string,
  data: any
}
```

## User Experience Flow

### Search Flow
1. User enters search query
2. Optional: Select collection and filters
3. Click search or press Enter
4. Display loading state
5. Show results with relevance scores
6. Allow pagination through results

### Ingestion Flow
1. User drags files or clicks to select
2. Files are validated (format, size)
3. Preview shows file information
4. User clicks "Upload & Process"
5. Progress bar shows real-time updates
6. Success/error notifications
7. Automatic refresh of collection stats

## Performance Considerations

### Frontend Optimization
- Lazy load routes and heavy components
- Virtualized lists for large result sets
- Image lazy loading with Intersection Observer
- Debounced search input
- Memoized expensive computations

### API Optimization
- Response caching for identical queries
- Chunked file uploads for large documents
- Pagination for search results
- WebSocket for real-time updates (no polling)
- Compressed responses with gzip

## Security Considerations

### Frontend
- Input sanitization for search queries
- File type validation before upload
- Size limits enforced client-side
- No sensitive data in local storage
- HTTPS only in production

### Backend
- File type validation server-side
- Virus scanning for uploads (future)
- Rate limiting on all endpoints
- Request size limits
- Sanitized error messages

## Deployment Strategy

### Development
```bash
# Install dependencies with Bun
bun install

# Frontend dev server
bun run dev  # Bun dev server on port 5173

# Backend dev server
uvicorn app:app --reload --port 8000
```

### Production
```bash
# Build frontend using Bun.build
bun run build  # Creates dist/ folder with optimized bundles

# Alternative: Compile to standalone executable (if needed)
bun build --compile --minify --sourcemap ./src/index.tsx --outfile frontend

# Serve through FastAPI
# Frontend served at /
# API served at /api/*
```

The frontend will be built as static files and served directly by FastAPI, maintaining a single deployment unit with no additional infrastructure requirements.

## Future Enhancements

1. **Real-time Collaboration**
   - Multiple users viewing same results
   - Shared collections
   - Collaborative annotations

2. **Advanced Visualization**
   - Embedding space visualization
   - Document clustering view
   - Query history analytics

3. **User Management**
   - Authentication/authorization
   - Personal collections
   - Usage quotas

4. **Mobile Application**
   - React Native mobile app
   - Offline support with service workers
   - Push notifications for long tasks