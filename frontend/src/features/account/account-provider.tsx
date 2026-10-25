import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useAuth } from "@/features/auth/auth-provider";
import { useTheme } from "@/components/theme/theme-provider";
import { accountApi, type Account, type AccountUpdate } from "./api";

type Value = { signedIn: boolean; account: Account | null; error: string; reload: () => Promise<Account>; save: (patch: AccountUpdate) => Promise<Account> };
const Context = createContext<Value | null>(null);
export function AccountProvider({ children }: { children: ReactNode }) {
  const { user, refresh } = useAuth();
  const { setTheme } = useTheme();
  const [account, setAccount] = useState<Account | null>(null);
  const [failure, setFailure] = useState<{ userId: string; message: string } | null>(null);
  const latestAccount = useRef<Account | null>(null);
  const currentUser = useRef(user?.id);
  currentUser.current = user?.id;
  const apply = useCallback((next: Account) => {
    if (currentUser.current !== next.id) return;
    if (latestAccount.current?.id === next.id && latestAccount.current.version > next.version) return;
    latestAccount.current = next;
    setAccount(next);
    setFailure(null);
    if (next.preferences.theme) setTheme(next.preferences.theme);
  }, [setTheme]);
  const reload = useCallback(async () => {
    const next = await accountApi.get();
    apply(next);
    return next;
  }, [apply]);
  useEffect(() => {
    if (!user?.id) return;
    const controller = new AbortController();
    void accountApi.get(controller.signal).then(apply).catch((cause: unknown) => {
      if (!controller.signal.aborted) setFailure({ userId: user.id, message: cause instanceof Error ? cause.message : "Unable to load your account." });
    });
    return () => controller.abort();
  }, [user?.id, apply]);
  async function save(patch: AccountUpdate) {
    const next = await accountApi.update(patch);
    apply(next);
    await refresh();
    return next;
  }
  return <Context.Provider value={{ signedIn: !!user, account: account?.id === user?.id ? account : null, error: failure?.userId === user?.id ? failure?.message || "" : "", reload, save }}>{children}</Context.Provider>;
}
export function useOptionalAccount() { return useContext(Context); }
export function useAccount() {
  const context = useOptionalAccount();
  if (!context) throw new Error("AccountProvider is required");
  return context;
}
/** Business dates remain unchanged; use this only for display of timestamps. */
export function effectiveTimezone(account: Account, organizationTimezone?: string) {
  return account.preferences.timezone || organizationTimezone || account.effective_timezone;
}
