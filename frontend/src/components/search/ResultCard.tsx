import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import type { SearchResult } from '../../services/api';
import RegionMetadataBadge from './RegionMetadataBadge';

interface ResultCardProps {
  result: SearchResult;
}

export default function ResultCard({ result }: ResultCardProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

   const score = result.score || 0;
   const scorePercentage = (score * 100).toFixed(1);
   const scoreColor = score > 0.8 ? colors.status.success : score > 0.5 ? colors.status.warning : colors.status.error;

  // Extract region metadata
  const regionType = result.metadata.region_type as string | undefined;
  const pageNumber = result.metadata.page_number as number | undefined;

  return (
    <div style={{
      position: 'relative',
      backgroundColor: colors.bg.secondary,
      padding: '1.5rem',
      borderRadius: '0.5rem',
      boxShadow: `0 2px 4px ${colors.shadow}`,
      borderLeft: `4px solid ${scoreColor}`,
      transition: 'all 0.2s',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.875rem', color: colors.text.tertiary, marginBottom: '0.25rem' }}>
            ID: {result.id}
          </div>
          {result.metadata.source && (
            <div style={{ fontSize: '0.875rem', color: colors.text.secondary, fontWeight: 'bold' }}>
              Source: {result.metadata.source}
            </div>
          )}
        </div>
        <div style={{
          backgroundColor: scoreColor,
          color: 'white',
          padding: '0.25rem 0.75rem',
          borderRadius: '9999px',
          fontSize: '0.875rem',
          fontWeight: 'bold'
        }}>
          {scorePercentage}%
        </div>
      </div>

      {result.document && (
        <div style={{
          fontSize: '0.9375rem',
          lineHeight: '1.6',
          color: colors.text.primary,
          marginBottom: '1rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {result.document}
        </div>
      )}

      {Object.keys(result.metadata).length > 0 && (
        <details style={{ fontSize: '0.875rem', color: colors.text.secondary }}>
          <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Metadata</summary>
          <pre style={{
            marginTop: '0.5rem',
            padding: '0.5rem',
            backgroundColor: colors.bg.tertiary,
            borderRadius: '0.25rem',
            overflow: 'auto',
            color: colors.text.primary,
          }}>
            {JSON.stringify(result.metadata, null, 2)}
          </pre>
        </details>
      )}

      <RegionMetadataBadge region_type={regionType} page_number={pageNumber} />
    </div>
  );
}
