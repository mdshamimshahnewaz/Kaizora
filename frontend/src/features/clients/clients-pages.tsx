import { useState } from "react";
import { Link, useParams } from "react-router";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { accessApi } from "@/features/identity/access-api";
import { EntityDialog, Pagination, ReadError, TextField, useWorkspaceRead } from "@/features/workspace/components";
import { clientsApi, type Client, type Contact } from "./api";

function ClientEditor({ org, client, onClose, refresh }: { org: string; client?: Client; onClose: () => void; refresh: () => void }) {
  const [name, setName] = useState(client?.name ?? "");
  const [code, setCode] = useState("");
  const [version, setVersion] = useState(client?.version ?? 1);
  const [reason, setReason] = useState("");
  return <EntityDialog allowConflictRetry={!client} title={client ? "Edit client" : "Create client"} description={client ? `Client code ${client.code} stays unchanged. Existing references retain this client's identity.` : "A client is your customer organization. Creating a contact does not create a login account."} onClose={onClose} onRefresh={refresh} reviewConflict={client ? async () => { const latest = await clientsApi.get(org, client.id); setVersion(latest.version); return `Latest client: ${latest.name} (${latest.status}), version ${latest.version}.`; } : undefined} saveLabel={client ? "Save changes" : "Create client"} onSave={() => client
    ? clientsApi.update(org, client.id, { name, version, reason })
    : clientsApi.create(org, { name, code })}>
    {!client && <TextField label="Client code" value={code} onChange={setCode} maxLength={32} required hint="Unique in this organization; cannot be changed later." />}
    <TextField label="Client name" value={name} onChange={setName} required />
    {client && <TextField label="Reason for change" value={reason} onChange={setReason} maxLength={500} required />}
  </EntityDialog>;
}

function ClientStatusEditor({ org, client, onClose, refresh }: { org: string; client: Client; onClose: () => void; refresh: () => void }) {
  const [reason, setReason] = useState("");
  const archive = client.status === "active";
  const [version, setVersion] = useState(client.version);
  return <EntityDialog title={`${archive ? "Archive" : "Restore"} ${client.name}`} description={archive ? "Existing project and historical references remain available. New projects cannot select this client until it is restored." : "This client becomes available for new projects and contacts again."} onClose={onClose} onRefresh={refresh} reviewConflict={async () => { const latest = await clientsApi.get(org, client.id); setVersion(latest.version); return `Latest client: ${latest.name} (${latest.status}), version ${latest.version}.`; }} saveLabel={archive ? "Archive client" : "Restore client"} onSave={() => clientsApi.update(org, client.id, { status: archive ? "archived" : "active", version, reason })}>
    <TextField label="Reason for change" value={reason} onChange={setReason} maxLength={500} required />
  </EntityDialog>;
}

function ClientResults({ org, page, search, status, changePage }: { org: string; page: number; search: string; status: string; changePage: (page: number) => void }) {
  const read = useWorkspaceRead((signal) => clientsApi.list(org, page, search, status, signal));
  if (read.error) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status">Loading clients…</p>;
  return <div className="space-y-4">{read.data.count ? <Table><TableHeader><TableRow><TableHead>Client</TableHead><TableHead>Code</TableHead><TableHead>Status</TableHead></TableRow></TableHeader><TableBody>{read.data.results.map((client) => <TableRow key={client.id}><TableCell><Link className="font-medium text-primary underline-offset-4 hover:underline" to={`/app/o/${org}/clients/${client.id}`}>{client.name}</Link></TableCell><TableCell>{client.code}</TableCell><TableCell><Badge variant="secondary">{client.status}</Badge></TableCell></TableRow>)}</TableBody></Table> : <p className="rounded-md border p-6 text-sm text-muted-foreground">No clients match this view. Create a client or adjust your filters.</p>}
    <Pagination {...read.data} page={page} change={changePage} />
  </div>;
}

