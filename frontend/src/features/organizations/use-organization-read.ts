import { useCallback, useEffect, useRef, useState } from "react";

// Callers key this hook’s component by organization/page to isolate private data.
// Background revalidation keeps the mounted view until a result arrives; failures
// clear it. Cleanup rejects stale responses even when transport cancellation fails.
export function useOrganizationRead<T>(read: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<{ data?: T; error?: string }>({});
  const [revision, setRevision] = useState(0);
  const reader = useRef(read);
  useEffect(() => { reader.current = read; });
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    reader.current(controller.signal).then(
      (data) => { if (current) setState({ data }); },
      (error: unknown) => {
        if (current) setState({ error: error instanceof Error && error.name !== "TypeError"
          ? error.message : "Unable to connect. Please try again." });
      },
    );
    return () => { current = false; controller.abort(); };
  }, [revision]);
  const refresh = useCallback(() => {
    setRevision((value) => value + 1);
  }, []);
  useEffect(() => {
    window.addEventListener("focus", refresh);
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, 60_000);
    return () => { window.removeEventListener("focus", refresh); window.clearInterval(timer); };
  }, [refresh]);
  const retry = useCallback(() => {
    // Explicit retries after mutations/conflicts must discard the old snapshot.
    setState({});
    refresh();
  }, [refresh]);
  return { ...state, retry };
}

