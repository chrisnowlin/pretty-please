# React Query Best Practices

## Overview

This document outlines the recommended patterns for using React Query v5 in this project, based on debugging and testing.

## Counter Pattern for Triggered Queries

### Problem

Boolean flags don't reliably trigger React Query refetches when changing from `false` to `true`:

```typescript
// ❌ UNRELIABLE PATTERN
const [shouldSearch, setShouldSearch] = useState(false);

const { data } = useQuery({
  queryKey: ['search', query, collection],
  queryFn: () => apiClient.search({ query, collection }),
  enabled: shouldSearch && !!query && !!collection,
});

const handleSearch = () => setShouldSearch(true); // May not refetch!
```

### Solution

Use a numeric counter that increments on each trigger:

```typescript
// ✅ RELIABLE PATTERN
const [searchTrigger, setSearchTrigger] = useState(0);

const { data } = useQuery({
  queryKey: ['search', query, collection, searchTrigger], // Include trigger!
  queryFn: () => apiClient.search({ query, collection }),
  enabled: searchTrigger > 0 && !!query && !!collection,
});

const handleSearch = () => setSearchTrigger(prev => prev + 1); // Always refetches!
```

### Why It Works

1. **Query Key Changes**: React Query detects the changed `searchTrigger` value in the query key
2. **Guaranteed Uniqueness**: Each increment creates a new, unique query key
3. **No Race Conditions**: Functional updates (`prev => prev + 1`) prevent stale state issues

## Using Typed Hooks

### Available Typed Hooks

Import from `src/hooks/useTypedQuery.ts`:

```typescript
import { useSearchQuery, useCollectionsQuery, useIngestionStatusQuery } from '../hooks/useTypedQuery';
```

### Search Query Example

```typescript
function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [topK, setTopK] = useState(5);
  const [searchTrigger, setSearchTrigger] = useState(0);

  // Use typed hook
  const { data: searchResults, isLoading, error } = useSearchQuery(
    {
      query: searchQuery,
      collection_name: selectedCollection,
      top_k: topK,
    },
    searchTrigger
  );

  const handleSearch = () => {
    if (searchQuery && selectedCollection) {
      setSearchTrigger(prev => prev + 1); // Trigger search
    }
  };

  return (
    <>
      <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
      {isLoading && <div>Loading...</div>}
      {searchResults && <ResultsList results={searchResults.results} />}
    </>
  );
}
```

### Collections Query Example

```typescript
function CollectionSelector() {
  const { data: collections, refetch } = useCollectionsQuery();

  return (
    <select>
      {collections?.collections.map(col => (
        <option key={col.name} value={col.name}>
          {col.name} ({col.count} documents)
        </option>
      ))}
    </select>
  );
}
```

### Ingestion Status Example

```typescript
function UploadProgress({ taskId }: { taskId: string }) {
  const { data: status } = useIngestionStatusQuery(taskId, {
    refetchInterval: 1000, // Poll every second
    enabled: !!taskId,
  });

  return (
    <div>
      Status: {status?.status}
      Progress: {status?.progress}%
    </div>
  );
}
```

## Key Principles

### 1. Include All Dependencies in Query Key

```typescript
// ✅ GOOD: All parameters in query key
queryKey: ['search', query, collection, topK, trigger]

// ❌ BAD: Missing parameters
queryKey: ['search', trigger]
```

### 2. Use Functional State Updates

```typescript
// ✅ GOOD: Functional update prevents stale closure
setTrigger(prev => prev + 1)

// ❌ BAD: May use stale value
setTrigger(trigger + 1)
```

### 3. Guard with Enabled Flag

```typescript
// ✅ GOOD: Prevents unnecessary API calls
enabled: trigger > 0 && !!query && !!collection

// ❌ BAD: May fire on mount with invalid data
enabled: true
```

### 4. Use Typed Hooks for Consistency

```typescript
// ✅ GOOD: Type-safe, enforces pattern
const { data } = useSearchQuery(request, trigger);

// ❌ BAD: Easy to make mistakes
const { data } = useQuery({ queryKey: [...], queryFn: ... });
```

## Common Patterns

### Dependent Queries

```typescript
// First query
const { data: collections } = useCollectionsQuery();

// Second query depends on first
const { data: collectionStats } = useQuery({
  queryKey: ['collection-stats', collections?.collections[0]?.name],
  queryFn: () => apiClient.getCollectionStats(collections!.collections[0].name),
  enabled: !!collections && collections.collections.length > 0,
});
```

### Polling Pattern

```typescript
const { data: status } = useIngestionStatusQuery(taskId, {
  refetchInterval: (query) => {
    // Stop polling when complete
    return query.state.data?.status === 'completed' ? false : 1000;
  },
});
```

### Optimistic Updates

```typescript
const { mutate } = useMutation({
  mutationFn: apiClient.createCollection,
  onMutate: async (newCollection) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['collections'] });

    // Snapshot previous value
    const previous = queryClient.getQueryData(['collections']);

    // Optimistically update
    queryClient.setQueryData(['collections'], (old) => ({
      ...old,
      collections: [...old.collections, newCollection],
    }));

    return { previous };
  },
  onError: (err, newCollection, context) => {
    // Rollback on error
    queryClient.setQueryData(['collections'], context.previous);
  },
});
```

## Migration Guide

If you have existing code using the boolean pattern:

### Before (Unreliable)

```typescript
const [shouldFetch, setShouldFetch] = useState(false);
const { data } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  enabled: shouldFetch,
});
const trigger = () => setShouldFetch(true);
```

### After (Reliable)

```typescript
const [fetchTrigger, setFetchTrigger] = useState(0);
const { data } = useQuery({
  queryKey: ['data', fetchTrigger],
  queryFn: fetchData,
  enabled: fetchTrigger > 0,
});
const trigger = () => setFetchTrigger(prev => prev + 1);
```

## References

- [React Query v5 Documentation](https://tanstack.com/query/latest)
- [Query Keys Best Practices](https://tanstack.com/query/latest/docs/react/guides/query-keys)
- Project file: `src/hooks/useTypedQuery.ts`
