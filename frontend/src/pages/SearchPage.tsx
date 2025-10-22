import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../styles/theme';
import SearchBar from '../components/search/SearchBar';
import ResultsList from '../components/search/ResultsList';
import CollectionSelector from '../components/collections/CollectionSelector';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ImageSearchUpload from '../components/search/ImageSearchUpload';
import { apiClient } from '../services/api';
import type { SearchRequest, SearchResponse } from '../services/api';

type SearchMode = 'text' | 'image';
type ModalityFilter = 'all' | 'image' | 'text';
type RegionTypeFilter = 'all' | 'Text' | 'Image' | 'Table' | 'Title' | 'List';

export default function SearchPage() {
  const [searchMode, setSearchMode] = useState<SearchMode>('text');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [topK, setTopK] = useState(5);
  const [searchTrigger, setSearchTrigger] = useState(0);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [modalityFilter, setModalityFilter] = useState<ModalityFilter>('all');
  const [regionTypeFilter, setRegionTypeFilter] = useState<RegionTypeFilter>('all');

  const { data: collections, refetch: refetchCollections } = useQuery({
    queryKey: ['collections'],
    queryFn: () => apiClient.getCollections(),
  });

  // Text search query
  const { data: textSearchResults, isLoading: isTextSearchLoading, error: textSearchError } = useQuery({
    queryKey: ['search', searchQuery, selectedCollection, topK, regionTypeFilter, searchTrigger],
    queryFn: async (): Promise<SearchResponse> => {
      const request: SearchRequest = {
        query: searchQuery,
        collection_name: selectedCollection,
        top_k: topK,
      };

      // Add region type filter if specified
      if (regionTypeFilter !== 'all') {
        request.metadata_filter = {
          region_type: regionTypeFilter,
        };
      }

      return apiClient.search(request);
    },
    enabled: searchMode === 'text' && searchTrigger > 0 && !!searchQuery && !!selectedCollection,
  });

  // Image search mutation
  const imageSearchMutation = useMutation({
    mutationFn: async ({ image, collection, topK, filter }: {
      image: File;
      collection: string;
      topK: number;
      filter?: 'image' | 'text';
    }) => {
      return apiClient.searchByImage(image, collection, topK, filter);
    },
  });

  const handleTextSearch = () => {
    if (searchQuery && selectedCollection) {
      setSearchTrigger(prev => prev + 1);
    }
  };

  const handleImageSearch = () => {
    if (selectedImage && selectedCollection) {
      const filter = modalityFilter === 'all' ? undefined : modalityFilter as 'image' | 'text';
      imageSearchMutation.mutate({
        image: selectedImage,
        collection: selectedCollection,
        topK,
        filter,
      });
    }
  };

  const handleImageSelect = (file: File) => {
    setSelectedImage(file);
  };

  const handleCollectionCreated = (collectionName: string) => {
    // Refresh collections list
    refetchCollections();
  };

  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  // Determine current search results and loading/error states
  const searchResults = searchMode === 'text' ? textSearchResults : imageSearchMutation.data;
  const isLoading = searchMode === 'text' ? isTextSearchLoading : imageSearchMutation.isPending;
  const error = searchMode === 'text' ? textSearchError : imageSearchMutation.error;

  const ModeToggle = () => (
    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
      <button
        onClick={() => setSearchMode('text')}
        style={{
          flex: 1,
          padding: '0.75rem',
          backgroundColor: searchMode === 'text' ? colors.button.active : colors.button.inactive,
          color: searchMode === 'text' ? 'white' : colors.text.primary,
          border: searchMode === 'text' ? 'none' : `1px solid ${colors.border}`,
          borderRadius: '0.375rem',
          cursor: 'pointer',
          fontWeight: searchMode === 'text' ? 'bold' : 'normal',
          fontSize: '1rem',
          transition: 'all 0.2s',
        }}
      >
        Text Search
      </button>
      <button
        onClick={() => setSearchMode('image')}
        style={{
          flex: 1,
          padding: '0.75rem',
          backgroundColor: searchMode === 'image' ? colors.button.active : colors.button.inactive,
          color: searchMode === 'image' ? 'white' : colors.text.primary,
          border: searchMode === 'image' ? 'none' : `1px solid ${colors.border}`,
          borderRadius: '0.375rem',
          cursor: 'pointer',
          fontWeight: searchMode === 'image' ? 'bold' : 'normal',
          fontSize: '1rem',
          transition: 'all 0.2s',
        }}
      >
        Image Search
      </button>
    </div>
  );

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{
        backgroundColor: colors.bg.secondary,
        padding: '2rem',
        borderRadius: '0.5rem',
        boxShadow: `0 2px 4px ${colors.shadow}`,
        marginBottom: '2rem',
        transition: 'all 0.2s',
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: colors.text.primary }}>
          Search Documents
        </h2>

        <ModeToggle />

        {collections && (
          <CollectionSelector
            collections={collections.collections}
            selectedCollection={selectedCollection}
            onSelect={setSelectedCollection}
            onCollectionCreated={handleCollectionCreated}
          />
        )}

        {searchMode === 'text' ? (
          <SearchBar
            query={searchQuery}
            onQueryChange={setSearchQuery}
            onSearch={handleTextSearch}
            topK={topK}
            onTopKChange={setTopK}
          />
        ) : (
          <React.Fragment>
            <ImageSearchUpload
              onImageSelect={handleImageSelect}
              disabled={!selectedCollection}
            />

            {/* Modality Filter */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 'bold',
                color: colors.text.primary,
                marginBottom: '0.5rem',
              }}>
                Search in:
              </label>
              <select
                value={modalityFilter}
                onChange={(e) => setModalityFilter(e.target.value as ModalityFilter)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  backgroundColor: colors.bg.primary,
                  color: colors.text.primary,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                }}
              >
                <option value="all">All (Images and Text)</option>
                <option value="image">Images Only</option>
                <option value="text">Text Only</option>
              </select>
            </div>

            {/* Top K Slider */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 'bold',
                color: colors.text.primary,
                marginBottom: '0.5rem',
              }}>
                Number of results: {topK}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            {/* Search Button */}
            <button
              onClick={handleImageSearch}
              disabled={!selectedImage || !selectedCollection}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: (!selectedImage || !selectedCollection) ? colors.button.inactive : colors.status.success,
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: (!selectedImage || !selectedCollection) ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                fontSize: '1rem',
                opacity: (!selectedImage || !selectedCollection) ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              Search with Image
            </button>
          </React.Fragment>
        )}
      </div>

      {isLoading && <LoadingSpinner />}

      {error && (
        <div style={{
          backgroundColor: '#fed7d7',
          color: '#c53030',
          padding: '1rem',
          borderRadius: '0.5rem',
          marginBottom: '1rem'
        }}>
          Error: {error instanceof Error ? error.message : 'Search failed'}
        </div>
      )}

      {searchResults && (
        <React.Fragment>
          {/* Region Type Filter */}
          <div style={{
            backgroundColor: colors.bg.secondary,
            padding: '1rem',
            borderRadius: '0.5rem',
            boxShadow: `0 2px 4px ${colors.shadow}`,
            marginBottom: '1rem',
            display: 'flex',
            gap: '1rem',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 'bold',
                color: colors.text.primary,
                marginBottom: '0.5rem',
              }}>
                Filter by Region Type:
              </label>
              <select
                value={regionTypeFilter}
                onChange={(e) => setRegionTypeFilter(e.target.value as RegionTypeFilter)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  backgroundColor: colors.bg.primary,
                  color: colors.text.primary,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                }}
              >
                <option value="all">All Types</option>
                <option value="Text">Text</option>
                <option value="Image">Image</option>
                <option value="Table">Table</option>
                <option value="Title">Title</option>
                <option value="List">List</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
              {regionTypeFilter !== 'all' && (
                <button
                  onClick={() => setRegionTypeFilter('all')}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: colors.button.inactive,
                    color: colors.text.primary,
                    border: `1px solid ${colors.border}`,
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    transition: 'all 0.2s',
                  }}
                >
                  Clear Filter
                </button>
              )}
              <div style={{
                padding: '0.5rem 1rem',
                backgroundColor: colors.bg.tertiary,
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                color: colors.text.secondary,
                fontWeight: 'bold',
              }}>
                {searchResults.results.length} result{searchResults.results.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          <ResultsList results={searchResults.results} />
        </React.Fragment>
      )}
    </div>
  );
}
