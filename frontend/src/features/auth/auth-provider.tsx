import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { authApi, type Credentials, type User } from "./api";

type AuthState = {
  status: "loading" | "ready" | "unavailable";
  user: User | null;
};
type AuthContextValue = AuthState & {
  refresh: () => Promise<void>;
  signIn: (credentials: Credentials) => Promise<void>;
  signOut: () => Promise<void>;
};
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    status: "loading",
    user: null,
  });
  const revision = useRef(0);
  const mutating = useRef(false);
  const refresh = useCallback(async () => {
    if (mutating.current) return;
    const requestRevision = ++revision.current;
    try {
      const snapshot = await authApi.session();
      if (requestRevision === revision.current)
        setState((previous) => {
          const current = previous.user;
          const next = snapshot.user;
          const unchanged =
            current === next ||
            (current !== null &&
              next !== null &&
              current.id === next.id &&
              current.username === next.username &&
              current.display_name === next.display_name &&
              current.email === next.email);
          return previous.status === "ready" && unchanged
            ? previous
            : { status: "ready", user: next };
        });
    } catch {
      if (requestRevision === revision.current)
        setState((previous) =>
          previous.status === "unavailable"
            ? previous
            : { status: "unavailable", user: null },
        );
    }
  }, []);

  useEffect(() => {
    void refresh();
    const onFocus = () => {
      void refresh();
    };
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 60_000);
    window.addEventListener("focus", onFocus);
    return () => {
      ++revision.current;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
    };
  }, [refresh]);

  async function signIn(credentials: Credentials) {
    mutating.current = true;
    ++revision.current;
    try {
      const snapshot = await authApi.login(credentials);
      setState({ status: "ready", user: snapshot.user });
    } finally {
      mutating.current = false;
    }
  }
  async function signOut() {
    mutating.current = true;
    ++revision.current;
    try {
      await authApi.logout();
      setState({ status: "ready", user: null });
    } finally {
      mutating.current = false;
    }
  }
  return (
    <AuthContext.Provider value={{ ...state, refresh, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth requires AuthProvider");
  return auth;
}
