import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface PromptSuggestionsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  label?: string;
}

export function PromptSuggestions({
  suggestions,
  onSelect,
  label = "Try asking:"
}: PromptSuggestionsProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1rem'
    }}>
      <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <h3 style={{
          fontSize: '1.125rem',
          fontWeight: '600',
          color: colors.text.primary,
          marginBottom: '0.5rem'
        }}>
          {label}
        </h3>
        <p style={{
          fontSize: '0.875rem',
          color: colors.text.secondary
        }}>
          Select a suggestion below or type your own question
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '0.75rem',
        width: '100%',
        maxWidth: '42rem'
      }}>
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSelect(suggestion)}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              padding: '1rem',
              textAlign: 'left',
              border: `1px solid ${colors.border}`,
              borderRadius: '0.75rem',
              backgroundColor: colors.bg.primary,
              transition: 'all 0.2s',
              boxShadow: `0 1px 2px ${colors.shadow}`,
              minHeight: '2.75rem',
              outline: 'none',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = colors.button.active;
              e.currentTarget.style.backgroundColor = colors.bg.secondary;
              e.currentTarget.style.boxShadow = `0 4px 12px ${colors.shadow}`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = colors.border;
              e.currentTarget.style.backgroundColor = colors.bg.primary;
              e.currentTarget.style.boxShadow = `0 1px 2px ${colors.shadow}`;
            }}
          >
            <div style={{
              flexShrink: 0,
              width: '2rem',
              height: '2rem',
              borderRadius: '0.5rem',
              backgroundColor: colors.bg.tertiary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.2s'
            }}>
              <svg
                style={{
                  width: '1.25rem',
                  height: '1.25rem',
                  color: colors.button.active
                }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                fontSize: '0.875rem',
                fontWeight: '500',
                color: colors.text.primary,
                transition: 'color 0.2s'
              }}>
                {suggestion}
              </p>
            </div>

            <svg
              style={{
                flexShrink: 0,
                width: '1.25rem',
                height: '1.25rem',
                color: colors.text.tertiary,
                transition: 'color 0.2s'
              }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
}
