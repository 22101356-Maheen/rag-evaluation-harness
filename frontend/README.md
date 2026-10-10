# Ragify frontend

Responsive React + Vite + TypeScript interface for Ragify. It includes the public marketing and authentication-preview routes plus an honest, disconnected product workspace for projects, document selection, evaluation setup, and results presentation.

The frontend intentionally makes no backend requests yet. Forms validate locally, but credentials, files, projects, and evaluation settings are never sent or persisted as product data.

## Run locally

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

## Validate

```powershell
npm run lint
npm run build
```

## Routes

Public routes:

- `/` — complete marketing landing page
- `/features` — detailed capability groups
- `/how-it-works` — full evaluation workflow
- `/sign-in` — validated sign-in preview
- `/sign-up` — validated registration preview

Product preview routes:

- `/dashboard` — empty-state overview and quick actions
- `/projects` — project resource states and local create-project draft
- `/projects/:projectId` — document selection, evaluation configuration, and latest-result state
- `/evaluations` — honest evaluation-history unavailable state
- `/results` — summary and advanced result presentation states
- `/settings` — working light/dark theme preference

Unknown routes render a helpful not-found page.

## Architecture

- `src/router/router.tsx` owns the route map, titles, scroll restoration, and route focus.
- `src/layouts/PublicLayout.tsx` owns public navigation and the footer.
- `src/layouts/AppLayout.tsx` owns the responsive product sidebar, mobile drawer, top bar, and preview notice.
- `src/components/marketing/` contains the public landing-page sections.
- `src/components/auth/` contains the reusable authentication-page shell.
- `src/components/dashboard/`, `projects/`, and `evaluation/` contain feature-specific presentation components.
- `src/components/shared/` contains shared branding, theme, page-header, and resource-state components.
- `src/components/ui/Dialog.tsx` wraps the native dialog element for accessible modals and drawers.
- `src/lib/view-models.ts` defines UI-only resource states and view models. It does not mirror a live API response.
- `src/styles/` separates design tokens/base styles, marketing styles, and product/application styles.

Tailwind CSS is configured through the Vite plugin and shares the cascade with the existing token-driven CSS. Lucide icons are used selectively. The existing `src/assets/ragify-logo.png` is used directly without modification.

## Theme behavior

Light mode is the default on a first visit, including when the operating system prefers dark mode. An explicit light or dark choice is saved under `ragify-theme`, applied before first paint by `index.html`, and synchronized across open tabs. Settings and the header toggle use the same theme context.

## Integration boundaries

Authentication, server-state caching, projects, document upload, evaluation execution, and results loading are not connected. In particular:

- Sign-in and sign-up validate fields but do not create a session or send credentials.
- Creating a project keeps only the current form draft and does not create or save a project.
- Document selection accepts one local `.txt` file, displays its metadata, and does not read or upload its contents.
- Evaluation controls validate locally and do not start an evaluation.
- Result components accept future view data but currently show explicit empty placeholders rather than invented metrics.
- Product routes are deliberately reachable as a UI preview; they are not an authentication boundary.

Future integration can be added at the route/layout and page-service boundaries without replacing the presentation components. The installed TanStack Query package remains unused, and no Clerk provider, API client, endpoint, mock server, or fabricated production data has been added.

## Source structure

```text
frontend/
├── index.html
├── package.json
├── package-lock.json
├── README.md
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── assets/
    │   └── ragify-logo.png
    ├── components/
    │   ├── auth/
    │   │   └── AuthFormLayout.tsx
    │   ├── dashboard/
    │   │   ├── DashboardEmptyState.tsx
    │   │   ├── DashboardHeader.tsx
    │   │   └── QuickActions.tsx
    │   ├── evaluation/
    │   │   ├── AdvancedDetails.tsx
    │   │   ├── EvaluationControls.tsx
    │   │   ├── EvaluationSummary.tsx
    │   │   └── types.ts
    │   ├── marketing/
    │   │   ├── CapabilitiesPreview.tsx
    │   │   ├── FinalCTA.tsx
    │   │   ├── Footer.tsx
    │   │   ├── Hero.tsx
    │   │   ├── HowItWorksPreview.tsx
    │   │   ├── Navbar.tsx
    │   │   ├── TestingToDecision.tsx
    │   │   ├── WhoItsFor.tsx
    │   │   └── WhyRagify.tsx
    │   ├── projects/
    │   │   ├── DocumentUpload.tsx
    │   │   ├── ProjectForm.tsx
    │   │   └── ProjectList.tsx
    │   ├── shared/
    │   │   ├── Brand.tsx
    │   │   ├── EmptyState.tsx
    │   │   ├── ErrorState.tsx
    │   │   ├── LoadingState.tsx
    │   │   ├── PageHeader.tsx
    │   │   ├── ThemeProvider.tsx
    │   │   └── ThemeToggle.tsx
    │   └── ui/
    │       └── Dialog.tsx
    ├── layouts/
    │   ├── AppLayout.tsx
    │   └── PublicLayout.tsx
    ├── lib/
    │   ├── constants.ts
    │   ├── theme.ts
    │   └── view-models.ts
    ├── pages/
    │   ├── app/
    │   │   ├── DashboardPage.tsx
    │   │   ├── EvaluationsPage.tsx
    │   │   ├── ProjectDetailPage.tsx
    │   │   ├── ProjectsPage.tsx
    │   │   ├── ResultsPage.tsx
    │   │   └── SettingsPage.tsx
    │   ├── auth/
    │   │   ├── SignInPage.tsx
    │   │   └── SignUpPage.tsx
    │   └── public/
    │       ├── FeaturesPage.tsx
    │       ├── HomePage.tsx
    │       ├── HowItWorksPage.tsx
    │       └── NotFoundPage.tsx
    ├── router/
    │   └── router.tsx
    └── styles/
        ├── application.css
        ├── globals.css
        └── marketing.css
```
