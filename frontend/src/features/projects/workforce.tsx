import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EntityDialog, Pagination, ReadError, TextField, useWorkspaceRead } from "@/features/workspace/components";
import { SearchablePicker, type Choice } from "@/features/workspace/searchable-picker";
import { workforceApi, type Worker } from "./workforce-api";

function WorkerEditor({ org, project, worker, close, refresh }: { org: string; project: string; worker?: Worker; close: () => void; refresh: () => void }) {
  const [kind, setKind] = useState<"members" | "resources">("members");
  const [choice, setChoice] = useState<Choice | null>(null);
  const [reason, setReason] = useState("");
  const [version, setVersion] = useState(worker?.version || 1);
  return <EntityDialog title={worker ? `End work assignment: ${worker.resource_name}` : "Add worker"} description="This records who works on the project. It never grants login or project access. Work/time entry will be a separate feature." onClose={close} onRefresh={refresh} saveLabel={worker ? "End work assignment" : "Add worker"} allowConflictRetry={!worker} reviewConflict={worker ? async () => {
    let page = 1;
    while (true) {
      const rows = await workforceApi.list(org, project, page);
      const latest = rows.results.find(row => row.id === worker.id);
      if (latest) { if (latest.ended_at) throw new Error("This assignment has already ended. Close and refresh the roster."); setVersion(latest.version); return `Latest worker: ${latest.resource_name}, version ${latest.version}.`; }
      if (!rows.next) throw new Error("Assignment unavailable. Close and refresh.");
      page++;
    }
  } : undefined} onSave={() => {
    if (worker) return workforceApi.end(org, project, worker.id, { version, reason });
    if (!choice) throw new Error("Choose a worker.");
    return workforceApi.add(org, project, { ...(kind === "members" ? { membership_id: choice.id } : { resource_id: choice.id }), reason });
  }}>
    {!worker && <><Select value={kind} onValueChange={(value: "members" | "resources") => { setKind(value); setChoice(null); }}><SelectTrigger aria-label="Worker source"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="members">Existing member</SelectItem><SelectItem value="resources">Existing resource / no-login worker</SelectItem></SelectContent></Select><SearchablePicker key={kind} label={kind === "members" ? "Organization member" : "Resource"} value={choice} onChange={setChoice} load={(search, page, signal) => workforceApi.options(org, project, kind, search, page, signal)} /></>}
    <TextField label="Reason" value={reason} onChange={setReason} required maxLength={500} />
  </EntityDialog>;
}
function WorkforceRows({ org, project, page, changePage, canManage, archived }: { org: string; project: string; page: number; changePage: (page: number) => void; canManage: boolean; archived: boolean }) {
  const read = useWorkspaceRead(signal => workforceApi.list(org, project, page, signal));
  const [editor, setEditor] = useState<Worker | "new">();
  if (read.denied) return <ReadError message={read.error || "Workforce unavailable."} retry={read.refresh} />;
  return <div className="space-y-4">{read.error && <ReadError message={read.error} retry={read.refresh} />}{canManage && !archived && <Button onClick={() => setEditor("new")}>Add worker</Button>}{!read.data ? <p role="status">Loading workforce…</p> : <>{!read.data.count && <p>No workers assigned yet.</p>}<ul className="space-y-3">{read.data.results.map(row => <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"><span>{row.resource_name} · {row.ended_at ? "Ended" : "Active"}</span>{canManage && !row.ended_at && <Button variant="outline" onClick={() => setEditor(row)}>End work assignment</Button>}</li>)}</ul><Pagination {...read.data} page={page} change={changePage} /></>}{editor && canManage && (editor !== "new" || !archived) && <WorkerEditor org={org} project={project} worker={editor === "new" ? undefined : editor} close={() => setEditor(undefined)} refresh={read.refresh} />}</div>;
}
export function ProjectWorkforce({ org, project, canManage, archived }: { org: string; project: string; canManage: boolean; archived: boolean }) {
  const [page, setPage] = useState(1);
  return <Card><CardHeader><CardTitle>Workforce</CardTitle></CardHeader><CardContent className="space-y-4"><p className="text-sm text-muted-foreground">Assign existing members directly, or select a resource without a login. This roster does not grant app access or record tasks/time yet.</p><WorkforceRows key={`${org}:${project}:${page}`} org={org} project={project} page={page} changePage={setPage} canManage={canManage} archived={archived} /></CardContent></Card>;
}
