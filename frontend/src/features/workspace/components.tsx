import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Mount with a scope/query key. Background refresh keeps drafts mounted, while
// failed authorization hides data through the caller's error state.
export function useWorkspaceRead<T>(read: (signal: AbortSignal) => Promise<T>) {
  const reader = useRef(read);
  const [state, setState] = useState<{ data?: T; error?: string; denied?: boolean }>({});
  const [revision, setRevision] = useState(0);
  useEffect(() => { reader.current = read; });
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    reader.current(controller.signal).then(
      (data) => { if (current) setState({ data }); },
      (error: unknown) => {
        if (current) {
          const status = error && typeof error === "object" && "status" in error ? error.status : undefined;
          const denied = status === 403 || status === 404;
          setState((previous) => ({ ...(denied ? {} : { data: previous.data }), denied, error: error instanceof Error ? error.message : "Unable to connect." }));
        }
      },
    );
    return () => { current = false; controller.abort(); };
  }, [revision]);
  useEffect(() => {
    const refresh = () => setRevision((value) => value + 1);
    window.addEventListener("focus", refresh);
    return () => window.removeEventListener("focus", refresh);
  }, []);
  return { ...state, refresh: () => setRevision((value) => value + 1) };
}

export function ReadError({ message, retry }: { message: string; retry: () => void }) {
  return <Alert variant="destructive"><AlertDescription className="flex flex-wrap items-center gap-3"><span>{message}</span><Button variant="outline" size="sm" onClick={retry}>Refresh</Button></AlertDescription></Alert>;
}

export function Pagination({ page, next, previous, count, change }: { page: number; next: string | null; previous: string | null; count: number; change: (page: number) => void }) {
  return <nav aria-label="Pagination" className="flex flex-wrap items-center gap-3"><Button variant="outline" disabled={!previous} onClick={() => change(page - 1)}>Previous</Button><span className="text-sm">Page {page} · {count} results</span><Button variant="outline" disabled={!next} onClick={() => change(page + 1)}>Next</Button></nav>;
}

export function TextField({ label, value, onChange, required = false, maxLength = 200, type = "text", hint }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; maxLength?: number; type?: string; hint?: string }) {
  const id = useId();
  return <div className="space-y-2"><Label htmlFor={id}>{label}</Label><Input id={id} value={value} onChange={(event) => onChange(event.target.value)} required={required} maxLength={maxLength} type={type} aria-describedby={hint ? `${id}-hint` : undefined} />{hint && <p id={`${id}-hint`} className="text-xs text-muted-foreground">{hint}</p>}</div>;
}

export function EntityDialog({ title, description, children, onClose, onSave, saveLabel = "Save changes", onRefresh, reviewConflict, allowConflictRetry = false }: { title: string; description: string; children: ReactNode; onClose: () => void; onSave: () => Promise<unknown>; saveLabel?: string; onRefresh: () => void; reviewConflict?: () => Promise<string>; allowConflictRetry?: boolean }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [blocked, setBlocked] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [review, setReview] = useState("");
  return <Dialog open onOpenChange={(open) => { if (!open && !pending) onClose(); }}><DialogContent className="max-h-[90dvh] overflow-y-auto"><DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription></DialogHeader>
    <form className="space-y-4" onSubmit={async (event) => {
      event.preventDefault(); if (pending || blocked) return; setPending(true); setError("");
      try { await onSave(); onRefresh(); onClose(); }
      catch (failure) { setConflict(!!failure && typeof failure === "object" && "status" in failure && failure.status === 409); setBlocked(!(failure && typeof failure === "object" && "status" in failure && (failure.status === 400 || (failure.status === 409 && allowConflictRetry)))); setError(failure instanceof Error ? failure.message : "Request failed. Refresh to check its outcome."); onRefresh(); }
      finally { setPending(false); }
    }}>
      <fieldset disabled={pending} className="space-y-4">{children}</fieldset>
      {error && <Alert variant="destructive"><AlertDescription><p>{error}</p><p className="mt-2">{blocked ? (conflict && reviewConflict ? "Your draft is kept. Review the latest saved version before applying your changes." : "Your draft is kept. Check the refreshed records before closing this form; the previous request may already have succeeded.") : "Correct the indicated fields, then save again."}</p><Button type="button" variant="outline" className="mt-2" onClick={onRefresh}>Refresh records</Button>{conflict && reviewConflict && <Button type="button" variant="outline" className="mt-2 ml-2" disabled={pending} onClick={async () => { setPending(true); try { setReview(await reviewConflict()); setBlocked(false); setConflict(false); setError(""); } catch (failure) { setError(failure instanceof Error ? failure.message : "Unable to refresh."); } finally { setPending(false); } }}>Review latest version</Button>}</AlertDescription></Alert>}
      {review && <div role="status" className="rounded-md border p-3 text-sm"><p>{review}</p><p className="mt-2">Your draft is unchanged. Saving now applies it to this latest version; cancel if you do not want to replace those fields.</p></div>}
      <DialogFooter><Button type="button" variant="outline" disabled={pending} onClick={onClose}>Cancel</Button><Button disabled={pending || blocked}>{pending ? "Saving…" : saveLabel}</Button></DialogFooter>
    </form>
  </DialogContent></Dialog>;
}
