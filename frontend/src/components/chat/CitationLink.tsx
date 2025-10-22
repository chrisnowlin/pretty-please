import React, { useState, useRef, useEffect } from 'react';
import type { CitationMetadata } from '../../types/chat';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface CitationLinkProps {
  citationId: string;
  citationData: CitationMetadata;
  onClick: (citationId: string, citationData: CitationMetadata) => void;
}

/**
 * Renders a clickable citation marker (e.g., [1], [IMG-1]) with hover tooltip
 * Follows existing accessibility patterns with ARIA labels and keyboard support
 */
export function CitationLink({ citationId, citationData, onClick }: CitationLinkProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState<'top' | 'bottom'>('top');
  const buttonRef = useRef<HTMLButtonElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onClick(citationId, citationData);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(citationId, citationData);
    }
  };

  const handleMouseEnter = () => {
    setShowTooltip(true);
  };

  const handleMouseLeave = () => {
    setShowTooltip(false);
  };

  // Calculate tooltip position based on available space
  useEffect(() => {
    if (showTooltip && buttonRef.current && tooltipRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const tooltipHeight = tooltipRef.current.offsetHeight;
      const spaceAbove = buttonRect.top;
      const spaceBelow = window.innerHeight - buttonRect.bottom;

      // Show tooltip below if there's not enough space above
      if (spaceAbove < tooltipHeight + 10 && spaceBelow > tooltipHeight + 10) {
        setTooltipPosition('bottom');
      } else {
        setTooltipPosition('top');
      }
    }
  }, [showTooltip]);

  // Generate accessible label
  const ariaLabel = citationData.type === 'image'
    ? `View image source: ${citationData.source}`
    : `View document source: ${citationData.source}`;

  // Truncate source name if too long
  const displaySource = citationData.source.length > 40
    ? citationData.source.substring(0, 37) + '...'
    : citationData.source;

  const tooltipStyle: React.CSSProperties = {
    position: 'absolute',
    [tooltipPosition === 'top' ? 'bottom' : 'top']: '100%',
    left: '50%',
    transform: 'translateX(-50%)',
    marginTop: tooltipPosition === 'bottom' ? '0.5rem' : '0',
    marginBottom: tooltipPosition === 'top' ? '0.5rem' : '0',
    backgroundColor: colors.bg.primary,
    border: `1px solid ${colors.border}`,
    borderRadius: '0.5rem',
    padding: '0.75rem',
    minWidth: '200px',
    maxWidth: '300px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    zIndex: 1000,
    pointerEvents: 'none',
    opacity: showTooltip ? 1 : 0,
    transition: 'opacity 0.2s ease-in-out',
  };

  const arrowStyle: React.CSSProperties = {
    position: 'absolute',
    [tooltipPosition === 'top' ? 'bottom' : 'top']: '-6px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: 0,
    height: 0,
    borderLeft: '6px solid transparent',
    borderRight: '6px solid transparent',
    ...(tooltipPosition === 'top'
      ? { borderTop: `6px solid ${colors.border}` }
      : { borderBottom: `6px solid ${colors.border}` }
    ),
  };

  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <button
        ref={buttonRef}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleMouseEnter}
        onBlur={handleMouseLeave}
        className="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded px-0.5 transition-colors cursor-pointer font-medium"
        aria-label={ariaLabel}
        aria-describedby={showTooltip ? `tooltip-${citationId}` : undefined}
        type="button"
        tabIndex={0}
      >
        {citationId}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div
          ref={tooltipRef}
          id={`tooltip-${citationId}`}
          role="tooltip"
          style={tooltipStyle}
        >
          <div style={arrowStyle} />
          <div style={{ fontSize: '0.875rem', lineHeight: '1.25rem' }}>
            <p style={{
              fontWeight: '600',
              color: colors.text.primary,
              marginBottom: '0.25rem'
            }}>
              {displaySource}
            </p>
            <p style={{
              color: colors.text.secondary,
              fontSize: '0.75rem',
              marginBottom: '0.5rem'
            }}>
              {citationData.type === 'image' ? '📷 Image' : '📄 Document'}
            </p>
            <div style={{
              paddingTop: '0.5rem',
              borderTop: `1px solid ${colors.border}`,
              fontSize: '0.75rem',
              color: colors.text.secondary
            }}>
              <p>Relevance: {(citationData.score * 100).toFixed(1)}%</p>
              <p style={{ marginTop: '0.25rem', fontStyle: 'italic' }}>
                Click to view details
              </p>
            </div>
          </div>
        </div>
      )}
    </span>
  );
}
