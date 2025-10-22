import React from 'react';
import { useTheme, type ThemeMode } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

export default function ThemeToggle() {
  const { theme, mode, setMode } = useTheme();
  const colors = getThemeColors(theme);

  const options: { mode: ThemeMode; label: string; icon: string }[] = [
    { mode: 'light', label: 'Light', icon: '☀️' },
    { mode: 'dark', label: 'Dark', icon: '🌙' },
    { mode: 'system', label: 'System', icon: '💻' },
  ];

  const buttonStyle = (isActive: boolean) => ({
    padding: '0.5rem 0.75rem',
    backgroundColor: isActive ? colors.button.active : colors.button.inactive,
    color: isActive ? 'white' : colors.text.primary,
    border: 'none',
    borderRadius: '0.375rem',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: isActive ? 'bold' : 'normal',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  });

  return (
    <div style={{
      display: 'flex',
      gap: '0.5rem',
      alignItems: 'center',
    }}>
      <span style={{
        fontSize: '0.875rem',
        color: colors.text.secondary,
        marginRight: '0.5rem',
      }}>
        Theme:
      </span>
      {options.map(({ mode: optionMode, label, icon }) => (
        <button
          key={optionMode}
          onClick={() => setMode(optionMode)}
          style={buttonStyle(mode === optionMode) as React.CSSProperties}
          title={`Switch to ${label} theme`}
          aria-label={`${label} theme`}
          aria-pressed={mode === optionMode}
        >
          <span>{icon}</span>
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}
