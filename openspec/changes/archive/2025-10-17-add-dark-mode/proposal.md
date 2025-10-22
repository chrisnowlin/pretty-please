## Why
Users benefit from a dark mode that reduces eye strain in low-light environments and respects their system-wide theme preferences. A theme system enables future customization and improves user experience across different lighting conditions.

## What Changes
- Add light and dark color themes to the frontend
- Implement system preference detection (prefers-color-scheme)
- Store user theme preference in browser local storage
- Provide UI toggle to switch between light, dark, and system modes
- Apply theme consistently across all components

## Impact
- Affected specs: frontend
- Affected code: frontend/src/components/common/Layout.tsx, frontend/src/App.tsx, all styled components
- Breaking changes: None (adds new capability)
