import { colors, Theme } from './theme';

export function getPrimaryButtonStyle(theme: Theme, isActive = false) {
  const themeColors = colors[theme];
  return {
    padding: '0.5rem 1rem',
    backgroundColor: isActive ? themeColors.button.active : themeColors.button.inactive,
    color: isActive ? 'white' : themeColors.text.primary,
    border: isActive ? 'none' : `1px solid ${themeColors.border}`,
    borderRadius: '0.375rem',
    fontSize: '0.875rem',
    fontWeight: isActive ? 'bold' : 'normal',
    cursor: 'pointer',
    transition: 'all 0.2s',
  };
}

export function getCardStyle(theme: Theme) {
  const themeColors = colors[theme];
  return {
    backgroundColor: themeColors.bg.secondary,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    boxShadow: `0 2px 4px ${themeColors.shadow}`,
    transition: 'all 0.2s',
  };
}

export function getInputStyle(theme: Theme) {
  const themeColors = colors[theme];
  return {
    padding: '0.75rem',
    border: `1px solid ${themeColors.border}`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    backgroundColor: themeColors.bg.secondary,
    color: themeColors.text.primary,
    transition: 'all 0.2s',
  };
}
