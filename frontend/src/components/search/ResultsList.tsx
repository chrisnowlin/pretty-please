import React, { useState, useMemo } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import ResultCard from './ResultCard';
import ImageResultCard from './ImageResultCard';
import type { SearchResult } from '../../services/api';

interface ResultsListProps {
  results: SearchResult[];
}

type FilterType = 'all' | 'text' | 'image';
type ViewMode = 'list' | 'grid';

export default function ResultsList({ results }: ResultsListProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [filter, setFilter] = useState<FilterType>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  // Separate results by type
  const { textResults, imageResults } = useMemo(() => {
    const text: SearchResult[] = [];
    const images: SearchResult[] = [];

    results.forEach((result) => {
      if (result.result_type === 'image') {
        images.push(result);
      } else {
        text.push(result);
      }
    });

    return { textResults: text, imageResults: images };
  }, [results]);

  // Apply filter
  const filteredResults = useMemo(() => {
    switch (filter) {
      case 'text':
        return textResults;
      case 'image':
        return imageResults;
      default:
        return results;
    }
  }, [filter, results, textResults, imageResults]);

  if (results.length === 0) {
    return (
      <div
        style={{
          backgroundColor: colors.bg.secondary,
          padding: '3rem',
          borderRadius: '0.5rem',
          textAlign: 'center',
          color: colors.text.secondary,
          transition: 'all 0.2s',
        }}
      >
        No results found. Try a different search query.
      </div>
    );
  }

  const FilterButton = ({ type, label }: { type: FilterType; label: string }) => (
    <button
      onClick={() => setFilter(type)}
      style={{
        padding: '0.5rem 1rem',
        backgroundColor: filter === type ? colors.button.active : colors.button.inactive,
        color: filter === type ? 'white' : colors.text.primary,
        border: filter === type ? 'none' : `1px solid ${colors.border}`,
        borderRadius: '0.375rem',
        fontSize: '0.875rem',
        fontWeight: filter === type ? 'bold' : 'normal',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {label}
    </button>
  );

  const ViewToggle = () => (
    <div style={{ display: 'flex', gap: '0.5rem' }}>
      <button
        onClick={() => setViewMode('list')}
        style={{
          padding: '0.5rem',
          backgroundColor: viewMode === 'list' ? colors.button.active : colors.button.inactive,
          color: viewMode === 'list' ? 'white' : colors.text.primary,
          border: viewMode === 'list' ? 'none' : `1px solid ${colors.border}`,
          borderRadius: '0.375rem',
          cursor: 'pointer',
          fontSize: '0.875rem',
        }}
      >
        📋 List
      </button>
      <button
        onClick={() => setViewMode('grid')}
        style={{
          padding: '0.5rem',
          backgroundColor: viewMode === 'grid' ? colors.button.active : colors.button.inactive,
          color: viewMode === 'grid' ? 'white' : colors.text.primary,
          border: viewMode === 'grid' ? 'none' : `1px solid ${colors.border}`,
          borderRadius: '0.375rem',
          cursor: 'pointer',
          fontSize: '0.875rem',
        }}
      >
        🖼️ Grid
      </button>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header with filters and stats */}
      <div
        style={{
          backgroundColor: colors.bg.secondary,
          padding: '1rem',
          borderRadius: '0.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          transition: 'all 0.2s',
        }}
      >
        <div>
          <div style={{ fontSize: '0.875rem', color: colors.text.secondary, marginBottom: '0.5rem' }}>
            Found {results.length} result{results.length !== 1 ? 's' : ''} ({textResults.length} text,{' '}
            {imageResults.length} image)
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <FilterButton type="all" label="All" />
            <FilterButton type="text" label="Text Only" />
            <FilterButton type="image" label="Images Only" />
          </div>
        </div>
        {imageResults.length > 0 && <ViewToggle />}
      </div>

      {/* Results Display */}
      {viewMode === 'grid' && filter !== 'text' ? (
        // Grid view for images
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '1rem',
          }}
        >
          {filteredResults.map((result) =>
            result.result_type === 'image' ? (
              <ImageResultCard key={result.id} result={result} />
            ) : (
              <div key={result.id} style={{ gridColumn: '1 / -1' }}>
                <ResultCard result={result} />
              </div>
            )
          )}
        </div>
      ) : (
        // List view
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredResults.map((result) =>
            result.result_type === 'image' ? (
              <div key={result.id} style={{ maxWidth: '400px' }}>
                <ImageResultCard result={result} />
              </div>
            ) : (
              <ResultCard key={result.id} result={result} />
            )
          )}
        </div>
      )}
    </div>
  );
}
