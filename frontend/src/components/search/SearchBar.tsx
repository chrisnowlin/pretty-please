import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface SearchBarProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  topK: number;
  onTopKChange: (topK: number) => void;
}

export default function SearchBar({
  query,
  onQueryChange,
  onSearch,
  topK,
  onTopKChange,
}: SearchBarProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSearch();
    }
  };

  const inputStyle = {
    flex: 1,
    padding: '0.75rem',
    border: `1px solid ${colors.border}`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    backgroundColor: colors.bg.secondary,
    color: colors.text.primary,
    transition: 'all 0.2s',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter your search query..."
          style={inputStyle}
        />
        <button
          onClick={onSearch}
          style={{
            padding: '0.75rem 2rem',
            backgroundColor: colors.button.active,
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '1rem',
            transition: 'all 0.2s',
          }}
        >
          Search
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <label style={{ fontSize: '0.875rem', color: colors.text.secondary }}>
          Number of results:
        </label>
        <input
          type="number"
          min="1"
          max="100"
          value={topK}
          onChange={(e) => onTopKChange(parseInt(e.target.value) || 5)}
          style={{
            width: '5rem',
            padding: '0.5rem',
            border: `1px solid ${colors.border}`,
            borderRadius: '0.375rem',
            backgroundColor: colors.bg.secondary,
            color: colors.text.primary,
            transition: 'all 0.2s',
          }}
        />
      </div>
    </div>
  );
}
