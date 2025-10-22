import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

export default function LoadingSpinner() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem'
    }}>
      <div style={{
        border: `4px solid ${colors.border}`,
        borderTop: `4px solid ${colors.button.active}`,
        borderRadius: '50%',
        width: '3rem',
        height: '3rem',
        animation: 'spin 1s linear infinite'
      }} />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
