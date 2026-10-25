import { useState, type FormEvent, type ReactNode } from "react";
import { accessApi, type Role, type Member, type Assignment, type Catalog, type Permissions, type RoleInput } from "./access-api";
import type { Organization } from "@/features/organizations/api";
import { useOrganizationRead } from "@/features/organizations/use-organization-read";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return <Card><CardHeader><CardTitle><h2>{title}</h2></CardTitle></CardHeader><CardContent className="space-y-4">{children}</CardContent></Card>;
}

function Pager({ page, previous, next, change }: { page: number; previous: string | null; next: string | null; change: (page: number) => void }) {
  return <div className="flex flex-wrap items-center gap-3"><Button variant="outline" disabled={!previous} onClick={() => change(page - 1)}>Previous</Button><span className="text-sm">Page {page}</span><Button variant="outline" disabled={!next} onClick={() => change(page + 1)}>Next</Button></div>;
}

type Mutation = (action: () => Promise<unknown>) => Promise<void>;

export function OrganizationAccess({ organization, onChanged }: { organization: Organization; onChanged: () => void }) {
  const [pages, setPages] = useState({ members: 1, roles: 1, assignments: 1 });
  return <AccessSnapshot key={`${pages.members}:${pages.roles}:${pages.assignments}`} organization={organization} onChanged={onChanged} pages={pages} setPage={(kind, page) => setPages((value) => ({ ...value, [kind]: page }))} />;
}

