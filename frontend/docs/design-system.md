# Kaizora UI foundation

Implemented 2026-10-17. Frontend only; no application modules or backend changes.

## Run and inspect

```sh
cd frontend
npm ci
npm run dev
# http://127.0.0.1:5173/__ui
npm run typecheck
npm run lint
npm run check:ui
npm run build
```

`/__ui` is a Vite development-only lazy import. Production renders the authenticated application (spec 0002) and excludes the showcase
JavaScript and specialized libraries.
The showcase does not call backend APIs. `/` redirects to the protected `/app` shell.

## Structure and conventions

- `src/components/ui`: shadcn Radix/Nova source components, plus date picker and
  accessible icon button compositions. `components.json` is the CLI configuration.
- `src/styles.css`: semantic light/dark tokens, typography, spacing/radius/shadows,
  focus and reduced motion. Use semantic classes (`bg-card`, `text-muted-foreground`)
  instead of screen-specific hex values. Default compact controls are 32px; button
  sizes also provide 24/28/36px variants. Use larger targets for touch-first screens.
- `src/components/theme/theme-provider.tsx`: light/dark/system preference,
  system change listener and resilient local persistence. Wrap future app roots
  with ThemeProvider and TooltipProvider; render one Toaster within them.
- `src/lib/utils.ts`: clsx + tailwind-merge, shared by every primitive.
- `src/dev/ui-showcase.tsx`: placeholder-only visual review surface.
- `src/foundation.css`: legacy screen styling scoped to its root.

Use 4px spacing increments, 12/14/16px text and 24/30/36px headings. Geist is
self-hosted, with a sans-serif fallback. Default icons are Lucide, 16px/2px stroke;
use 18–20px for navigation and 14–16px for inline status. Decorative icons should
be aria-hidden. Icon-only actions use IconButton with a required descriptive label
and a TooltipProvider. Never communicate status with color alone.

The exact brand teal is a swatch/accent token. `text-teal-foreground` uses a darker
light-theme shade for small accessible text. Input boundaries are darker than
subtle card borders. Dark colors use slate/navy surfaces and lighter status colors.

## Dependencies and licenses

Versions below are those resolved in package-lock.json. Existing React 19.3.1,
TypeScript 5.9.3, Vite 7.3.7 and npm were preserved.

| Dependency | Version | Purpose | License |
| --- | --- | --- | --- |
| Tailwind CSS / @tailwindcss/vite | 4.3.3 | Styling and Vite integration | MIT |
| shadcn/ui source, Radix Nova preset | CLI 4.22.0 | Shared UI components | MIT |
| radix-ui | 1.8.1 | Accessible interaction primitives | MIT |
| lucide-react | 1.59.0 | Only primary icon pack | ISC |
| class-variance-authority | 0.7.1 | Component variants | Apache-2.0 |
| clsx / tailwind-merge | 2.1.1 / 3.7.0 | Class composition | MIT |
| tw-animate-css | 1.4.0 | Primitive transitions, reduced-motion override | MIT |
| @fontsource-variable/geist | 5.3.0 | Locally served variable font | OFL-1.1 |
| cmdk | 1.1.1 | Command primitive | MIT |
| sonner | 2.0.8 | Notifications | MIT |
| react-day-picker / date-fns | 10.0.2 / 4.4.0 | Calendar and date formatting | MIT |
| @tanstack/react-table | 9.3.1 | Future advanced table engine | MIT |
| @svar-ui/react-gantt | 2.8.1 | Future free Gantt timeline | MIT |
| @dnd-kit/react | 0.5.1 | Current drag-and-drop API | MIT |
| recharts / react-is | 3.10.1 / 19.3.1 | Future charts and matching React peer | MIT |
| react-hook-form | 7.90.0 | Typed form state | MIT |
| zod / @hookform/resolvers | 3.25.76 / 5.9.2 | Schema validation and form bridge | MIT |

