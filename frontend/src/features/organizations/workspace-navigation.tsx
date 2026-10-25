import { Link, NavLink } from "react-router";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { organizationsApi } from "./api";
import { useOrganizationRead } from "./use-organization-read";

export const workspaceDestinations = [
  { path: "projects", label: "Projects" },
  { path: "clients", label: "Clients" },
  { path: "resources", label: "People" },
  { path: "teams", label: "Teams" },
  { path: "settings", label: "Settings & access" },
];

export function WorkspaceNavigation({ orgId }: { orgId: string }) {
  const { data, error } = useOrganizationRead((signal) => organizationsApi.get(orgId, signal));
  return <div className="space-y-3"><div className="flex flex-wrap items-center justify-between gap-2">
    <p className="min-w-0 break-words text-sm font-medium">{data?.name || (error ? "Organization unavailable" : "Loading organization…")}</p>
    <Button variant="ghost" size="sm" asChild><Link to="/app/organizations">Switch organization</Link></Button>
  </div><nav aria-label="Organization workspace" className="flex flex-wrap gap-2 border-b pb-3">
    {workspaceDestinations.map(({ path, label }) => <NavLink key={path}
      to={`/app/o/${orgId}/${path}`}
      className={({ isActive }) => cn("rounded-md px-3 py-2 text-sm font-medium hover:bg-muted", isActive ? "bg-secondary text-secondary-foreground" : "text-muted-foreground")}
    >{label}</NavLink>)}
  </nav></div>;
}
