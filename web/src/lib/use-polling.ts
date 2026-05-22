"use client";
/**
 * Custom hook: refaz uma chamada à API a cada N ms. Cancela em unmount.
 */
import { useEffect, useState } from "react";

import { POLL_INTERVAL_MS } from "./config";

interface PollingState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number = POLL_INTERVAL_MS,
): PollingState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const r = await fetcher();
        if (!cancelled) {
          setData(r);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    tick();
    const id = window.setInterval(tick, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs]);

  return { data, error, loading };
}