function AccessSnapshot({ organization, onChanged, pages, setPage }: {
  organization: Organization; onChanged: () => void;
  pages: { members: number; roles: number; assignments: number };
  setPage: (kind: "members" | "roles" | "assignments", page: number) => void;
}) {
  const org = organization.id;
  const { data, error, retry } = useOrganizationRead(async (signal) => {
    const permissions = await accessApi.permissions(org, signal);
    const can = (key: string) => permissions.permissions.includes(key);
    const [catalog, members, roles, assignments] = await Promise.all([
      accessApi.catalog(org, signal),
      can("memberships.read") ? accessApi.members(org, pages.members, signal) : undefined,
      can("roles.read") ? accessApi.roles(org, pages.roles, signal) : undefined,
      can("roles.read") ? accessApi.assignments(org, pages.assignments, signal) : undefined,
    ]);
    return { permissions, catalog, members, roles, assignments };
  });
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<string>();
  const mutate: Mutation = async (action) => {
    if (pending) return;
    setPending(true); setNotice(undefined);
    try { await action(); onChanged(); }
    catch (failure) {
      setNotice(failure instanceof Error ? failure.message : "Request failed. Refresh to check its outcome before retrying.");
      // Reload authoritative data even when the transport cannot tell whether the write committed.
      retry();
    } finally { setPending(false); }
  };
  if (error) return <Panel title="Organization access"><Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert><Button onClick={retry}>Refresh access</Button></Panel>;
  if (!data) return <p role="status">Loading organization access…</p>;
  const can = (key: string) => data.permissions.permissions.includes(key);
  return <div className="space-y-6" aria-busy={pending}>
    {notice && <Alert variant="destructive"><AlertDescription>{notice}</AlertDescription></Alert>}
    <Panel title="Your access">
      <p className="text-sm text-muted-foreground">{data.permissions.is_owner ? "Owner — reserved organization authority." : "Permissions are checked on every request."} Project-specific actions become available with the projects module.</p>
      <div className="flex flex-wrap gap-2">{data.permissions.permissions.length ? data.permissions.permissions.map((key) => <Badge key={key} variant="secondary">{key}</Badge>) : <p className="text-sm">Basic membership: your account and organization identity only.</p>}</div>
    </Panel>
    <Panel title="Members">
      <p className="text-sm text-muted-foreground">Suspending or ending access preserves history. Reactivation restores any role assignments that have not been revoked.</p>
      {can("memberships.manage") && <AddMember org={org} mutate={mutate} pending={pending} />}
      {!data.members ? <p className="text-sm text-muted-foreground">You do not have permission to view the member directory.</p> : <>
        <div className="space-y-3">{data.members.results.map((member) => <MemberRow key={member.id} member={member} organization={organization} permissions={data.permissions} mutate={mutate} pending={pending} />)}</div>
        {!data.members.count && <p>No members found.</p>}
        <Pager page={pages.members} {...data.members} change={(page) => setPage("members", page)} />
      </>}
    </Panel>
    <Panel title="Roles">
      {can("roles.manage") && <RoleEditor org={org} catalog={data.catalog} permissions={data.permissions} mutate={mutate} pending={pending} />}
      {!data.roles ? <p className="text-sm text-muted-foreground">You do not have permission to view organization roles.</p> : <>
        {!data.roles.count && <p className="text-sm">No custom roles yet. Owners can create one or use a preset.</p>}
        <div className="space-y-3">{data.roles.results.map((role) => <div key={role.id} className="flex flex-wrap items-start justify-between gap-3 rounded-md border p-4">
          <div className="min-w-0 space-y-2"><h3 className="break-words font-medium">{role.name}</h3><div className="flex flex-wrap gap-2"><Badge variant="outline">{role.scope_kind}</Badge><Badge variant="secondary">{role.status}</Badge><span className="text-sm text-muted-foreground">{role.permissions.length} permissions</span></div><p className="break-words text-xs text-muted-foreground">{role.permissions.join(", ") || "Basic membership only"}</p></div>
          {can("roles.manage") && role.permissions.every((key) => can(key)) && <RoleEditor org={org} role={role} catalog={data.catalog} permissions={data.permissions} mutate={mutate} pending={pending} />}
        </div>)}</div>
        <Pager page={pages.roles} {...data.roles} change={(page) => setPage("roles", page)} />
      </>}
    </Panel>
    <Panel title="Role assignments">
      {can("roles.assign") && data.members && data.roles && <AssignRole org={org} members={data.members.results} roles={data.roles.results} mutate={mutate} pending={pending} />}
      {can("roles.assign") && (!data.members || !data.roles) && <p className="text-sm text-muted-foreground">The assignment picker also requires member and role read permissions.</p>}
      <p className="text-sm text-muted-foreground">Revoked assignments stay in history. Project roles cannot be assigned here.</p>
      {data.assignments ? <>
        {!data.assignments.count && <p className="text-sm">No role assignments yet.</p>}
        <div className="space-y-3">{data.assignments.results.map((assignment) => <AssignmentRow key={assignment.id} assignment={assignment} org={org} canRevoke={can("roles.assign")} mutate={mutate} pending={pending} />)}</div>
        <Pager page={pages.assignments} {...data.assignments} change={(page) => setPage("assignments", page)} />
      </> : <p className="text-sm text-muted-foreground">You do not have permission to view assignments.</p>}
    </Panel>
  </div>;
}

function AddMember({ org, mutate, pending }: { org: string; mutate: Mutation; pending: boolean }) {
  const [username, setUsername] = useState("");
  return <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); void mutate(() => accessApi.addMember(org, { username })); }}>
    <div className="min-w-0 flex-1 space-y-2"><Label htmlFor="member-username">Existing account username</Label><Input id="member-username" value={username} onChange={(e) => setUsername(e.target.value)} maxLength={150} required placeholder="Exact username" autoComplete="off" /></div>
    <Button disabled={pending}>Add member</Button>
  </form>;
}

function ActionDialog({ title, description, trigger, pending, action, children }: {
  title: string; description: string; trigger: string; pending: boolean;
  action: (reason: string) => Promise<void>; children?: ReactNode;
}) {
  const [reason, setReason] = useState("");
  return <Dialog><DialogTrigger asChild><Button size="sm" variant="outline" disabled={pending}>{trigger}</Button></DialogTrigger><DialogContent>
    <DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription></DialogHeader>
    <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); void action(reason); }}>
      {children}<div className="space-y-2"><Label htmlFor="change-reason">Reason</Label><Input id="change-reason" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} required /></div>
      <Button disabled={pending}>{pending ? "Saving…" : "Confirm change"}</Button>
    </form>
  </DialogContent></Dialog>;
}

