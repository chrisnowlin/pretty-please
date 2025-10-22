import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import ThemeToggle from './ThemeToggle';

interface NavigationProps {
  currentPage: 'search' | 'ingest' | 'collections' | 'chat' | 'lesson-plans' | 'settings';
  onNavigate: (page: 'search' | 'ingest' | 'collections' | 'chat' | 'lesson-plans' | 'settings') => void;
}

export default function Navigation({ currentPage, onNavigate }: NavigationProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const buttonStyle = (page: string) => ({
    padding: '0.75rem 1.5rem',
    backgroundColor: currentPage === page ? colors.button.active : colors.button.inactive,
    color: currentPage === page ? 'white' : colors.text.primary,
    border: 'none',
    borderRadius: '0.375rem',
    cursor: 'pointer',
    fontWeight: currentPage === page ? 'bold' : 'normal',
    transition: 'all 0.2s',
  });

  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '2rem',
      borderBottom: `2px solid ${colors.border}`,
      paddingBottom: '1rem',
      gap: '1rem',
    }}>
      <div style={{
        display: 'flex',
        gap: '1rem',
      }}>
        <button
          style={buttonStyle('search')}
          onClick={() => onNavigate('search')}
        >
          Search
        </button>
        <button
          style={buttonStyle('ingest')}
          onClick={() => onNavigate('ingest')}
        >
          Upload Documents
        </button>
        <button
          style={buttonStyle('collections')}
          onClick={() => onNavigate('collections')}
        >
          Collections
        </button>
        <button
          style={buttonStyle('chat')}
          onClick={() => onNavigate('chat')}
        >
          Chat
        </button>
        <button
          style={buttonStyle('lesson-plans')}
          onClick={() => onNavigate('lesson-plans')}
        >
          Lesson Plans
        </button>
        <button
          style={buttonStyle('settings')}
          onClick={() => onNavigate('settings')}
        >
          Settings
        </button>
      </div>
      <ThemeToggle />
    </nav>
  );
}