function ClientsWorkspace({ org }: { org: string }) {
  const permissions = useWorkspaceRead((signal) => accessApi.permissions(org, signal));
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("active");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [creating, setCreating] = useState(false);
  const can = (key: string) => permissions.data?.permissions.includes(key) ?? false;
  return <section className="space-y-6">
    <header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-semibold">Clients</h1><p className="mt-2 text-sm text-muted-foreground">Manage the customers your organization works with.</p></div>{can("clients.manage") && <Button onClick={() => setCreating(true)}><Plus aria-hidden="true" />Create client</Button>}</header>
    {permissions.error ? <ReadError message={permissions.error} retry={permissions.refresh} /> : !permissions.data ? <p role="status">Checking access…</p> : can("clients.read") ? <>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); }}>
        <div className="min-w-56 flex-1"><TextField label="Search clients" value={search} onChange={setSearch} maxLength={100} /></div><Button variant="outline">Search</Button>
        <Select value={status} onValueChange={(value) => { setStatus(value); setPage(1); }}><SelectTrigger className="w-44" aria-label="Client status"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Active clients</SelectItem><SelectItem value="archived">Archived clients</SelectItem><SelectItem value="all">All clients</SelectItem></SelectContent></Select>
      </form>
      <ClientResults key={`${page}:${query}:${status}:${revision}`} org={org} page={page} search={query} status={status === "all" ? "" : status} changePage={setPage} />
    </> : <p>You do not have permission to view clients. Ask your organization owner for client read access.</p>}
    {creating && can("clients.manage") && !permissions.denied && <ClientEditor org={org} onClose={() => setCreating(false)} refresh={() => { setPage(1); setRevision((value) => value + 1); permissions.refresh(); }} />}
  </section>;
}

function ContactEditor({ org, clientId, contact, onClose, refresh }: { org: string; clientId: string; contact?: Contact; onClose: () => void; refresh: () => void }) {
  const [name, setName] = useState(contact?.name ?? "");
  const [email, setEmail] = useState(contact?.email ?? "");
  const [phone, setPhone] = useState(contact?.phone ?? "");
  const [position, setPosition] = useState(contact?.position ?? "");
  const [version, setVersion] = useState(contact?.version ?? 1);
  const [reason, setReason] = useState("");
  const [status, setStatus] = useState<"active" | "retired">(contact?.status ?? "active");
  return <EntityDialog allowConflictRetry={!contact} title={contact ? "Edit contact" : "Add contact"} description="Business contact information is visible only to people with contact read permission. Contacts are not application users." onClose={onClose} onRefresh={refresh} reviewConflict={contact ? async () => { const latest = await clientsApi.getContact(org, clientId, contact.id); setVersion(latest.version); return `Latest contact: ${latest.name}, ${latest.email || "no email"}, ${latest.phone || "no phone"}, ${latest.position || "no position"} (${latest.status}), version ${latest.version}.`; } : undefined} saveLabel={contact ? "Save contact" : "Add contact"} onSave={() => contact
    ? clientsApi.updateContact(org, clientId, contact.id, { name, email, phone, position, status, reason, version })
    : clientsApi.createContact(org, clientId, { name, email, phone, position })}>
    <TextField label="Contact name" value={name} onChange={setName} required />
    <TextField label="Email" value={email} onChange={setEmail} type="email" maxLength={254} />
    <TextField label="Phone" value={phone} onChange={setPhone} type="tel" maxLength={50} />
    <TextField label="Position" value={position} onChange={setPosition} />
    {contact && <><Select value={status} onValueChange={(value: "active" | "retired") => setStatus(value)}><SelectTrigger aria-label="Contact status"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Active</SelectItem><SelectItem value="retired">Retired</SelectItem></SelectContent></Select><TextField label="Reason for change" value={reason} onChange={setReason} maxLength={500} required hint="Business reason only; do not repeat personal contact information." /></>}
  </EntityDialog>;
}

function ContactResults({ org, clientId, page, status, changePage, canManage, edit }: { org: string; clientId: string; page: number; status: string; changePage: (page: number) => void; canManage: boolean; edit: (contact: Contact) => void }) {
  const read = useWorkspaceRead((signal) => clientsApi.contacts(org, clientId, page, status, signal));
  if (read.error) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status">Loading contacts…</p>;
  return <div className="space-y-4">{read.data.count ? <Table><TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Contact details</TableHead><TableHead>Position</TableHead><TableHead>Status</TableHead>{canManage && <TableHead>Actions</TableHead>}</TableRow></TableHeader><TableBody>{read.data.results.map((contact) => <TableRow key={contact.id}><TableCell className="font-medium">{contact.name}</TableCell><TableCell><div>{contact.email || "No email"}</div><div className="text-muted-foreground">{contact.phone || "No phone"}</div></TableCell><TableCell>{contact.position || "—"}</TableCell><TableCell><Badge variant="secondary">{contact.status}</Badge></TableCell>{canManage && <TableCell><Button variant="outline" size="sm" aria-label={`Edit ${contact.name}`} onClick={() => edit(contact)}>Edit</Button></TableCell>}</TableRow>)}</TableBody></Table> : <p className="text-sm text-muted-foreground">No contacts in this view.</p>}<Pagination {...read.data} page={page} change={changePage} /></div>;
}

