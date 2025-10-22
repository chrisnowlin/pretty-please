import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import type { RetrievalMetrics } from '../../types/chat';

interface MetricsDisplayProps {
  metrics: RetrievalMetrics;
}

export default function MetricsDisplay({ metrics }: MetricsDisplayProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Auto-collapse after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsCollapsed(true);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  const handleToggle = () => {
    if (isCollapsed) {
      setIsCollapsed(false);
      setIsExpanded(!isExpanded);
    } else {
      setIsExpanded(!isExpanded);
    }
  };

  // Generate summary text
  const summaryText = () => {
    const parts: string[] = [];

    if (metrics.documents_retrieved > 0) {
      parts.push(`${metrics.documents_retrieved} doc${metrics.documents_retrieved !== 1 ? 's' : ''}`);
    }

    if (metrics.images_retrieved > 0) {
      parts.push(`${metrics.images_retrieved} image${metrics.images_retrieved !== 1 ? 's' : ''}`);
    }

    const itemsText = parts.length > 0 ? parts.join(', ') : 'No items';
    return `Retrieved ${itemsText} in ${Math.round(metrics.total_time_ms)}ms`;
  };

  if (isCollapsed && !isExpanded) {
    return null;
  }

  return (
    <div style={{
      margin: '0.75rem 0',
      padding: '0.75rem 1rem',
      backgroundColor: colors.bg.secondary,
      border: `1px solid ${colors.border}`,
      borderRadius: '0.5rem',
      fontSize: '0.875rem',
      color: colors.text.secondary,
    }}>
      {/* Summary Header (Always Visible) */}
      <div
        onClick={handleToggle}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          {/* Info Icon */}
          <svg
            style={{
              width: '1rem',
              height: '1rem',
              color: colors.text.tertiary,
              flexShrink: 0,
            }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>

          <span>{summaryText()}</span>

          {metrics.reranking_enabled && (
            <span style={{
              marginLeft: '0.25rem',
              color: colors.text.tertiary,
            }}>
              (reranked in {Math.round(metrics.reranking_time_ms)}ms)
            </span>
          )}
        </div>

        {/* Expand/Collapse Icon */}
        <svg
          style={{
            width: '1.25rem',
            height: '1.25rem',
            color: colors.text.tertiary,
            transition: 'transform 0.2s',
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div style={{
          marginTop: '0.75rem',
          paddingTop: '0.75rem',
          borderTop: `1px solid ${colors.border}`,
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr',
            gap: '0.5rem 1rem',
            fontSize: '0.8125rem',
          }}>
            {/* Vector Search Time */}
            <div style={{ color: colors.text.tertiary }}>Vector search:</div>
            <div style={{ color: colors.text.secondary }}>
              {Math.round(metrics.vector_search_time_ms)}ms
            </div>

            {/* Reranking Time */}
            {metrics.reranking_enabled && (
              <>
                <div style={{ color: colors.text.tertiary }}>Reranking:</div>
                <div style={{ color: colors.text.secondary }}>
                  {Math.round(metrics.reranking_time_ms)}ms
                </div>
              </>
            )}

            {/* Documents Retrieved */}
            <div style={{ color: colors.text.tertiary }}>Documents retrieved:</div>
            <div style={{ color: colors.text.secondary }}>
              {metrics.documents_retrieved}
            </div>

            {/* Documents After Rerank */}
            {metrics.reranking_enabled && (
              <>
                <div style={{ color: colors.text.tertiary }}>After reranking:</div>
                <div style={{ color: colors.text.secondary }}>
                  {metrics.documents_after_rerank}
                </div>
              </>
            )}

            {/* Images Retrieved */}
            {metrics.images_retrieved > 0 && (
              <>
                <div style={{ color: colors.text.tertiary }}>Images retrieved:</div>
                <div style={{ color: colors.text.secondary }}>
                  {metrics.images_retrieved}
                </div>
              </>
            )}

            {/* Compression Status */}
            {metrics.compression_enabled && (
              <>
                <div style={{ color: colors.text.tertiary }}>Compression:</div>
                <div style={{ color: colors.status.success }}>
                  Enabled
                </div>
              </>
            )}

            {/* Hybrid Search Status */}
            {metrics.hybrid_search_used && (
              <>
                <div style={{ color: colors.text.tertiary }}>Search mode:</div>
                <div style={{ color: colors.status.success }}>
                  Hybrid (semantic + keyword)
                </div>
              </>
            )}

            {/* Total Time */}
            <div style={{
              color: colors.text.tertiary,
              fontWeight: '500',
              marginTop: '0.25rem',
            }}>
              Total time:
            </div>
            <div style={{
              color: colors.text.primary,
              fontWeight: '500',
              marginTop: '0.25rem',
            }}>
              {Math.round(metrics.total_time_ms)}ms
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
