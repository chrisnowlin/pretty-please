import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface MessageInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  disabled: boolean;
  isGenerating: boolean;
  placeholder?: string;
}

export function MessageInput({
  value,
  onChange,
  onSubmit,
  disabled,
  isGenerating,
  placeholder = "Type your message... (Enter to send, Shift+Enter for new line)"
}: MessageInputProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled && !isGenerating) {
        onSubmit();
      }
    }
  };

  return (
    <div style={{
      borderTop: `1px solid ${colors.border}`,
      padding: '0.5rem 1rem'
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}>
        <textarea
          value={value}
          onChange={onChange}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          style={{
            flex: 1,
            padding: '0.5rem',
            border: `1px solid ${colors.border}`,
            borderRadius: '0.25rem',
            resize: 'none',
            fontSize: '0.875rem',
            outline: 'none',
            backgroundColor: colors.bg.primary,
            color: colors.text.primary,
            transition: 'border-color 0.2s, box-shadow 0.2s'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = colors.button.active;
            e.currentTarget.style.boxShadow = `0 0 0 2px ${colors.button.active}33`;
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.boxShadow = 'none';
          }}
          rows={2}
          disabled={disabled || isGenerating}
          aria-label="Chat message input"
        />
        <button
          onClick={onSubmit}
          disabled={!value.trim() || disabled || isGenerating}
          style={{
            alignSelf: 'flex-end',
            backgroundColor: (!value.trim() || disabled || isGenerating) ? colors.button.inactive : colors.button.active,
            color: 'white',
            padding: '0.5rem 1.5rem',
            borderRadius: '0.25rem',
            border: 'none',
            minHeight: '2.75rem',
            fontWeight: '500',
            transition: 'background-color 0.2s',
            outline: 'none',
            cursor: (!value.trim() || disabled || isGenerating) ? 'not-allowed' : 'pointer'
          }}
          onMouseEnter={(e) => {
            if (!(!value.trim() || disabled || isGenerating)) {
              e.currentTarget.style.backgroundColor = colors.button.active;
            }
          }}
          onMouseLeave={(e) => {
            if (!(!value.trim() || disabled || isGenerating)) {
              e.currentTarget.style.backgroundColor = colors.button.active;
            }
          }}
          aria-label="Send message"
        >
          Send
        </button>
      </div>
    </div>
  );
}