function MemberRow({ member, organization, permissions, mutate, pending }: { member: Member; organization: Organization; permissions: Permissions; mutate: Mutation; pending: boolean }) {
  const canManage = permissions.permissions.includes("memberships.manage") && (!member.is_owner || permissions.is_owner);
  return <div className="space-y-3 rounded-md border p-4">
    <div className="flex flex-wrap items-center gap-2"><h3 className="break-words font-medium">{member.display_name || member.username}</h3><span className="text-sm text-muted-foreground">@{member.username}</span><Badge variant="secondary">{member.status}</Badge>{member.is_owner && <Badge>Owner</Badge>}</div>
    
    <div className="flex flex-wrap gap-2">
      {canManage && (["active", "suspended", "ended"] as const).filter((status) => status !== member.status).map((status) => <ActionDialog key={status} title={`Set ${member.username} to ${status}`} trigger={status === "active" ? "Reactivate" : status === "suspended" ? "Suspend" : "End membership"} description="Access changes immediately after saving. Historical records are retained." pending={pending} action={(reason) => mutate(() => accessApi.changeMember(organization.id, member.id, { status, version: member.version, reason }))} />)}
      {permissions.is_owner && member.status === "active" && member.id !== permissions.membership_id && <ActionDialog title={`Transfer ownership to ${member.username}`} trigger="Transfer ownership" description="You will stop being an owner. Your remaining access will depend on your assigned roles." pending={pending} action={(reason) => mutate(() => accessApi.transferOwner(organization.id, { target_membership_id: member.id, version: organization.version, reason }))} />}
    </div>
  </div>;
}

function RoleEditor({ org, role, catalog, permissions, mutate, pending }: { org: string; role?: Role; catalog: Catalog; permissions: Permissions; mutate: Mutation; pending: boolean }) {
  const [name, setName] = useState(role?.name ?? "");
  const [scope, setScope] = useState<RoleInput["scope_kind"]>(role?.scope_kind ?? "organization");
  const [keys, setKeys] = useState<string[]>(role?.permissions ?? []);
  const [status, setStatus] = useState(role?.status ?? "active");
  const [reason, setReason] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    void mutate(() => role ? accessApi.updateRole(org, role.id, { name, permissions: keys, status, reason, version: role.version }) : accessApi.createRole(org, { name, permissions: keys, scope_kind: scope }));
  };
  return <Dialog><DialogTrigger asChild><Button variant={role ? "outline" : "default"} size="sm" disabled={pending}>{role ? `Edit ${role.name}` : "Create role"}</Button></DialogTrigger>
    <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl"><DialogHeader><DialogTitle>{role ? "Edit role" : "Create role"}</DialogTitle><DialogDescription>Changes affect every current assignment. You can delegate only permissions you hold. Ownership is reserved.</DialogDescription></DialogHeader>
      <form className="space-y-4" onSubmit={submit}>
        {!role && <div className="space-y-2"><Label>Start from a preset (optional)</Label><Select onValueChange={(value) => { const preset = catalog.presets.find((item) => item.name === value); if (preset) { setName(preset.name); setScope(preset.scope_kind); setKeys(preset.permissions); } }}><SelectTrigger aria-label="Role preset"><SelectValue placeholder="Choose a preset" /></SelectTrigger><SelectContent>{catalog.presets.filter((preset) => preset.permissions.every((key) => permissions.permissions.includes(key))).map((preset) => <SelectItem key={preset.name} value={preset.name}>{preset.name}</SelectItem>)}</SelectContent></Select></div>}
        <div className="space-y-2"><Label htmlFor="role-name">Role name</Label><Input id="role-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={200} required /></div>
        <div className="space-y-2"><Label>Scope</Label><Select value={scope} disabled={!!role} onValueChange={(value: "organization" | "project") => { setScope(value); setKeys([]); }}><SelectTrigger aria-label="Role scope"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="organization">Organization</SelectItem><SelectItem value="project">Project (assign later in project settings)</SelectItem></SelectContent></Select></div>
        <fieldset className="space-y-3"><legend className="mb-3 text-sm font-medium">Permissions</legend><div className="grid gap-3 sm:grid-cols-2">{catalog.entries.filter((entry) => scope === "organization" || entry.scope === "project").map((entry) => <Label key={entry.key} className="flex items-start gap-2 break-all"><Checkbox checked={keys.includes(entry.key)} disabled={!permissions.permissions.includes(entry.key)} onCheckedChange={(checked) => setKeys((current) => checked ? [...current, entry.key] : current.filter((key) => key !== entry.key))} /><span>{entry.key}</span></Label>)}</div></fieldset>
        {role && <><div className="space-y-2"><Label>Status</Label><Select value={status} onValueChange={(value: "active" | "archived") => setStatus(value)}><SelectTrigger aria-label="Role status"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Active</SelectItem><SelectItem value="archived">Archived — grants give no access</SelectItem></SelectContent></Select></div><div className="space-y-2"><Label htmlFor="role-reason">Reason</Label><Input id="role-reason" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} required /></div></>}
        <Button disabled={pending}>{pending ? "Saving…" : "Save role"}</Button>
      </form>
    </DialogContent>
  </Dialog>;
}

