import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTheme } from "@/components/theme/theme-provider";
import { useAccount } from "./account-provider";
import { type Account, AccountError } from "./api";

export function AccountPage() {
  const { account, error, reload } = useAccount();
  const [retryError, setRetryError] = useState("");
  return <div className="space-y-6"><header><h1 className="text-2xl font-semibold tracking-tight">Your account</h1><p className="mt-2 text-sm text-muted-foreground">Manage your name and preferences across devices.</p></header>
    {!account ? error || retryError ? <div role="alert" className="space-y-3"><p>{retryError || error}</p><Button onClick={() => void reload().catch((e: unknown) => setRetryError(e instanceof Error ? e.message : "Unable to load account."))}>Try again</Button></div> : <p role="status">Loading your account…</p> : <AccountForm key={account.id} initial={account} />}
  </div>;
}
function AccountForm({ initial }: { initial: Account }) {
  const { save, reload } = useAccount();
  const { theme: deviceTheme } = useTheme();
  const [firstName, setFirstName] = useState(initial.first_name);
  const [lastName, setLastName] = useState(initial.last_name);
  const [theme, setTheme] = useState<"light" | "dark" | "system">(initial.preferences.theme || deviceTheme);
  const [timezone, setTimezone] = useState(initial.preferences.timezone || "");
  const [version, setVersion] = useState(initial.version);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [needsReview, setNeedsReview] = useState(false);
  const [latest, setLatest] = useState<Account | null>(null);
  return <form className="space-y-6" onSubmit={async (event) => {
    event.preventDefault(); if (pending || needsReview) return;
    setPending(true); setError(""); setMessage("");
    try {
      const saved = await save({ version, first_name: firstName, last_name: lastName, preferences: { theme, timezone: timezone.trim() || null } });
      setVersion(saved.version); setLatest(null); setMessage("Account saved.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to save your account.");
      if (!(cause instanceof AccountError) || cause.status === 409 || cause.status >= 500) setNeedsReview(true);
    } finally { setPending(false); }
  }}>
    <section className="space-y-5 rounded-lg border bg-card p-6"><h2 className="font-semibold">Profile</h2><div className="grid gap-5 sm:grid-cols-2">
      <div className="space-y-2"><Label htmlFor="account-first">First name</Label><Input id="account-first" value={firstName} onChange={(e) => setFirstName(e.target.value)} maxLength={150} autoComplete="given-name" /></div>
      <div className="space-y-2"><Label htmlFor="account-last">Last name</Label><Input id="account-last" value={lastName} onChange={(e) => setLastName(e.target.value)} maxLength={150} autoComplete="family-name" /></div>
      <div className="space-y-2"><Label htmlFor="account-username">Username</Label><Input id="account-username" value={initial.username} readOnly /></div>
      <div className="space-y-2"><Label htmlFor="account-email">Email</Label><Input id="account-email" value={initial.email} readOnly placeholder="Not provided" /></div>
    </div><p className="text-sm text-muted-foreground">Username and email are managed by your administrator.</p></section>
    <section className="space-y-5 rounded-lg border bg-card p-6"><h2 className="font-semibold">Preferences</h2><div className="grid gap-5 sm:grid-cols-2">
      <div className="space-y-2"><Label htmlFor="account-theme">Theme</Label><Select value={theme} onValueChange={(v) => { if (v === "light" || v === "dark" || v === "system") setTheme(v); }}><SelectTrigger id="account-theme"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="light">Light</SelectItem><SelectItem value="dark">Dark</SelectItem><SelectItem value="system">System</SelectItem></SelectContent></Select></div>
      <div className="space-y-2"><Label htmlFor="account-timezone">Personal timezone</Label><Input id="account-timezone" list="account-timezones" value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="Inherit organization timezone" maxLength={100} /><datalist id="account-timezones">{Intl.supportedValuesOf("timeZone").map((zone) => <option key={zone} value={zone} />)}<option value="UTC" /></datalist></div>
    </div><p className="text-sm text-muted-foreground">Leave timezone blank to follow the selected organization, or the application default outside an organization. This changes timestamp display only.</p></section>
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}{message && <p role="status" className="text-sm text-success">{message}</p>}
    {needsReview && <Button type="button" variant="outline" disabled={pending} onClick={async () => { setPending(true); try { const fresh = await reload(); setLatest(fresh); setVersion(fresh.version); setNeedsReview(false); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to refresh."); } finally { setPending(false); } }}>Review latest saved values</Button>}
    {latest && <div className="rounded-lg border p-4 text-sm" role="status"><p>Latest saved: {latest.display_name}; theme: {latest.preferences.theme || "device default"}; timezone: {latest.preferences.timezone || "inherited"}.</p><p>Your inputs above are preserved. Review them, then save to apply your changes.</p></div>}
    <Button type="submit" disabled={pending || needsReview}>{pending ? "Please wait…" : "Save changes"}</Button>
  </form>;
}
