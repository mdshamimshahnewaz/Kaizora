import { useState } from "react";
import { useOptionalAccount } from "@/features/account/account-provider";
import { Link, useParams } from "react-router";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { accessApi } from "@/features/identity/access-api";
import { organizationsApi } from "@/features/organizations/api";
import { EntityDialog, Pagination, ReadError, TextField, useWorkspaceRead } from "@/features/workspace/components";
import { resourcesApi, type Person, type Team, type IdentityLink, type TeamMembership } from "./api";

import { SearchablePicker, type Choice } from "@/features/workspace/searchable-picker";

type Kind = "resources" | "teams";
function nameOf(item: Person | Team) { return "display_name" in item ? item.display_name : item.name; }
function businessToday(timezone: string) {
  const parts = new Intl.DateTimeFormat("en", { timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
  return ["year", "month", "day"].map((type) => parts.find((part) => part.type === type)?.value).join("-");
}
function StatusSelect({ value, onChange, kind }: { value: string; onChange: (value: string) => void; kind: Kind }) {
  const ended = kind === "resources" ? "retired" : "archived";
  return <Select value={value} onValueChange={onChange}><SelectTrigger aria-label="Status" className="w-44"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Active</SelectItem><SelectItem value={ended}>{kind === "resources" ? "Retired" : "Archived"}</SelectItem><SelectItem value="all">All statuses</SelectItem></SelectContent></Select>;
}
function RecordEditor({ org, kind, record, statusOnly = false, refresh, close }: { org: string; kind: Kind; record?: Person | Team; statusOnly?: boolean; refresh: () => void; close: () => void }) {
  const [name, setName] = useState(record ? nameOf(record) : "");
  const [code, setCode] = useState("");
  const [reason, setReason] = useState("");
  const [version, setVersion] = useState(record?.version ?? 1);
  const person = kind === "resources";
  const label = person ? "person" : "team";
  const status = record?.status === "active" ? person ? "retired" : "archived" : "active";
  const action = !record ? "Create" : statusOnly ? status === "active" ? "Reactivate" : person ? "Retire" : "Archive" : "Edit";
  return <EntityDialog title={`${action} ${label}`} description={person ? "People are stable work identities. Creating a person does not create a login; retiring preserves history and existing team intervals." : "Teams organize people without granting application access. Archiving preserves membership history and prevents new assignments."} allowConflictRetry={!record} onClose={close} onRefresh={refresh} saveLabel={`${action} ${label}`} reviewConflict={record ? async () => { const latest = person ? await resourcesApi.person(org, record.id) : await resourcesApi.team(org, record.id); setVersion(latest.version); return `Latest: ${nameOf(latest)} (${latest.status}), version ${latest.version}.`; } : undefined} onSave={() => {
    if (!record) return person ? resourcesApi.createResource(org, { code, display_name: name }) : resourcesApi.createTeam(org, { code, name });
    return person ? resourcesApi.updateResource(org, record.id, { version, reason, ...(statusOnly ? { status: status as "active" | "retired" } : { display_name: name }) }) : resourcesApi.updateTeam(org, record.id, { version, reason, ...(statusOnly ? { status: status as "active" | "archived" } : { name }) });
  }}>
    {!record && <TextField label={`${person ? "Person" : "Team"} code`} value={code} onChange={setCode} maxLength={32} required={!person} hint={person ? "Optional; generated automatically if blank. Cannot change later." : "Unique within the organization; cannot change later."} />}
    {!statusOnly && <TextField label={`${person ? "Display" : "Team"} name`} value={name} onChange={setName} required />}
    {record && <TextField label="Reason for change" value={reason} onChange={setReason} maxLength={500} required />}
  </EntityDialog>;
}
function Results({ org, kind, page, search, status, changePage }: { org: string; kind: Kind; page: number; search: string; status: string; changePage: (page: number) => void }) {
  const read = useWorkspaceRead<{ count: number; next: string | null; previous: string | null; results: (Person | Team)[] }>((signal) => kind === "resources" ? resourcesApi.resources(org, page, search, status, signal) : resourcesApi.teams(org, page, search, status, signal));
  if (read.error && !read.data) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status">Loading {kind === "resources" ? "people" : "teams"}…</p>;
  return <div className="space-y-4">{read.error && <ReadError message={read.error} retry={read.refresh} />}{read.data.count ? <Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Code</TableHead><TableHead>Status</TableHead>{kind === "resources" && <TableHead>Login</TableHead>}</TableRow></TableHeader><TableBody>{read.data.results.map((item) => <TableRow key={item.id}><TableCell><Link className="font-medium text-primary hover:underline" to={`/app/o/${org}/${kind}/${item.id}`}>{nameOf(item)}</Link></TableCell><TableCell>{item.code}</TableCell><TableCell><Badge variant="secondary">{item.status}</Badge></TableCell>{"linked_membership_id" in item && <TableCell>{item.linked_membership_id ? "Linked login" : "No linked login"}</TableCell>}</TableRow>)}</TableBody></Table> : <p className="rounded-md border p-6 text-sm text-muted-foreground">No {kind === "resources" ? "people" : "teams"} match this view. Create a record or change your filters.</p>}<Pagination {...read.data} page={page} change={changePage} /></div>;
}
function ListWorkspace({ org, kind }: { org: string; kind: Kind }) {
  const permissions = useWorkspaceRead((signal) => accessApi.permissions(org, signal));
  const [search, setSearch] = useState(""); const [query, setQuery] = useState("");
  const [status, setStatus] = useState("active"); const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0); const [creating, setCreating] = useState(false); const [addingMember, setAddingMember] = useState(false);
  const can = (key: string) => !permissions.denied && !!permissions.data?.permissions.includes(key);
  const label = kind === "resources" ? "People" : "Teams";
  return <section className="space-y-6"><header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-semibold">{label}</h1><p className="mt-2 text-sm text-muted-foreground">{kind === "resources" ? "Existing members can be selected directly in teams and projects. Create a person only for a worker without a login." : "Organize people with dated memberships. Teams do not grant access."}</p></div>{can(`${kind}.manage`) && <Button onClick={() => setCreating(true)}><Plus aria-hidden />Create {kind === "resources" ? "person" : "team"}</Button>}{kind === "resources" && can("resources.manage") && can("resources.link_identity") && can("memberships.read") && <Button variant="outline" onClick={() => setAddingMember(true)}>Add existing member</Button>}</header>
    {addingMember && can("resources.manage") && can("resources.link_identity") && can("memberships.read") && <MemberResourceEditor org={org} close={() => setAddingMember(false)} refresh={() => setRevision(v => v + 1)} />}
    {permissions.error ? <ReadError message={permissions.error} retry={permissions.refresh} /> : !permissions.data ? <p role="status">Checking access…</p> : !can(`${kind}.read`) ? <p>You do not have permission to view {label.toLowerCase()}. Ask your organization owner for access.</p> : <>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); }}><div className="min-w-48 flex-1"><TextField label={`Search ${label.toLowerCase()}`} value={search} onChange={setSearch} maxLength={100} /></div><Button variant="outline">Search</Button><StatusSelect kind={kind} value={status} onChange={(value) => { setStatus(value); setPage(1); }} /></form>
      <Results key={`${query}:${status}:${page}:${revision}`} org={org} kind={kind} search={query} status={status === "all" ? "" : status} page={page} changePage={setPage} />
    </>}{creating && can(`${kind}.manage`) && <RecordEditor org={org} kind={kind} close={() => setCreating(false)} refresh={() => { setRevision((v) => v + 1); setPage(1); permissions.refresh(); }} />}</section>;
}
function MemberPicker({ org, value, change }: { org: string; value: string; change: (value: string) => void }) {
  const [choice, setChoice] = useState<Choice | null>(null);
  return <SearchablePicker label="Organization member" value={choice?.id === value ? choice : null} onChange={item => { setChoice(item); change(item?.id || ""); }} load={(search, page, signal) => resourcesApi.choices(org, "members", search, page, signal)} />;
}
function MemberResourceEditor({ org, close, refresh }: { org: string; close: () => void; refresh: () => void }) {
  const [member, setMember] = useState("");
  return <EntityDialog title="Add existing member" description="Choose a member once. Their work identity is reused or created automatically; no new account or permissions are created." onClose={close} onRefresh={refresh} saveLabel="Add member as resource" onSave={() => { if (!member) throw new Error("Choose an organization member."); return resourcesApi.fromMember(org, member); }}><MemberPicker org={org} value={member} change={setMember} /></EntityDialog>;
}
function LinkEditor({ org, person, link, close, refresh }: { org: string; person: Person; link?: IdentityLink; close: () => void; refresh: () => void }) {
  const [membership, setMembership] = useState(""); const [reason, setReason] = useState(""); const [version, setVersion] = useState(person.version);
  return <EntityDialog title={link ? "End login link" : "Link existing login"} description="A link connects this person to an existing organization member. It does not create an account or grant roles. Ending a link preserves earlier history." onClose={close} onRefresh={refresh} reviewConflict={async () => { const latest = await resourcesApi.person(org, person.id); setVersion(latest.version); return `Latest: ${latest.display_name}, ${latest.linked_membership_id ? "has a linked login" : "no linked login"}, version ${latest.version}.`; }} onSave={async () => { if (!link && !membership) throw Object.assign(new Error("Choose an organization member."), { status: 400 }); return link ? resourcesApi.unlink(org, person.id, link.id, { reason, version }) : resourcesApi.link(org, person.id, { membership_id: membership, reason, version }); }} saveLabel={link ? "End link now" : "Link login"}>
    {!link && <MemberPicker org={org} value={membership} change={setMembership} />}<TextField label="Reason" value={reason} onChange={setReason} maxLength={500} required />
  </EntityDialog>;
}
function LinkHistory({ org, person, canLink, refreshPerson }: { org: string; person: Person; canLink: boolean; refreshPerson: () => void }) {
  const [page, setPage] = useState(1);
  return <LinkHistoryPage key={page} org={org} person={person} canLink={canLink} page={page} changePage={setPage} refreshPerson={refreshPerson} />;
}
function LinkHistoryPage({ org, person, canLink, page, changePage, refreshPerson }: { org: string; person: Person; canLink: boolean; page: number; changePage: (page: number) => void; refreshPerson: () => void }) {
  const read = useWorkspaceRead((signal) => resourcesApi.links(org, person.id, page, signal));
  const account = useOptionalAccount()?.account;
  const organization = useWorkspaceRead((signal) => organizationsApi.get(org, signal));
  const timeZone = account?.preferences.timezone || organization.data?.timezone || account?.effective_timezone;
  const timestamp = (value: string) => new Date(value).toLocaleString(undefined, { timeZone });
  const [ending, setEnding] = useState<IdentityLink>();
  if (read.error && !read.data) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status">Loading login history…</p>;
  return <div className="space-y-4">{read.error && <ReadError message={read.error} retry={read.refresh} />}<h2 className="text-lg font-semibold">Login link history</h2>{read.data.count ? <Table><TableHeader><TableRow><TableHead>Linked since</TableHead><TableHead>Ended</TableHead><TableHead>Reason</TableHead><TableHead>Action</TableHead></TableRow></TableHeader><TableBody>{read.data.results.map((link) => <TableRow key={link.id}><TableCell>{timestamp(link.started_at)}</TableCell><TableCell>{link.ended_at ? timestamp(link.ended_at) : "Current login link"}</TableCell><TableCell>{link.reason}</TableCell><TableCell>{canLink && !link.ended_at && <Button variant="outline" size="sm" onClick={() => setEnding(link)}>End link</Button>}</TableCell></TableRow>)}</TableBody></Table> : <p>No login links yet. This person can still be assigned to teams.</p>}<Pagination {...read.data} page={page} change={changePage} />{ending && canLink && <LinkEditor org={org} person={person} link={ending} close={() => setEnding(undefined)} refresh={() => { read.refresh(); refreshPerson(); }} />}</div>;
}
function PersonWorkspace({ org, id }: { org: string; id: string }) {
  const read = useWorkspaceRead((signal) => resourcesApi.person(org, id, signal));
  const permissions = useWorkspaceRead((signal) => accessApi.permissions(org, signal));
  const [editor, setEditor] = useState<"edit" | "status" | "link">();
  const [historyRevision, setHistoryRevision] = useState(0);
  const refresh = () => { read.refresh(); setHistoryRevision((value) => value + 1); };
  if ((read.error && !read.data) || (permissions.error && !permissions.data)) return <ReadError message={read.error || permissions.error || "Unable to load."} retry={() => { read.refresh(); permissions.refresh(); }} />;
  if (!read.data || !permissions.data) return <p role="status">Loading person…</p>;
  const person = read.data; const can = (key: string) => permissions.data!.permissions.includes(key);
  return <section className="space-y-6">{(read.error || permissions.error) && <ReadError message={read.error || permissions.error || "Unable to refresh."} retry={() => { read.refresh(); permissions.refresh(); }} />}<Link className="text-sm text-primary hover:underline" to={`/app/o/${org}/resources`}>Back to People</Link><header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-semibold">{person.display_name}</h1><p className="mt-2 text-sm text-muted-foreground">{person.code} · {person.status} · {person.linked_membership_id ? "Linked login" : "No linked login"}</p></div><div className="flex flex-wrap gap-2">{can("resources.manage") && <><Button variant="outline" onClick={() => setEditor("edit")}>Edit person</Button><Button variant="outline" onClick={() => setEditor("status")}>{person.status === "active" ? "Retire person" : "Reactivate person"}</Button></>}{can("resources.link_identity") && can("memberships.read") && !person.linked_membership_id && person.status === "active" && <Button onClick={() => setEditor("link")}>Link login</Button>}</div></header>
    <p className="text-sm text-muted-foreground">Retirement preserves this identity, login history and team assignments. Existing team intervals remain until explicitly ended.</p>
    {can("resources.link_identity") && !can("memberships.read") && <p className="text-sm">Membership read access is needed to choose a login to link.</p>}
    <LinkHistory key={historyRevision} org={org} person={person} canLink={can("resources.link_identity")} refreshPerson={read.refresh} />
    {editor === "link" && can("resources.link_identity") && can("memberships.read") ? <LinkEditor org={org} person={person} close={() => setEditor(undefined)} refresh={refresh} /> : editor && editor !== "link" && can("resources.manage") && <RecordEditor org={org} kind="resources" record={person} statusOnly={editor === "status"} close={() => setEditor(undefined)} refresh={refresh} />}
  </section>;
}
export function WorkerPicker({ org, value, change, allowMembers = true }: { org: string; value: { kind: "members" | "resources"; choice: Choice | null }; change: (value: { kind: "members" | "resources"; choice: Choice | null }) => void; allowMembers?: boolean }) {
  return <div className="space-y-3"><Select value={value.kind} onValueChange={(kind: "members" | "resources") => change({ kind, choice: null })}><SelectTrigger aria-label="Worker source"><SelectValue /></SelectTrigger><SelectContent>{allowMembers && <SelectItem value="members">Existing member</SelectItem>}<SelectItem value="resources">Existing resource / no-login worker</SelectItem></SelectContent></Select><SearchablePicker key={value.kind} label={value.kind === "members" ? "Organization member" : "Resource"} value={value.choice} onChange={choice => change({ ...value, choice })} load={(search, page, signal) => resourcesApi.choices(org, value.kind, search, page, signal)} /></div>;
}
function AssignmentEditor({ org, team, assignment, timezone, close, refresh, allowMembers = true }: { org: string; team: Team; assignment?: TeamMembership; timezone: string; close: () => void; refresh: () => void; allowMembers?: boolean }) {
  const [worker, setWorker] = useState<{ kind: "members" | "resources"; choice: Choice | null }>({ kind: allowMembers ? "members" : "resources", choice: null }); const [start, setStart] = useState(businessToday(timezone)); const [end, setEnd] = useState(assignment?.end_date ?? "");
  const [reason, setReason] = useState(""); const [version, setVersion] = useState(assignment?.version ?? 1);
  return <EntityDialog title={assignment ? `End membership: ${assignment.resource_name}` : "Add person to team"} description={`Dates use ${timezone}. Start is inclusive; end is exclusive (the person is no longer in the team on that date). Only today or future changes are allowed. Multiple teams are supported; membership grants no access.`} allowConflictRetry={!assignment} onClose={close} onRefresh={refresh} saveLabel={assignment ? "Save end date" : "Add to team"} reviewConflict={assignment ? async () => {
    let page = 1;
    while (true) { const data = await resourcesApi.assignments(org, team.id, page, ""); const current = data.results.find((row) => row.id === assignment.id); if (current) { setVersion(current.version); return `Latest interval: ${current.start_date} through ${current.end_date || "ongoing"} (exclusive), version ${current.version}.`; } if (!data.next) throw new Error("Membership unavailable. Close this form and refresh history."); page += 1; }
  } : undefined} onSave={async () => { if (assignment) return resourcesApi.end(org, team.id, assignment.id, { end_date: end, reason, version }); if (!worker.choice) throw Object.assign(new Error("Choose a member or resource."), { status: 400 }); return resourcesApi.assign(org, team.id, { ...(worker.kind === "members" ? { membership_id: worker.choice.id } : { resource_id: worker.choice.id }), start_date: start, end_date: end || null }); }}>
    {!assignment && <><WorkerPicker org={org} value={worker} change={setWorker} allowMembers={allowMembers} /><TextField label="Start date (inclusive)" type="date" value={start} onChange={setStart} required /></>}
    {assignment && <p className="text-sm">Starts {assignment.start_date}. This date cannot be rewritten.</p>}
    <TextField label="End date (exclusive)" type="date" value={end} onChange={setEnd} required={!!assignment} hint={assignment ? "Must be after the start date." : "Leave blank for an ongoing membership."} />
    {assignment && <TextField label="Reason" value={reason} onChange={setReason} maxLength={500} required />}
  </EntityDialog>;
}
function TeamHistory({ org, team, canManage, timezone }: { org: string; team: Team; canManage: boolean; timezone: string }) {
  const [asOf, setAsOf] = useState(businessToday(timezone)); const [page, setPage] = useState(1);
  return <div className="space-y-4"><h2 className="text-lg font-semibold">Team memberships</h2><div className="flex flex-wrap items-end gap-3"><TextField label="As of date" value={asOf} onChange={(date) => { setAsOf(date); setPage(1); }} type="date" hint="Clear the date to show all history, including future intervals." /><Button variant="outline" onClick={() => { setAsOf(""); setPage(1); }}>All history</Button><Button variant="outline" onClick={() => { setAsOf(businessToday(timezone)); setPage(1); }}>Today</Button></div><TeamHistoryPage key={`${asOf}:${page}`} org={org} team={team} page={page} changePage={setPage} asOf={asOf} timezone={timezone} canManage={canManage} /></div>;
}
function TeamHistoryPage({ org, team, page, changePage, asOf, timezone, canManage }: { org: string; team: Team; page: number; changePage: (page: number) => void; asOf: string; timezone: string; canManage: boolean }) {
  const read = useWorkspaceRead((signal) => resourcesApi.assignments(org, team.id, page, asOf, signal)); const [ending, setEnding] = useState<TeamMembership>();
  if (read.error && !read.data) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status">Loading team memberships…</p>;
  return <div className="space-y-4">{read.error && <ReadError message={read.error} retry={read.refresh} />}{read.data.count ? <Table><TableHeader><TableRow><TableHead>Person</TableHead><TableHead>Starts (inclusive)</TableHead><TableHead>Ends (exclusive)</TableHead><TableHead>Action</TableHead></TableRow></TableHeader><TableBody>{read.data.results.map((item) => <TableRow key={item.id}><TableCell>{item.resource_name}{item.resource_status === "retired" && <Badge variant="secondary" className="ml-2">Retired person</Badge>}</TableCell><TableCell>{item.start_date}</TableCell><TableCell>{item.end_date || "Ongoing"}</TableCell><TableCell>{canManage && (!item.end_date || item.end_date > businessToday(timezone)) && <Button size="sm" variant="outline" onClick={() => setEnding(item)}>Set end date</Button>}</TableCell></TableRow>)}</TableBody></Table> : <p>No team memberships {asOf ? "on this date" : "in history"}. Future assignments appear on their start date or in All history.</p>}<Pagination {...read.data} page={page} change={changePage} />{ending && canManage && <AssignmentEditor org={org} team={team} assignment={ending} timezone={timezone} close={() => setEnding(undefined)} refresh={read.refresh} />}</div>;
}
function TeamWorkspace({ org, id }: { org: string; id: string }) {
  const read = useWorkspaceRead((signal) => resourcesApi.team(org, id, signal)); const permissions = useWorkspaceRead((signal) => accessApi.permissions(org, signal)); const organization = useWorkspaceRead((signal) => organizationsApi.get(org, signal));
  const [editor, setEditor] = useState<"edit" | "status" | "assign">(); const [revision, setRevision] = useState(0);
  if ((read.error && !read.data) || (permissions.error && !permissions.data) || (organization.error && !organization.data)) return <ReadError message={read.error || permissions.error || organization.error || "Unable to load."} retry={() => { read.refresh(); permissions.refresh(); organization.refresh(); }} />;
  if (!read.data || !permissions.data || !organization.data) return <p role="status">Loading team…</p>;
  const team = read.data; const can = (key: string) => permissions.data!.permissions.includes(key); const refresh = () => { read.refresh(); setRevision((v) => v + 1); };
  return <section className="space-y-6">{(read.error || permissions.error) && <ReadError message={read.error || permissions.error || "Unable to refresh."} retry={() => { read.refresh(); permissions.refresh(); }} />}<Link className="text-sm text-primary hover:underline" to={`/app/o/${org}/teams`}>Back to Teams</Link><header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-semibold">{team.name}</h1><p className="mt-2 text-sm text-muted-foreground">{team.code} · {team.status}</p></div>{can("teams.manage") && <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => setEditor("edit")}>Edit team</Button><Button variant="outline" onClick={() => setEditor("status")}>{team.status === "active" ? "Archive team" : "Reactivate team"}</Button>{team.status === "active" && can("resources.read") && <Button onClick={() => setEditor("assign")}>Add person</Button>}</div>}</header>
    <p className="text-sm text-muted-foreground">A person can belong to multiple teams. Teams do not grant roles or login access. Dates use {organization.data.timezone}.</p>{can("teams.manage") && !can("resources.read") && <p>People read access is required to select someone for a new membership.</p>}
    <TeamHistory key={revision} org={org} team={team} canManage={can("teams.manage")} timezone={organization.data.timezone} />
    {editor === "assign" && can("teams.manage") && can("resources.read") ? <AssignmentEditor org={org} team={team} allowMembers={can("memberships.read")} timezone={organization.data.timezone} close={() => setEditor(undefined)} refresh={refresh} /> : editor && editor !== "assign" && can("teams.manage") && <RecordEditor org={org} kind="teams" record={team} statusOnly={editor === "status"} close={() => setEditor(undefined)} refresh={refresh} />}
  </section>;
}
export function PeoplePage() { const { orgId = "" } = useParams(); return <ListWorkspace key={orgId} org={orgId} kind="resources" />; }
export function TeamsPage() { const { orgId = "" } = useParams(); return <ListWorkspace key={orgId} org={orgId} kind="teams" />; }
export function PersonDetailPage() { const { orgId = "", resourceId = "" } = useParams(); return <PersonWorkspace key={`${orgId}:${resourceId}`} org={orgId} id={resourceId} />; }
export function TeamDetailPage() { const { orgId = "", teamId = "" } = useParams(); return <TeamWorkspace key={`${orgId}:${teamId}`} org={orgId} id={teamId} />; }
