# Frontend UI rules

Authority: constitution P9. Detailed tokens and dependency notes:
[design system](../frontend/docs/design-system.md). Original setup scope:
[UI foundation spec](../frontend/docs/ui-foundation-spec.md).

- React/TypeScript + Vite and React Router; no Next.js conventions.
- Reuse centralized shadcn UI components and Tailwind semantic CSS tokens. Use the
  existing light/dark/system theme mechanism; avoid per-component hardcoded palettes.
- Indigo/navy/teal palette, restrained surfaces and spacing; preserve readable
  contrast, visible keyboard focus and consistent control heights.
- Lucide is the primary icon set. Icon-only controls need accessible names and
  explanatory labels/tooltips. Status must not be communicated by colour alone.
- Inputs need labels, useful validation and disabled/pending states. Dialogs/Sheets
  must preserve keyboard operation, focus management and dismiss behaviour.
- Screens define loading, empty, failure, success and access-denied states. Never
  fabricate operational metrics or expose unavailable navigation as working features.
- The app shell uses full available content width, desktop expanded/icon-only sidebar
  and an independent mobile Sheet. Content-specific readable text widths are allowed
  where intentional. Check narrow layouts without accidental horizontal overflow.
- Footer is normal-flow: bottom of viewport for short content, below long content;
  no fixed overlay and no decorative top border, per owner preference.
- `/__ui` is an isolated development-only showcase with placeholder data; preserve
  production route isolation. Do not use it as a business screen.
- Tables, Gantt, charts and drag-and-drop use the approved installed libraries when
  needed. Provide accessible alternatives to pointer-only interaction. No paid-only
  features, competing UI frameworks or duplicate icon libraries.

Verification follows the changed behaviour: typecheck/lint/build when code changes;
interaction tests for meaningful behaviour; light/dark, keyboard and responsive visual
checks when relevant. A tiny cosmetic fix needs a focused check, not duplicated tests.
Record browser evidence separately from DOM tests and state any unexecuted checks.
