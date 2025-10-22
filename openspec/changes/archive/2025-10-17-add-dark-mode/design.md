## Context
The frontend currently uses hardcoded colors with inline styles. Adding dark mode requires:
1. A centralized theme system that manages color state
2. System preference detection using CSS media query API
3. User preference persistence across sessions
4. Consistent color application across all components

## Goals / Non-Goals

### Goals
- Support light and dark themes
- Detect and respect system color scheme preferences
- Allow user override of system preference
- Persist user preference in browser
- Maintain accessibility standards (WCAG AA contrast ratios)
- Keep implementation lightweight and maintainable

### Non-Goals
- Multiple color themes beyond light/dark
- Custom color picker UI
- Server-side theme synchronization
- Theme for backend/API

## Decisions

### Architecture: React Context + Hooks
- **Decision**: Use React Context API for theme state management with a custom useTheme hook
- **Why**: Lightweight, no external dependencies, direct React idiom, all data available in frontend
- **Alternatives considered**:
  - localStorage only: Doesn't react to system preference changes in real-time
  - Tailwind theme configuration: Limited to CSS, doesn't manage state well

### Color Palette: CSS Variables
- **Decision**: Define theme colors as CSS variables (--color-bg, --color-text, etc.) in a constants file
- **Why**: Easy to reference, update, and maintain; centralized; can be exported to CSS if needed
- **Alternatives considered**:
  - Inline theme objects per component: Scattered, hard to maintain
  - CSS-in-JS library: Overkill, adds dependency

### System Preference Detection: matchMedia API
- **Decision**: Use `window.matchMedia('(prefers-color-scheme: dark)')` to detect system preference
- **Why**: Native browser API, reactive (supports addEventListener), no dependencies
- **Alternatives considered**:
  - User-Agent parsing: Fragile, unreliable
  - Manual OS detection: Not possible in browser

### Storage: localStorage
- **Decision**: Store user preference as `theme: 'light' | 'dark' | 'system'` in localStorage
- **Why**: Simple, persistent across sessions, synchronous, no server needed
- **Alternatives considered**:
  - IndexedDB: Overkill for simple preference
  - Server-side: Requires authentication, adds complexity

### Initialization Order
1. Check localStorage for saved preference
2. If found, use saved preference
3. If not found or preference is 'system', detect system preference
4. Apply theme to document root

## Risks / Trade-offs

### Risk: User switches OS theme while app running
- **Mitigation**: Attach listener to matchMedia that updates app when system preference changes (only when user preference is 'system')

### Risk: Initial page load flashing wrong theme
- **Mitigation**: Load theme synchronously during app init before rendering, or use CSS media query directly on document root

### Risk: CSS not loaded fast enough
- **Mitigation**: Ensure theme application happens before component render

### Risk: Accessibility contrast ratios
- **Mitigation**: Use approved WCAG AA color combinations; validate with contrast checker tool

## Migration Plan
No migration needed - this is a new feature with backward-compatible defaults (light mode when theme not set).

## Open Questions
- Should we provide per-component color overrides, or enforce global theme consistency?
  - **Recommendation**: Enforce global theme consistency initially; add per-component if specific colors needed later