function AssignRole({ org, members, roles, mutate, pending }: { org: string; members: Member[]; roles: Role[]; mutate: Mutation; pending: boolean }) {
  const [memberId, setMemberId] = useState("");
  const [roleId, setRoleId] = useState("");
  return <ActionDialog title="Assign organization role" trigger="Assign role" description="Select from the current Members and Roles pages. Change their page first if the person or role is not listed." pending={pending} action={(reason) => mutate(() => accessApi.assign(org, { membership_id: memberId, role_id: roleId, reason }))}>
    <div className="space-y-2"><Label htmlFor="assign-member">Member</Label><Select value={memberId} onValueChange={setMemberId} required><SelectTrigger id="assign-member"><SelectValue placeholder="Choose a member" /></SelectTrigger><SelectContent>{members.filter((member) => member.status === "active").map((member) => <SelectItem key={member.id} value={member.id}>{member.display_name || member.username}</SelectItem>)}</SelectContent></Select></div>
    <div className="space-y-2"><Label htmlFor="assign-role">Role</Label><Select value={roleId} onValueChange={setRoleId} required><SelectTrigger id="assign-role"><SelectValue placeholder="Choose a role" /></SelectTrigger><SelectContent>{roles.filter((role) => role.status === "active" && role.scope_kind === "organization").map((role) => <SelectItem key={role.id} value={role.id}>{role.name}</SelectItem>)}</SelectContent></Select></div>
  </ActionDialog>;
}

function AssignmentRow({ org, assignment, canRevoke, mutate, pending }: { org: string; assignment: Assignment; canRevoke: boolean; mutate: Mutation; pending: boolean }) {
  return <div className="flex flex-wrap items-start justify-between gap-3 rounded-md border p-4"><div className="min-w-0 space-y-2"><h3 className="break-words font-medium">{assignment.role_name}</h3><p className="break-all text-xs text-muted-foreground">Member: {assignment.membership_id}</p><p className="text-xs text-muted-foreground">Assigned {new Date(assignment.started_at).toLocaleString()}</p><Badge variant="secondary">{assignment.ended_at ? `Revoked ${new Date(assignment.ended_at).toLocaleString()}` : "Live assignment"}</Badge></div>
    {canRevoke && !assignment.ended_at && <ActionDialog title={`Revoke ${assignment.role_name}`} trigger="Revoke" description="This grant stops giving access immediately. Other active roles may still grant the same permissions." pending={pending} action={(reason) => mutate(() => accessApi.revoke(org, assignment.id, { version: assignment.version, reason }))} />}
  </div>;
}
