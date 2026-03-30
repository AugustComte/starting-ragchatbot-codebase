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
