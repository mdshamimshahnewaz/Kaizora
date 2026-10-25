import { lazy, Suspense } from "react";
import {
  Link,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
} from "react-router";
import { LoaderCircle, WifiOff } from "lucide-react";
import { AuthProvider, useAuth } from "@/features/auth/auth-provider";
const LoginPage = lazy(() =>
  import("@/features/auth/login-page").then((module) => ({
    default: module.LoginPage,
  })),
);
import { AccountProvider } from "@/features/account/account-provider";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
const AppShell = lazy(() =>
  import("./app-shell").then((module) => ({ default: module.AppShell })),
);
const HomePage = lazy(() =>
  import("./app-pages").then((module) => ({ default: module.HomePage })),
);
const AccountPage = lazy(() =>
  import("./app-pages").then((module) => ({ default: module.AccountPage })),
);

const OrganizationsPage = lazy(() => import("@/features/organizations/organization-pages").then((m) => ({ default: m.OrganizationsPage })));
const OrganizationPage = lazy(() => import("@/features/organizations/organization-pages").then((m) => ({ default: m.OrganizationPage })));
const ClientsPage = lazy(() => import("@/features/clients/clients-pages").then((m) => ({ default: m.ClientsPage })));
const ClientDetailPage = lazy(() => import("@/features/clients/clients-pages").then((m) => ({ default: m.ClientDetailPage })));
const PeoplePage = lazy(() => import("@/features/resources/resources-pages").then((m) => ({ default: m.PeoplePage })));
const PersonDetailPage = lazy(() => import("@/features/resources/resources-pages").then((m) => ({ default: m.PersonDetailPage })));
const TeamsPage = lazy(() => import("@/features/resources/resources-pages").then((m) => ({ default: m.TeamsPage })));
const TeamDetailPage = lazy(() => import("@/features/resources/resources-pages").then((m) => ({ default: m.TeamDetailPage })));
const ProjectsPage = lazy(() => import("@/features/projects/projects-pages").then((m) => ({ default: m.ProjectsPage })));
const ProjectDetailPage = lazy(() => import("@/features/projects/projects-pages").then((m) => ({ default: m.ProjectDetailPage })));

function SessionGate() {
  const { status, refresh } = useAuth();
  if (status === "loading")
    return (
      <main className="flex min-h-svh items-center justify-center">
        <p
          role="status"
          className="flex items-center gap-3 text-sm text-muted-foreground"
        >
          <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          Checking your session…
        </p>
      </main>
    );
  if (status === "unavailable")
    return (
      <main className="flex min-h-svh items-center justify-center p-6">
        <div className="max-w-sm space-y-4 text-center">
          <WifiOff
            className="mx-auto size-8 text-muted-foreground"
            aria-hidden="true"
          />
          <h1 className="text-xl font-semibold">Unable to connect</h1>
          <p className="text-sm leading-6 text-muted-foreground">
            We couldn’t verify your session. Check your connection and try
            again.
          </p>
          <Button
            onClick={() => {
              void refresh();
            }}
          >
            Try again
          </Button>
        </div>
      </main>
    );
  return <Outlet />;
}
function RequireUser() {
  const { user } = useAuth();
  const location = useLocation();
  return user ? (
    <Outlet />
  ) : (
    <Navigate to="/login" replace state={{ from: location.pathname }} />
  );
}
function NotFound() {
  return (
    <section className="mx-auto max-w-lg space-y-4 p-8">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="text-sm text-muted-foreground">
        This page doesn’t exist or has moved.
      </p>
      <Button asChild variant="outline">
        <Link to="/app">Back to home</Link>
      </Button>
    </section>
  );
}
export default function App() {
  return (
    <ThemeProvider>
      <TooltipProvider>
        <AuthProvider>
          <AccountProvider>
          <Suspense
            fallback={
              <p role="status" className="p-8 text-sm text-muted-foreground">
                Loading page…
              </p>
            }
          >
            <Routes>
              <Route element={<SessionGate />}>
                <Route path="/" element={<Navigate to="/app" replace />} />
                <Route path="/login" element={<LoginPage />} />
                <Route element={<RequireUser />}>
                  <Route path="/app" element={<AppShell />}>
                    <Route index element={<HomePage />} />
                    <Route path="account" element={<AccountPage />} />
                    <Route path="organizations" element={<OrganizationsPage />} />
                    <Route path="o/:orgId/settings" element={<OrganizationPage />} />
                    <Route path="o/:orgId/clients" element={<ClientsPage />} />
                    <Route path="o/:orgId/clients/:clientId" element={<ClientDetailPage />} />
                    <Route path="o/:orgId/resources" element={<PeoplePage />} />
                    <Route path="o/:orgId/resources/:resourceId" element={<PersonDetailPage />} />
                    <Route path="o/:orgId/teams" element={<TeamsPage />} />
                    <Route path="o/:orgId/teams/:teamId" element={<TeamDetailPage />} />
                    <Route path="o/:orgId/projects" element={<ProjectsPage />} />
                    <Route path="o/:orgId/projects/:projectId" element={<ProjectDetailPage />} />
                    <Route path="*" element={<NotFound />} />
                  </Route>
                </Route>
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </AccountProvider>
        </AuthProvider>
        <Toaster />
      </TooltipProvider>
    </ThemeProvider>
  );
}
