import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import {
  Building2,
  ChevronDown,
  CircleUserRound,
  FolderKanban,
  Home,
  Layers,
  LogOut,
  Menu,
  PanelLeft,
  Users,
  Workflow,
  BarChart3,
  ContactRound,
  UsersRound,
  Settings,
} from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeMenu } from "@/components/theme/theme-menu";
import { cn } from "@/lib/utils";
import { WorkspaceNavigation } from "@/features/organizations/workspace-navigation";

function Navigation({
  onNavigate,
  collapsed = false,
}: {
  onNavigate?: () => void;
  collapsed?: boolean;
}) {
  const location = useLocation();
  const orgId = location.pathname.match(/^\/app\/o\/([^/]+)/)?.[1];
  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "space-y-6 overflow-y-auto py-5",
        collapsed ? "px-2" : "px-3",
      )}
    >
      <div className="space-y-1">
        {[
          { to: "/app", name: "Home", icon: Home, end: true },
          { to: "/app/organizations", name: "Organizations", icon: Building2, end: false },
          {
            to: "/app/account",
            name: "My account",
            icon: CircleUserRound,
            end: false,
          },
        ].map(({ to, name, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            title={collapsed ? name : undefined}
            aria-label={name}
            className={({ isActive }) =>
              cn(
                "flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                isActive
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            <Icon className="size-[18px]" aria-hidden="true" />
            <span className={collapsed ? "sr-only" : undefined}>{name}</span>
          </NavLink>
        ))}
      </div>
      <div>
        <p
          className={cn(
            "mb-3 px-3 text-[10px] font-semibold tracking-widest text-muted-foreground",
            collapsed && "sr-only",
          )}
        >
          WORKSPACE
        </p>
        <ul className="space-y-1">
          {[
            { name: "Projects", icon: FolderKanban, path: "projects" },
            { name: "Clients", icon: ContactRound, path: "clients" },
            { name: "People", icon: Users, path: "resources" },
            { name: "Teams", icon: UsersRound, path: "teams" },
            { name: "Settings & access", icon: Settings, path: "settings" },
          ].map(({ name, icon: Icon, path }) => (
            <li key={path}><NavLink
              to={orgId ? `/app/o/${orgId}/${path}` : "/app/organizations"}
              onClick={onNavigate}
              aria-label={orgId ? name : `${name} — choose organization`}
              title={collapsed ? name : undefined}
              className={({ isActive }) => cn("flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium", collapsed && "justify-center px-0", orgId && isActive ? "bg-secondary text-secondary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground")}
            ><Icon className="size-[18px] shrink-0" aria-hidden="true" /><span className={collapsed ? "sr-only" : undefined}>{name}</span></NavLink></li>
          ))}
          {[
            { name: "Operations queues", icon: Workflow },
            { name: "Reports", icon: BarChart3 },
          ].map(({ name, icon: Icon }) => <li key={name}>
            <button type="button" disabled aria-label={`${name} — Coming soon`} title={`${name} — Coming soon`}
              className={cn("flex min-h-10 w-full items-center gap-3 rounded-lg px-3 text-left text-sm text-muted-foreground/70", collapsed && "justify-center px-0")}>
              <Icon className="size-[18px] shrink-0" aria-hidden="true" /><span className={collapsed ? "sr-only" : "flex-1"}>{name}</span>{!collapsed && <span className="text-[10px]">Soon</span>}
            </button>
          </li>)}
        </ul>
      </div>
    </nav>
  );
}

export function AppShell() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [error, setError] = useState("");
  const orgId = location.pathname.match(/^\/app\/o\/([^/]+)/)?.[1];
  const moduleName = location.pathname.split("/")[4];
  const workspaceTitle = ({ clients: "Clients", resources: "People", teams: "Teams", projects: "Projects", settings: "Settings & access" } as Record<string, string>)[moduleName];
  const title = workspaceTitle || (
    location.pathname === "/app/account"
      ? "My account"
      : location.pathname === "/app"
        ? "Home"
        : location.pathname.startsWith("/app/o/") || location.pathname === "/app/organizations"
          ? "Organizations"
          : "Page not found");
  const initials = (user?.display_name || "")
    .split(/\s+/)
    .map((word) => word[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  async function handleLogout() {
    setError("");
    setSigningOut(true);
    try {
      await signOut();
      navigate("/login", { replace: true });
    } catch (cause) {
      setError(
        cause instanceof Error && cause.name !== "TypeError"
          ? cause.message
          : "Unable to sign out. Check your connection and try again.",
      );
    } finally {
      setSigningOut(false);
    }
  }
  return (
    <div className="min-h-svh bg-background">
      <a
        href="#main-content"
        className="sr-only z-50 rounded bg-primary p-3 text-primary-foreground focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to content
      </a>
      <aside
        id="desktop-sidebar"
        className={cn(
          "fixed inset-y-0 left-0 hidden flex-col border-r bg-card lg:flex",
          collapsed ? "w-18" : "w-60",
        )}
      >
        <Link
          to="/app"
          aria-label="Kaizora home"
          className={cn(
            "flex h-16 shrink-0 items-center gap-3 border-b text-lg font-semibold tracking-tight",
            collapsed ? "justify-center" : "px-6",
          )}
        >
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Layers className="size-[18px]" aria-hidden="true" />
          </span>
          <span className={collapsed ? "sr-only" : undefined}>Kaizora</span>
        </Link>
        <Navigation collapsed={collapsed} />
        <div className={cn("mt-auto border-t p-5", collapsed && "hidden")}>
          <p className="text-xs font-medium">Your space to work</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Projects and operations,
            <br />
            connected.
          </p>
        </div>
      </aside>
      <div className={cn("flex min-h-svh flex-col", collapsed ? "lg:pl-18" : "lg:pl-60")}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b bg-card px-4 sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  aria-label="Open navigation"
                >
                  <Menu aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 gap-0">
                <SheetHeader className="border-b">
                  <SheetTitle className="flex items-center gap-2">
                    <Layers
                      className="size-5 text-primary"
                      aria-hidden="true"
                    />
                    Kaizora
                  </SheetTitle>
                  <SheetDescription>Workspace navigation</SheetDescription>
                </SheetHeader>
                <Navigation onNavigate={() => setMobileOpen(false)} />
              </SheetContent>
            </Sheet>
            <Button
              variant="ghost"
              size="icon"
              className="hidden lg:inline-flex"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              aria-controls="desktop-sidebar"
              onClick={() => setCollapsed((value) => !value)}
            >
              <PanelLeft aria-hidden="true" />
            </Button>
            <span className="hidden text-sm text-muted-foreground sm:inline">
              Workspace
            </span>
            <span
              className="hidden text-muted-foreground sm:inline"
              aria-hidden="true"
            >
              /
            </span>
            <span className="truncate text-sm font-medium">{title}</span>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <ThemeMenu />
            <div className="mx-1 h-5 border-l" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  aria-label="Account menu"
                  disabled={signingOut}
                  className="h-10 gap-2 px-1 sm:px-2"
                >
                  <Avatar className="size-7">
                    <AvatarFallback className="bg-secondary text-xs text-secondary-foreground">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-32 truncate text-sm sm:inline">
                    {signingOut ? "Signing out…" : user?.display_name}
                  </span>
                  <ChevronDown
                    className="size-3.5 text-muted-foreground"
                    aria-hidden="true"
                  />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <p className="truncate">{user?.display_name}</p>
                  <p className="mt-1 truncate text-xs font-normal text-muted-foreground">
                    @{user?.username}
                  </p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/app/account">
                    <CircleUserRound aria-hidden="true" />
                    My account
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  disabled={signingOut}
                  onSelect={() => {
                    void handleLogout();
                  }}
                >
                  <LogOut aria-hidden="true" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main
          id="main-content"
          tabIndex={-1}
          className="w-full min-w-0 flex-1 space-y-6 px-4 py-7 outline-none sm:px-8 sm:py-10"
        >
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {orgId && <WorkspaceNavigation key={orgId} orgId={orgId} />}
          <Outlet key={user?.id} />
        </main>
        <footer className="flex shrink-0 flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-muted-foreground sm:px-8">
          <span>© {new Date().getFullYear()} Kaizora</span>
          <a href="/user-guide/" className="rounded-sm underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-ring">User guide</a>
        </footer>
      </div>
    </div>
  );
}
