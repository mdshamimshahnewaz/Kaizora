# UI foundation specification

Status: implemented and verified. Scope is frontend only.

Preserve npm, React 19, strict TypeScript, Vite and the existing API connection screen.
No business modules, API changes, authentication or backend work.

## Acceptance
1. Tailwind v4 Vite plugin and shadcn/ui source components use semantic CSS tokens.
2. Indigo/navy/teal light and layered slate dark themes share typography, spacing,
   radii, elevation, focus rings and control heights. Lucide is the sole icon system.
3. Requested reusable controls exist in src/components/ui; date picker composes
   calendar/popover. Toasts use the current shadcn notification recommendation.
4. An isolated development-only /__ui showcase demonstrates both themes, controls,
   accessible dialogs/dropdowns, status colors, tables, loading and disabled states.
   It makes no API calls. The normal foundation screen retains its API behavior.
5. Verify peers/licenses before adding specialized libraries. Only free MIT SVAR
   edition is allowed. No paid features or application-specific demos.
6. Document dependencies, license boundaries and usage conventions. Validate types,
   lint/build, library imports, browser theme persistence and responsive behavior.

## Design
Use shadcn Radix-based components, CSS-variable theming, @/* alias and a Vite plugin.
Keep the original screen stylesheet scoped to its root to avoid leaking styles into
shared primitives. The showcase is dynamically imported only under import.meta.env.DEV.
A reusable theme provider owns light/dark/system preference and local persistence.
No router dependency is needed for a single development-only path.

## Specialized libraries
Install only after compatibility/license verification. Import smoke checks validate
exports without delivering business features or loading them in the production app.
Deferred wrappers/integrations require their own feature specifications.
