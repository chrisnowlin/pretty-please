export const colors = {
  light: {
    bg: {
      primary: '#ffffff',
      secondary: '#f9fafb',
      tertiary: '#f3f4f6',
    },
    text: {
      primary: '#1f2937',
      secondary: '#6b7280',
      tertiary: '#9ca3af',
    },
    border: '#e5e7eb',
     button: {
       active: '#4299e1',
       inactive: '#e2e8f0',
     },
     status: {
       success: '#10b981',
       warning: '#f59e0b',
       error: '#ef4444',
     },
     regionType: {
       Text: '#3b82f6',      // blue
       Image: '#8b5cf6',     // purple/violet
       Table: '#10b981',     // green
       Title: '#f97316',     // orange
       List: '#14b8a6',      // teal
     },
     header: '#4a5568',
     headerText: '#ffffff',
     shadow: 'rgba(0,0,0,0.1)',
  },
  dark: {
    bg: {
      primary: '#1a1a1a',
      secondary: '#2d2d2d',
      tertiary: '#3f3f3f',
    },
    text: {
      primary: '#f3f4f6',
      secondary: '#d1d5db',
      tertiary: '#9ca3af',
    },
    border: '#4b5563',
     button: {
       active: '#4299e1',
       inactive: '#3d3d3d',
     },
     status: {
       success: '#10b981',
       warning: '#f59e0b',
       error: '#ef4444',
     },
     regionType: {
       Text: '#3b82f6',      // blue
       Image: '#8b5cf6',     // purple/violet
       Table: '#10b981',     // green
       Title: '#f97316',     // orange
       List: '#14b8a6',      // teal
     },
     header: '#0f0f0f',
     headerText: '#f3f4f6',
     shadow: 'rgba(0,0,0,0.3)',
  },
};

export type Theme = 'light' | 'dark';

export function getThemeColors(theme: Theme) {
  return colors[theme];
}
