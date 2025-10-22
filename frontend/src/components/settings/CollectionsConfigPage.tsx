import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import { apiClient } from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import CollectionConfigPanel from './CollectionConfigPanel';

export default function CollectionsConfigPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const { data: collections, isLoading, error } = useQuery({
    queryKey: ['collections'],
    queryFn: () => apiClient.getCollections(),
  });

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    return (
      <div style={{
        backgroundColor: colors.bg.tertiary,
        color: colors.text.primary,
        padding: '1rem',
        borderRadius: '0.5rem',
        border: `1px solid ${colors.border}`,
      }}>
        Error: {error instanceof Error ? error.message : 'Failed to load collections'}
      </div>
    );
  }

  const tableHeaderStyle = {
    padding: '0.75rem 1rem',
    textAlign: 'left' as const,
    fontSize: '0.875rem',
    fontWeight: '600' as const,
    color: colors.text.secondary,
    borderBottom: `2px solid ${colors.border}`,
  };

  const tableCellStyle = {
    padding: '1rem',
    borderBottom: `1px solid ${colors.border}`,
    color: colors.text.primary,
  };

  const badgeStyle = (enabled: boolean) => ({
    padding: '0.25rem 0.75rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: '600' as const,
    backgroundColor: enabled ? '#10b98120' : '#6b728020',
    color: enabled ? '#10b981' : colors.text.secondary,
    display: 'inline-block',
  });

  return (
    <div>
      <p style={{ color: colors.text.secondary, marginBottom: '1.5rem' }}>
        Manage layout analysis and processing settings for each collection.
        Changes only affect future uploads.
      </p>

      {collections && collections.collections.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          color: colors.text.secondary,
          backgroundColor: colors.bg.secondary,
          borderRadius: '0.5rem',
          border: `1px solid ${colors.border}`,
        }}>
          No collections found. Create a collection to get started.
        </div>
      ) : (
        <div style={{
          border: `1px solid ${colors.border}`,
          borderRadius: '0.5rem',
          overflow: 'hidden',
          backgroundColor: colors.bg.secondary,
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: colors.bg.tertiary }}>
              <tr>
                <th style={tableHeaderStyle}>Collection Name</th>
                <th style={tableHeaderStyle}>Documents</th>
                <th style={tableHeaderStyle}>Layout Analysis</th>
                <th style={tableHeaderStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {collections?.collections.map((collection, index) => (
                <CollectionRow
                  key={collection.name}
                  collection={collection}
                  colors={colors}
                  tableCellStyle={tableCellStyle}
                  badgeStyle={badgeStyle}
                  isLast={index === collections.collections.length - 1}
                  onConfigure={() => setSelectedCollection(collection.name)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedCollection && (
        <CollectionConfigPanel
          collectionName={selectedCollection}
          onClose={() => setSelectedCollection(null)}
        />
      )}
    </div>
  );
}

interface CollectionRowProps {
  collection: { name: string; count: number; metadata: Record<string, any> };
  colors: any;
  tableCellStyle: React.CSSProperties;
  badgeStyle: (enabled: boolean) => React.CSSProperties;
  isLast: boolean;
  onConfigure: () => void;
}

function CollectionRow({ collection, colors, tableCellStyle, badgeStyle, isLast, onConfigure }: CollectionRowProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Fetch config to determine layout analysis status
  const { data: config } = useQuery({
    queryKey: ['collection-config', collection.name],
    queryFn: () => apiClient.getCollectionConfig(collection.name),
  });

  const layoutAnalysisEnabled = config?.enable_layout_analysis ?? true; // Default to true

  return (
    <tr
      style={{
        backgroundColor: isHovered ? colors.bg.tertiary : 'transparent',
        transition: 'background-color 0.2s',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <td style={{ ...tableCellStyle, borderBottom: isLast ? 'none' : tableCellStyle.borderBottom }}>
        <div style={{ fontWeight: '600' }}>{collection.name}</div>
      </td>
      <td style={{ ...tableCellStyle, borderBottom: isLast ? 'none' : tableCellStyle.borderBottom }}>
        {collection.count}
      </td>
      <td style={{ ...tableCellStyle, borderBottom: isLast ? 'none' : tableCellStyle.borderBottom }}>
        <span style={badgeStyle(layoutAnalysisEnabled)}>
          {layoutAnalysisEnabled ? 'Enabled' : 'Disabled'}
        </span>
      </td>
      <td style={{ ...tableCellStyle, borderBottom: isLast ? 'none' : tableCellStyle.borderBottom }}>
        <button
          onClick={onConfigure}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: colors.button.active,
            color: 'white',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '600',
            transition: 'opacity 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'}
          onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
        >
          Configure
        </button>
      </td>
    </tr>
  );
}
