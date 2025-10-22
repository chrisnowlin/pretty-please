import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: colors.bg.primary,
      color: colors.text.primary,
      transition: 'background-color 0.3s, color 0.3s',
    }}>
      <header style={{
        backgroundColor: colors.header,
        color: colors.headerText,
        padding: '1rem 2rem',
        boxShadow: `0 2px 4px ${colors.shadow}`
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Jina RAG Pipeline</h1>
      </header>
      <main style={{ flex: 1, padding: '2rem' }}>
        {children}
      </main>
    </div>
  );
}