ESLint, @eslint/js and typescript-eslint are development-only lint tooling.
Package metadata and installed license files were checked. Preserve third-party
license notices when distributing. The copied shadcn components and supporting
stylesheet are covered by `src/styles/vendor/shadcn.LICENSE`.

### Compatibility decisions

- Followed the [official Vite installation](https://ui.shadcn.com/docs/installation/vite)
  with Tailwind 4's Vite plugin, CSS variables and the `@/*` alias.
- Used the [current dnd-kit React API](https://dndkit.com/react/quickstart/),
  `DragDropProvider` from `@dnd-kit/react`; did not install the legacy core stack.
- TanStack Table is v9 (`useTable`), not the v8 `useReactTable` API. Future features
  must use installed v9 documentation/types.
- Zod 4 initially triggered npm's optional @typeschema/zod peer conflict through
  resolvers. Compatible Zod 3.25.76 resolves cleanly without force/legacy-peer-deps.
  The resolver integration is smoke-tested.
- Removed generated `cn` and `next-themes` dependencies: the approved class helpers
  and local SPA theme provider already provide those responsibilities.
- The CLI installed itself as a runtime dependency and introduced seven transitive
  audit findings. Copied its MIT `tailwind.css` to `src/styles/vendor/shadcn.css`,
  retained the license, and removed the unnecessary CLI package. Final audit: zero.
  To add components later, use `npm exec --package=shadcn@4.22.0 -- shadcn add NAME`,
  then review generated imports (`cn`, theme provider) and package changes.

### SVAR boundary

Verified against [official installation docs](https://docs.svar.dev/react/gantt/getting-started/installation/)
and [SVAR licensing](https://svar.dev/licenses/). `@svar-ui/react-gantt` is the free
MIT package and permits commercial use under MIT notice requirements. The paid
`@svar/react-gantt` package is not installed. Do not rely on PRO auto-scheduling,
constraints/deadlines, baselines, critical path or resource planning. Recheck
feature/license boundaries before implementing a Gantt feature. No Gantt UI or
paid-only feature is implemented in this milestone.

All requested specialized packages are installed and import-checked. Full table,
chart, drag/drop, Gantt and business form integrations are intentionally deferred
until their own feature specifications. No additional UI or icon framework added.

## Database configuration (reference only)

The existing backend reads `backend/.env`. Edit its DATABASE_URL for the database
you already created (do not put these credentials in frontend environment files):

```dotenv
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@127.0.0.1:5432/YOUR_DATABASE
```

Use your actual hostname/port. The repository's Docker PostgreSQL is exposed on
55432; a separately installed local PostgreSQL commonly uses 5432. URL-encode
special password characters, e.g. `@` as `%40`, `#` as `%23`, `/` as `%2F`.
Keep the existing Django environment settings. After configuration, from the
repository root, initialize the existing application schema and optional admin:

```sh
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py createsuperuser
```

Restart Django after editing its environment. These commands were not run against
your newly created database as part of this UI task. No `.env` secrets were changed.

## Verification record

- npm install/ci and npm ls: clean peer resolution; lockfile reproducible.
- TypeScript, ESLint, production build and check:ui: passed.
- Specialized exports and Zod resolver invalid-input behavior: passed.
- Production JavaScript inspected: development showcase excluded.
- Browser: light/dark appearance, dark preference after reload, dialog Escape,
  dropdown action, calendar keyboard activation/date selection: passed.
- Responsive viewport 390px: no horizontal page overflow.
- Existing `/` foundation screen renders; backend currently unavailable, so its
  existing unavailable-state message is shown. No backend was changed/restarted.
- npm audit: zero vulnerabilities after removing the unused CLI dependency.
- npm reports an unapproved esbuild postinstall script; the installed binary works
  and Vite production build succeeds. No bypass flags were used.

These are foundation/import and browser smoke checks, not end-to-end business
feature tests or a full accessibility audit.
