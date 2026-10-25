import { useState } from "react";
import { useOrganizationRead } from "./use-organization-read";
import { OrganizationAccess } from "@/features/identity/organization-access";
import { Link, useNavigate, useParams } from "react-router";
import { Building2 } from "lucide-react";
import { organizationsApi, type Organization, type OrganizationPage } from "./api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CreateOrganization } from "./create-organization";
import { Badge } from "@/components/ui/badge";

function ReadError({ message, retry }: { message: string; retry: () => void }) {
  return <Alert variant="destructive"><AlertDescription className="flex flex-wrap items-center gap-3">
    <span>{message}</span><Button variant="outline" size="sm" onClick={retry}>Retry</Button>
  </AlertDescription></Alert>;
}

function OrganizationChoices({ page, changePage }: { page: number; changePage: (page: number) => void }) {
  const navigate = useNavigate();
  const { data, error, retry } = useOrganizationRead<OrganizationPage>(
    (signal) => organizationsApi.list(page, signal),
  );
  if (error) return <ReadError message={error} retry={retry} />;
  if (!data) return <p role="status">Loading organizations…</p>;
  if (!data.count) return <Card><CardHeader><CardTitle><h2>No organization access yet</h2></CardTitle></CardHeader>
    <CardContent className="space-y-3 text-sm text-muted-foreground">
      <p>An operator needs to provision your organization membership. Your account remains available.</p>
      <Button variant="outline" asChild><Link to="/app/account">My account</Link></Button>
    </CardContent></Card>;
  return <div className="space-y-4">
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {data.results.map((org) => <Card key={org.id}>
        <CardHeader><CardTitle className="flex min-w-0 items-center gap-2"><Building2 className="size-5 shrink-0" aria-hidden="true" /><span className="break-words">{org.name}</span></CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{org.timezone}</p>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Badge variant="secondary">{org.is_owner ? "Owner" : "Member"}</Badge>
            <Button onClick={() => navigate(`/app/o/${org.id}/settings`)} aria-label={`Open ${org.name}`}>Open organization</Button>
          </div>
        </CardContent>
      </Card>)}
    </div>
    <div className="flex items-center gap-3">
      <Button variant="outline" disabled={!data.previous} onClick={() => changePage(page - 1)}>Previous</Button>
      <span className="text-sm">Page {page}</span>
      <Button variant="outline" disabled={!data.next} onClick={() => changePage(page + 1)}>Next</Button>
    </div>
  </div>;
}

export function OrganizationsPage() {
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  return <section className="space-y-6">
    <div><h1 className="text-2xl font-semibold tracking-tight">Your organizations</h1>
      <p className="mt-2 text-sm text-muted-foreground">Choose an organization to open its workspace.</p></div>
    <CreateOrganization onCreated={() => { setPage(1); setRevision((value) => value + 1); }} />
    <OrganizationChoices key={`${page}:${revision}`} page={page} changePage={setPage} />
  </section>;
}

function OrganizationSettings({ orgId }: { orgId: string }) {
  const { data, error, retry } = useOrganizationRead<Organization>(
    (signal) => organizationsApi.get(orgId, signal),
  );
  if (error) return <section className="space-y-4"><h1 className="text-2xl font-semibold">Organization unavailable</h1>
    <ReadError message={error} retry={retry} /><Button variant="outline" asChild><Link to="/app/organizations">Choose another organization</Link></Button></section>;
  if (!data) return <p role="status">Loading organization…</p>;
  return <section className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="break-words text-2xl font-semibold tracking-tight">{data.name}</h1>
    </div>
    <Card><CardHeader><CardTitle><h2>Organization settings</h2></CardTitle></CardHeader>
      <CardContent><dl className="grid gap-5 text-sm sm:grid-cols-3">
        <div><dt className="text-muted-foreground">Timezone</dt><dd className="mt-1">{data.timezone}</dd></div>
        <div><dt className="text-muted-foreground">Status</dt><dd className="mt-1 capitalize">{data.status}</dd></div>
        <div><dt className="text-muted-foreground">Your membership</dt><dd className="mt-1">{data.is_owner ? "Owner" : "Member"}</dd></div>
      </dl></CardContent></Card>
    <OrganizationAccess organization={data} onChanged={retry} />
  </section>;
}

export function OrganizationPage() {
  const { orgId } = useParams();
  return orgId ? <OrganizationSettings key={orgId} orgId={orgId} /> : null;
}
