import { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import type { SessionConfig } from '../../types/chat';

interface ConfigSummaryBadgeProps {
  config: SessionConfig;
}

export function ConfigSummaryBadge({ config }: ConfigSummaryBadgeProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [showTooltip, setShowTooltip] = useState(false);

  // Build compact summary
  const summaryParts: string[] = [];
  summaryParts.push(`Temp: ${config.temperature.toFixed(1)}`);

  if (config.enable_reranking !== undefined) {
    summaryParts.push(`Rerank: ${config.enable_reranking ? 'On' : 'Off'}`);
  }

  summaryParts.push(`Thinking: ${config.enable_thinking ? 'On' : 'Off'}`);

  const summary = summaryParts.join(' • ');

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.25rem 0.75rem',
          backgroundColor: colors.bg.secondary,
          border: `1px solid ${colors.border}`,
          borderRadius: '9999px',
          fontSize: '0.75rem',
          color: colors.text.secondary,
          cursor: 'help',
          transition: 'all 0.2s',
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <svg
          style={{
            width: '0.875rem',
            height: '0.875rem',
            color: colors.button.active,
          }}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <span>{summary}</span>
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 0.5rem)',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: colors.bg.primary,
            border: `1px solid ${colors.border}`,
            borderRadius: '0.5rem',
            padding: '0.75rem',
            boxShadow: `0 4px 6px -1px ${colors.shadow}, 0 2px 4px -1px ${colors.shadow}`,
            zIndex: 1000,
            minWidth: '16rem',
            whiteSpace: 'nowrap',
          }}
        >
          {/* Arrow */}
          <div
            style={{
              position: 'absolute',
              top: '-0.25rem',
              left: '50%',
              transform: 'translateX(-50%) rotate(45deg)',
              width: '0.5rem',
              height: '0.5rem',
              backgroundColor: colors.bg.primary,
              border: `1px solid ${colors.border}`,
              borderRight: 'none',
              borderBottom: 'none',
            }}
          />

          {/* Content */}
          <div style={{
            fontSize: '0.75rem',
            color: colors.text.primary,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}>
            <div style={{ fontWeight: '600', marginBottom: '0.25rem', color: colors.text.primary }}>
              Session Configuration
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.25rem 0.75rem' }}>
              <span style={{ color: colors.text.secondary }}>Temperature:</span>
              <span style={{ color: colors.text.primary }}>{config.temperature.toFixed(2)}</span>

              <span style={{ color: colors.text.secondary }}>Top P:</span>
              <span style={{ color: colors.text.primary }}>{config.top_p.toFixed(2)}</span>

              <span style={{ color: colors.text.secondary }}>Top K:</span>
              <span style={{ color: colors.text.primary }}>{config.top_k}</span>

              <span style={{ color: colors.text.secondary }}>Max History:</span>
              <span style={{ color: colors.text.primary }}>{config.max_history_turns} turns</span>

              <span style={{ color: colors.text.secondary }}>Max Tokens:</span>
              <span style={{ color: colors.text.primary }}>{config.max_tokens}</span>

              <span style={{ color: colors.text.secondary }}>Thinking Mode:</span>
              <span style={{ color: config.enable_thinking ? colors.status.success : colors.text.secondary }}>
                {config.enable_thinking ? 'Enabled' : 'Disabled'}
              </span>

              {config.enable_reranking !== undefined && (
                <>
                  <span style={{ color: colors.text.secondary }}>Reranking:</span>
                  <span style={{ color: config.enable_reranking ? colors.status.success : colors.text.secondary }}>
                    {config.enable_reranking ? 'Enabled' : 'Disabled'}
                  </span>
                </>
              )}

              {config.initial_retrieval_k !== undefined && (
                <>
                  <span style={{ color: colors.text.secondary }}>Initial Retrieval K:</span>
                  <span style={{ color: colors.text.primary }}>{config.initial_retrieval_k}</span>
                </>
              )}

              {config.rerank_top_n !== undefined && config.enable_reranking && (
                <>
                  <span style={{ color: colors.text.secondary }}>Rerank Top N:</span>
                  <span style={{ color: colors.text.primary }}>{config.rerank_top_n}</span>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
