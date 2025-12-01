# Repository Guidelines

## Project Structure & Module Organization
- `pages/` holds all routes: `_app.js` wires Layout/global styles; `index.js`, `pricing.js`, and `managed.js` are the shipped pages.
- `components/Layout.js` is the shared header/footer wrapper; add shared UI there.
- `styles/globals.css` has Tailwind base/resets; prefer utilities over custom CSS.
- Build/config files (`tailwind.config.js`, `postcss.config.js`, `next.config.js`) stay in the root; `.next/` is generated and untracked.

## Build, Test, and Development Commands
- `npm install` (Node 18+): install dependencies.
- `npm run dev`: start the Next.js dev server with hot reload.
- `npm run build`: create a production bundle in `.next/`.
- `npm start`: serve the compiled bundle (after `npm run build`).
- No lint/tests yet; use `npm run dev` for manual QA until scripts are added.

## Coding Style & Naming Conventions
- JavaScript + React function components with 2-space indentation; hooks near the top.
- Components use PascalCase; pages mirror route filenames (e.g., `pricing.js` for `/pricing`). Use camelCase for props/handlers/state setters.
- Styling is Tailwind-first; reuse tokens from `tailwind.config.js` and consistent spacing (`max-w-7xl`, `px-4`/`py-*`).
- Extract repeated UI into `components/`; avoid inline style objects unless utilities cannot cover the layout.

## Testing Guidelines
- No automated framework is configured. When adding tests, co-locate `*.test.js` next to components or use `__tests__/` mirroring `pages/` and `components/`.
- Cover new logic with unit tests; smoke-test `/`, `/pricing`, and `/managed` in `npm run dev` for regressions.
- Note any manual checks or new scripts in PR descriptions until an automated suite exists.

## Production & Deployment
- Build with `npm run build`; serve with `npm start` (`NODE_ENV=production`). Keep `.next/` and `node_modules/` out of source control.
- In CI, prefer `npm ci` to lock dependency resolutions and fail fast.
- Store client-safe config as `NEXT_PUBLIC_*` env vars; inject server-only secrets via the host (no commits).
- Put assets in `public/` and reference them with absolute paths (`/images/logo.svg`) to use Next.js static serving.

## Commit & Pull Request Guidelines
- There is no visible git history here; use concise, imperative commits (e.g., `Add managed page hero`, `Tighten pricing CTA copy`) and keep unrelated changes separated.
- PRs should include a short summary, affected pages/components, screenshots for UI updates, and test/manual-check notes; link issues or tasks when relevant.
- Keep diffs focused and update README or in-code comments whenever behavior or page structure changes.
