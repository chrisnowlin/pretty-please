/**
 * Typed wrapper hooks for React Query to provide better type safety
 * and enforce consistent patterns across the application.
 */

import { useQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import type { SearchRequest, SearchResponse, CollectionsResponse, IngestionStatusResponse } from '../services/api';

/**
 * Type-safe hook for search queries with counter-based triggering.
 *
 * Pattern: Use a numeric trigger that increments on each search to force refetch.
 * This is more reliable than boolean flags with React Query v5.
 *
 * @example
 * const [searchTrigger, setSearchTrigger] = useState(0);
 * const { data, isLoading } = useSearchQuery(
 *   { query: 'test', collection_name: 'docs', top_k: 5 },
 *   searchTrigger
 * );
 * // To trigger search: setSearchTrigger(prev => prev + 1)
 */
export function useSearchQuery(
  request: SearchRequest,
  trigger: number,
  options?: Omit<UseQueryOptions<SearchResponse>, 'queryKey' | 'queryFn'>
): UseQueryResult<SearchResponse> {
  const { query, collection_name, top_k = 5 } = request;

  return useQuery<SearchResponse>({
    queryKey: ['search', query, collection_name, top_k, trigger],
    queryFn: async (): Promise<SearchResponse> => {
      const { apiClient } = await import('../services/api');
      return apiClient.search(request);
    },
    enabled: trigger > 0 && !!query && !!collection_name,
    ...options,
  });
}

/**
 * Type-safe hook for fetching collections.
 *
 * @example
 * const { data: collections } = useCollectionsQuery();
 */
export function useCollectionsQuery(
  options?: Omit<UseQueryOptions<CollectionsResponse>, 'queryKey' | 'queryFn'>
): UseQueryResult<CollectionsResponse> {
  return useQuery<CollectionsResponse>({
    queryKey: ['collections'],
    queryFn: async (): Promise<CollectionsResponse> => {
      const { apiClient } = await import('../services/api');
      return apiClient.getCollections();
    },
    ...options,
  });
}

/**
 * Type-safe hook for polling ingestion status.
 *
 * @example
 * const { data: status } = useIngestionStatusQuery(taskId, {
 *   refetchInterval: 1000, // Poll every second
 * });
 */
export function useIngestionStatusQuery(
  taskId: string | null,
  options?: Omit<UseQueryOptions<IngestionStatusResponse>, 'queryKey' | 'queryFn'>
): UseQueryResult<IngestionStatusResponse> {
  return useQuery<IngestionStatusResponse>({
    queryKey: ['ingestion-status', taskId],
    queryFn: async (): Promise<IngestionStatusResponse> => {
      if (!taskId) throw new Error('Task ID is required');
      const { apiClient } = await import('../services/api');
      return apiClient.getIngestionStatus(taskId);
    },
    enabled: !!taskId,
    ...options,
  });
}

/**
 * Best Practices for React Query in this project:
 *
 * 1. COUNTER PATTERN FOR TRIGGERED QUERIES
 *    Use numeric counters instead of boolean flags:
 *    ✅ const [trigger, setTrigger] = useState(0)
 *    ❌ const [shouldFetch, setShouldFetch] = useState(false)
 *
 * 2. INCLUDE TRIGGER IN QUERY KEY
 *    Ensures React Query detects the change:
 *    ✅ queryKey: ['search', ...params, trigger]
 *    ❌ queryKey: ['search', ...params]
 *
 * 3. INCREMENT COUNTER TO TRIGGER
 *    Use functional update for reliability:
 *    ✅ setTrigger(prev => prev + 1)
 *    ❌ setTrigger(trigger + 1)
 *
 * 4. USE TYPED HOOKS
 *    Leverage these utility hooks for type safety:
 *    ✅ useSearchQuery(request, trigger)
 *    ❌ useQuery({ queryKey: [...], queryFn: ... })
 */
