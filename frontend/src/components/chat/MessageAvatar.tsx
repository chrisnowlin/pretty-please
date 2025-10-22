import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface MessageAvatarProps {
  role: 'user' | 'assistant';
}

export function MessageAvatar({ role }: MessageAvatarProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const avatarStyle = {
    width: '2rem',
    height: '2rem',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '0.875rem',
    fontWeight: '500',
    flexShrink: 0,
  };

  if (role === 'user') {
    return (
      <div style={{
        ...avatarStyle,
        backgroundColor: colors.button.active,
      }}>
        <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
        </svg>
      </div>
    );
  }

  return (
    <div style={{
      ...avatarStyle,
      background: `linear-gradient(to bottom right, ${colors.status.success}, ${colors.status.warning})`,
    }}>
      <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="currentColor" viewBox="0 0 20 20">
        <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
        <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
      </svg>
    </div>
  );
}
