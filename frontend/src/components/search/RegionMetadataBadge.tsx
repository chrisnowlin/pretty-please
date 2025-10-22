import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface RegionMetadataBadgeProps {
  region_type?: string;
  page_number?: number;
}

export default function RegionMetadataBadge({ region_type, page_number }: RegionMetadataBadgeProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  // Return null if no metadata to display
  if (!region_type && !page_number) {
    return null;
  }

  // Get color for region type
  const getRegionColor = (type?: string): string => {
    if (!type) return colors.text.tertiary;

    const regionColors = colors.regionType as Record<string, string>;
    return regionColors[type] || colors.text.tertiary;
  };

  const regionColor = getRegionColor(region_type);

  // Build badge text
  const parts: string[] = [];
  if (page_number !== undefined) {
    parts.push(`Page ${page_number}`);
  }
  if (region_type) {
    parts.push(region_type);
  }
  const badgeText = parts.join(' • ');

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '1rem',
        left: '1rem',
        backgroundColor: regionColor,
        color: 'white',
        padding: '0.25rem 0.5rem',
        borderRadius: '0.25rem',
        fontSize: '0.75rem',
        fontWeight: '600',
        display: 'flex',
        alignItems: 'center',
        gap: '0.25rem',
        boxShadow: `0 1px 3px ${colors.shadow}`,
      }}
    >
      {badgeText}
    </div>
  );
}
