import type { StatusTone } from './data';

export function cn(...parts: unknown[]) {
  return parts.filter((p): p is string => typeof p === 'string' && p.length > 0).join(' ');
}

export function formatINR(value: number, compact = false) {
  if (compact) {
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(2)} L`;
    if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  }
  return `₹${value.toLocaleString('en-IN')}`;
}

/** Design-system status tokens — one source of truth for every badge in the app. */
export const TONE: Record<
  StatusTone,
  { bg: string; text: string; ring: string; dot: string; solid: string }
> = {
  active: {
    bg: 'bg-brand-50',
    text: 'text-brand-700',
    ring: 'ring-brand-600/20',
    dot: 'bg-brand-500',
    solid: 'bg-brand-600',
  },
  completed: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    ring: 'ring-emerald-600/20',
    dot: 'bg-emerald-500',
    solid: 'bg-emerald-600',
  },
  pending: {
    bg: 'bg-ink-100',
    text: 'text-ink-600',
    ring: 'ring-ink-500/15',
    dot: 'bg-ink-400',
    solid: 'bg-ink-500',
  },
  attention: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    ring: 'ring-amber-600/20',
    dot: 'bg-amber-500',
    solid: 'bg-amber-500',
  },
  critical: {
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    ring: 'ring-rose-600/20',
    dot: 'bg-rose-500',
    solid: 'bg-rose-600',
  },
  scheduled: {
    bg: 'bg-sky-50',
    text: 'text-sky-700',
    ring: 'ring-sky-600/20',
    dot: 'bg-sky-500',
    solid: 'bg-sky-600',
  },
  cancelled: {
    bg: 'bg-ink-100',
    text: 'text-ink-500',
    ring: 'ring-ink-400/15',
    dot: 'bg-ink-300',
    solid: 'bg-ink-400',
  },
  neutral: {
    bg: 'bg-ink-100',
    text: 'text-ink-600',
    ring: 'ring-ink-500/15',
    dot: 'bg-ink-400',
    solid: 'bg-ink-500',
  },
};

/** Maps a follicle diameter to a visual treatment — mature follicles read instantly. */
export function follicleTone(mm: number) {
  if (mm >= 16) return { fill: '#059669', ring: '#A7F3D0', label: 'Mature' };
  if (mm >= 12) return { fill: '#34D399', ring: '#D1FAE5', label: 'Developing' };
  return { fill: '#A8A29E', ring: '#E7E5E4', label: 'Small' };
}

export const TODAY = '29 July 2026';
