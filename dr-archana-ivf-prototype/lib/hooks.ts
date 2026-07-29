'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Animates a number from 0 to `end` using an ease-out curve.
 * Used on every dashboard metric so figures "count in" on screen entry.
 */
export function useCountUp(end: number, duration = 1100, start = true) {
  const [value, setValue] = useState(0);
  const frame = useRef<number>();
  const settle = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!start) return;

    const t0 = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - t0) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(end * eased);
      if (p < 1) frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);

    // Safety net: requestAnimationFrame is paused in background or
    // non-compositing tabs, which would leave the figure stuck at 0.
    // Guarantee the final value lands regardless of frame delivery.
    settle.current = setTimeout(() => {
      if (frame.current) cancelAnimationFrame(frame.current);
      setValue(end);
    }, duration + 120);

    return () => {
      if (frame.current) cancelAnimationFrame(frame.current);
      if (settle.current) clearTimeout(settle.current);
    };
  }, [end, duration, start]);

  return value;
}

/** Fires once when the element scrolls into view — drives chart draw-in. */
export function useInView<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          obs.disconnect();
        }
      },
      { threshold }
    );
    obs.observe(el);

    // Safety net: if the observer never fires (background tab, zero-size
    // layout during hydration), reveal anyway so charts are never blank.
    const fallback = setTimeout(() => {
      setInView(true);
      obs.disconnect();
    }, 1200);

    return () => {
      obs.disconnect();
      clearTimeout(fallback);
    };
  }, [threshold]);

  return { ref, inView };
}

/** Simulates async work so loading states are demonstrable in the prototype. */
export function useSimulatedLoad(deps: unknown[], ms = 420) {
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => setLoading(false), ms);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return loading;
}

/** Global keyboard shortcut binding (used for ⌘K command palette). */
export function useHotkey(key: string, handler: () => void, meta = true) {
  const saved = useRef(handler);
  saved.current = handler;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const modifier = meta ? e.metaKey || e.ctrlKey : true;
      if (modifier && e.key.toLowerCase() === key.toLowerCase()) {
        e.preventDefault();
        saved.current();
      }
      if (!meta && key === 'Escape' && e.key === 'Escape') {
        saved.current();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [key, meta]);
}

/** Live wall-clock used in the top bar. */
export function useClock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return now;
}

/** Sequential step runner for the login authentication choreography. */
export function useSequence(steps: number, interval: number, running: boolean) {
  const [step, setStep] = useState(-1);
  useEffect(() => {
    if (!running) {
      setStep(-1);
      return;
    }
    let i = 0;
    setStep(0);
    const t = setInterval(() => {
      i += 1;
      if (i >= steps) {
        clearInterval(t);
        return;
      }
      setStep(i);
    }, interval);
    return () => clearInterval(t);
  }, [steps, interval, running]);
  return step;
}

export function useToggle(initial = false) {
  const [on, setOn] = useState(initial);
  const toggle = useCallback(() => setOn((v) => !v), []);
  return [on, toggle, setOn] as const;
}
