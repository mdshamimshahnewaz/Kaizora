import { Link } from "react-router";
import { ArrowUpRight, FolderKanban, Users, ContactRound } from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function HomePage() {
  const { user } = useAuth();
  return (
    <>
      <div>
        <p className="mb-2 text-xs font-medium tracking-widest text-teal-foreground">
          YOUR WORKSPACE
        </p>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          Welcome, {user?.display_name}.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Manage your clients, people and projects in one organization workspace.
        </p>
      </div>
      <section className="relative overflow-hidden rounded-xl border bg-card p-6 sm:p-10">
        <div className="max-w-xl">
          <Badge variant="secondary" className="mb-5">
            Getting started
          </Badge>
          <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
            Choose your organization to get started.
          </h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Start with clients and people, organize your teams, then create delivery
            projects or operations engagements with the right access.
          </p>
          <Button asChild variant="outline" className="mt-6">
            <Link to="/app/organizations">
              Open organizations
              <ArrowUpRight aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </section>
      <section
        aria-label="Workspace foundations"
        className="grid gap-4 md:grid-cols-3"
      >
        {[
          {
            title: "Projects",
            body: "Create projects, choose a manager and control access and lifecycle.",
            icon: FolderKanban,
          },
          {
            title: "Clients",
            body: "Keep customer records and business contacts in one place.",
            icon: ContactRound,
          },
          {
            title: "People & teams",
            body: "Maintain people and dated team memberships, with or without a login.",
            icon: Users,
          },
        ].map(({ title, body, icon: Icon }) => (
          <article key={title} className="rounded-lg border bg-card p-5">
            <Icon
              className="mb-5 size-5 text-muted-foreground"
              aria-hidden="true"
            />
            <h2 className="text-sm font-semibold">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {body}
            </p>
            <Link to="/app/organizations" className="mt-5 inline-block text-sm font-medium text-primary hover:underline">Choose organization</Link>
          </article>
        ))}
      </section>
    </>
  );
}

export { AccountPage } from "@/features/account/account-page";