function ClientDetail({ org, clientId }: { org: string; clientId: string }) {
  const permissions = useWorkspaceRead((signal) => accessApi.permissions(org, signal));
  const read = useWorkspaceRead((signal) => clientsApi.get(org, clientId, signal));
  const [editing, setEditing] = useState<Client>();
  const [changingStatus, setChangingStatus] = useState<Client>();
  const [contactEditor, setContactEditor] = useState<Contact | "new">();
  const [contactStatus, setContactStatus] = useState("active");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const can = (key: string) => permissions.data?.permissions.includes(key) ?? false;
  function refresh() { read.refresh(); permissions.refresh(); setRevision((value) => value + 1); }
  return <section className="space-y-6">
    <Button variant="outline" asChild><Link to={`/app/o/${org}/clients`}>Back to clients</Link></Button>
    {read.error || permissions.error ? <ReadError message={read.error ?? permissions.error ?? "Unable to load client."} retry={refresh} /> : !read.data || !permissions.data ? <p role="status">Loading client…</p> : <>
      <header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="break-words text-2xl font-semibold">{read.data.name}</h1><div className="mt-2 flex items-center gap-3 text-sm"><span>{read.data.code}</span><Badge variant="secondary">{read.data.status}</Badge></div></div>{can("clients.manage") && <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => setEditing(read.data)}>Edit client</Button><Button variant="outline" onClick={() => setChangingStatus(read.data)}>{read.data.status === "active" ? "Archive client" : "Restore client"}</Button></div>}</header>
      {read.data.status === "archived" && <p className="rounded-md border p-4 text-sm text-muted-foreground">Archived clients retain their history. Restore this client to add new project links or contacts.</p>}
      <Card><CardHeader><CardTitle>Contacts</CardTitle></CardHeader><CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">{can("contacts.read") && <Select value={contactStatus} onValueChange={(value) => { setContactStatus(value); setPage(1); }}><SelectTrigger className="w-44" aria-label="Filter contacts"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Active contacts</SelectItem><SelectItem value="retired">Retired contacts</SelectItem><SelectItem value="all">All contacts</SelectItem></SelectContent></Select>}{can("contacts.manage") && read.data.status === "active" && <Button onClick={() => setContactEditor("new")}><Plus aria-hidden="true" />Add contact</Button>}</div>
        {can("contacts.read") ? <ContactResults key={`${page}:${contactStatus}:${revision}`} org={org} clientId={clientId} page={page} status={contactStatus === "all" ? "" : contactStatus} changePage={setPage} canManage={can("contacts.manage")} edit={setContactEditor} /> : <p className="text-sm text-muted-foreground">Contact details require separate contact read permission.</p>}
      </CardContent></Card>
    </>}
    {editing && can("clients.manage") && can("clients.read") && !read.denied && !permissions.denied && <ClientEditor org={org} client={editing} onClose={() => setEditing(undefined)} refresh={refresh} />}
    {changingStatus && can("clients.manage") && can("clients.read") && !read.denied && !permissions.denied && <ClientStatusEditor org={org} client={changingStatus} onClose={() => setChangingStatus(undefined)} refresh={refresh} />}
    {contactEditor && can("contacts.manage") && (contactEditor === "new" || can("contacts.read")) && !read.denied && !permissions.denied && <ContactEditor org={org} clientId={clientId} contact={contactEditor === "new" ? undefined : contactEditor} onClose={() => setContactEditor(undefined)} refresh={refresh} />}
  </section>;
}

export function ClientsPage() {
  const { orgId } = useParams();
  return orgId ? <ClientsWorkspace key={orgId} org={orgId} /> : null;
}
export function ClientDetailPage() {
  const { orgId, clientId } = useParams();
  return orgId && clientId ? <ClientDetail key={`${orgId}:${clientId}`} org={orgId} clientId={clientId} /> : null;
}
