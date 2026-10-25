import { useState } from "react";
import { organizationsApi } from "./api";
import { useOrganizationRead } from "./use-organization-read";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export function CreateOrganization({ onCreated }: { onCreated: () => void }) {
  const { data, error, retry } = useOrganizationRead((signal) => organizationsApi.provisioning(signal));
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [owner, setOwner] = useState("");
  const [timezone, setTimezone] = useState("Asia/Dhaka");
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<string>();
  const [success, setSuccess] = useState<string>();
  if (error) return <Alert><AlertDescription>Unable to check organization creation access. <Button variant="outline" onClick={retry}>Retry access check</Button></AlertDescription></Alert>;
  if (!data?.can_create) return null;
  return <div className="space-y-3">
    {success && <p role="status" className="text-sm">{success}</p>}
    <Dialog open={open} onOpenChange={(value) => { if (!pending) setOpen(value); }}>
      <DialogTrigger asChild><Button>Create organization</Button></DialogTrigger>
      <DialogContent><DialogHeader><DialogTitle>Create organization</DialogTitle><DialogDescription>Choose an existing active account as the first owner. Creating an organization for someone else does not give you membership.</DialogDescription></DialogHeader>
        <form className="space-y-4" onSubmit={async (event) => {
          event.preventDefault(); if (pending) return;
          setPending(true); setFailure(undefined); setSuccess(undefined);
          try {
            const result = await organizationsApi.create({ name, timezone, owner_username: owner });
            setOpen(false); setName(""); setOwner(""); onCreated();
            setSuccess(`${result.name} created.${result.membership_id ? " You can open it below." : " Its owner can now open it from their account."}`);
          } catch (cause) {
            setFailure(cause instanceof Error ? cause.message : "Unable to create organization.");
            onCreated();
          } finally { setPending(false); }
        }}>
          {failure && <Alert variant="destructive"><AlertDescription>{failure}</AlertDescription></Alert>}
          <div className="space-y-2"><Label htmlFor="organization-name">Organization name</Label><Input id="organization-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={200} required /></div>
          <div className="space-y-2"><Label htmlFor="organization-owner">Owner username</Label><Input id="organization-owner" value={owner} onChange={(e) => setOwner(e.target.value)} maxLength={150} required autoComplete="off" /></div>
          <div className="space-y-2"><Label htmlFor="organization-timezone">Timezone</Label><Input id="organization-timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} maxLength={64} required /></div>
          <Button disabled={pending}>{pending ? "Creating…" : "Create"}</Button>
        </form>
      </DialogContent>
    </Dialog>
  </div>;
}
