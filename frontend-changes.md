# Frontend Changes

## Code Quality Tooling Added

### Prettier (Automatic Code Formatter)

Added [Prettier](https://prettier.io/) as the frontend code formatting tool — the JS/CSS/HTML equivalent of Python's `black`.

**New files:**
- `frontend/package.json` — npm project config with `format` and `format:check` scripts
- `frontend/.prettierrc` — formatting rules (2-space indent, single quotes, 100-char line width, LF line endings)
- `frontend/.prettierignore` — excludes `node_modules/` and `package-lock.json`
- `scripts/check-frontend.sh` — shell script to run formatting checks from the project root

### Formatting Applied

Prettier was run on all three frontend files. Key changes:

**`script.js`**
- Indentation normalized from 4 spaces to 2 spaces throughout
- Removed duplicate blank lines (e.g., between `setupEventListeners` sections)
- Trailing commas added inside multi-line objects/arrays (`es5` style)
- Arrow function parameters wrapped in parens: `button =>` → `(button) =>`
- Long `addMessage(...)` call in `createNewSession` broken across lines for readability

**`style.css`**
- Indentation normalized to 2 spaces throughout

**`index.html`**
- Indentation normalized to 2 spaces throughout

## Developer Workflow

**Install dependencies (first time only):**
```bash
cd frontend && npm install
```

**Auto-format all frontend files:**
```bash
cd frontend && npm run format
```

**Check formatting without making changes (CI-friendly):**
```bash
cd frontend && npm run format:check
# or from project root:
./scripts/check-frontend.sh
```

---

## Dark/Light Theme Toggle

### Feature
Added a toggle button allowing users to switch between dark and light themes.

### Files Modified

#### `frontend/index.html`
- Added `<button id="themeToggle">` element directly inside `<body>`, before `.container`
- Button contains two SVG icons: a sun (shown in dark mode) and a moon (shown in light mode)
- `aria-label` and `title` attributes set for accessibility and keyboard navigation
- Bumped stylesheet and script cache-busting version numbers

#### `frontend/style.css`
- Added `[data-theme="light"]` CSS variable overrides with full accessibility review:
  - `--background: #f8fafc`, `--surface: #ffffff`, `--surface-hover: #e2e8f0`
  - `--text-primary: #1e293b` (~13:1 contrast on background — exceeds WCAG AAA)
  - `--text-secondary: #475569` (~5.9:1 contrast — improved from original `#64748b` ~4.9:1)
  - `--border-color: #cbd5e1` (more visible than the original `#e2e8f0`)
  - `--primary-color: #2563eb` / `--primary-hover: #1d4ed8` (unchanged; ~7.3:1 on white, passes WCAG AA/AAA)
  - `--focus-ring: rgba(37, 99, 235, 0.25)` (stronger than dark mode for light backgrounds)
  - `--welcome-border: #93c5fd` (softer accent for the light card border)
  - `--shadow` uses lower-opacity values suited to light surfaces
- Fixed hardcoded dark-mode source link colors (`#6db3f2` / `#9dcbf7` — invisible on light):
  - `[data-theme="light"] .sources-content a` → `#1d4ed8` (~5.4:1 on assistant bubble)
  - Hover state → `#1e40af`
- Fixed hardcoded dark-mode error message color (`#f87171` → `#b91c1c`, ~5.8:1 contrast)
- Fixed hardcoded dark-mode success message color (`#4ade80` → `#15803d`, ~5.1:1 contrast)
- Added light-mode overrides for `code` and `pre` block backgrounds (which used dark-specific rgba values)
- Added `#themeToggle` button styles: fixed position top-right, circular, icon-sized (40×40px)
  - Hover: highlights with primary color
  - Focus: visible focus ring (keyboard-navigable)
  - Active: subtle scale transform for tactile feedback
- Added icon visibility rules: sun shown in dark mode, moon shown in light mode
- Added `transition` declarations on key elements (body, sidebar, messages, input, etc.) for smooth 300ms theme switching

#### `frontend/script.js`
- Added `initTheme()`: reads `localStorage` preference, falls back to OS `prefers-color-scheme`
- Added `applyTheme(theme)`: sets/removes `data-theme` attribute on `<html>`, updates button aria-label, persists to `localStorage`
- Added `toggleTheme()`: flips between dark and light
- `initTheme()` called immediately (before `DOMContentLoaded`) to prevent flash of wrong theme on page load
- `setupEventListeners()` now wires up the toggle button's click handler

### Behavior
- Default theme respects the user's OS dark/light mode preference
- Selected theme is persisted in `localStorage` and restored on page reload
- Smooth 0.3s transition on all themed elements when toggling
- Button is fully keyboard-navigable (Tab to focus, Enter/Space to activate) with a visible focus ring
