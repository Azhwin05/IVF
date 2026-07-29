'use client';

import React from 'react';
import { cn, TONE } from '@/lib/utils';
import type { StatusTone } from '@/lib/data';
import { Check, X, AlertTriangle, Info, ChevronRight } from 'lucide-react';

/* ============================================================
   SURFACE
   ============================================================ */
export function Card({
  className,
  children,
  interactive,
  ...rest
}: React.HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div
      className={cn(
        'min-w-0 rounded-2xl border border-ink-200/70 bg-white shadow-card',
        interactive && 'lift cursor-pointer hover:border-brand-300/70 hover:shadow-lift',
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
  icon,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex items-start justify-between gap-4 px-5 pt-5 pb-4', className)}>
      <div className="flex items-start gap-3 min-w-0">
        {icon && (
          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 ring-1 ring-brand-600/10">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h3 className="text-[15px] font-semibold tracking-[-0.011em] text-ink-900">{title}</h3>
          {subtitle && <p className="mt-0.5 text-[13px] leading-relaxed text-ink-500">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

/* ============================================================
   BADGE
   ============================================================ */
export function Badge({
  tone = 'neutral',
  children,
  dot = true,
  className,
  size = 'md',
  wrap = false,
}: {
  tone?: StatusTone;
  children: React.ReactNode;
  dot?: boolean;
  className?: string;
  size?: 'sm' | 'md';
  wrap?: boolean;
}) {
  const t = TONE[tone];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium ring-1 ring-inset',
        wrap ? 'whitespace-normal text-left' : 'whitespace-nowrap',
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
        t.bg,
        t.text,
        t.ring,
        className
      )}
    >
      {dot && (
        <span className={cn('h-1.5 w-1.5 rounded-full', t.dot, tone === 'active' && 'animate-breathe')} />
      )}
      {children}
    </span>
  );
}

/* ============================================================
   BUTTON
   ============================================================ */
type BtnVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'dark';

export function Button({
  variant = 'secondary',
  size = 'md',
  icon,
  iconRight,
  loading,
  className,
  children,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: BtnVariant;
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  loading?: boolean;
}) {
  const variants: Record<BtnVariant, string> = {
    primary:
      'bg-brand-600 text-white shadow-[0_1px_2px_rgba(6,95,70,.25),inset_0_1px_0_rgba(255,255,255,.14)] hover:bg-brand-700 active:bg-brand-800 disabled:bg-brand-300',
    secondary:
      'bg-white text-ink-700 border border-ink-200 hover:bg-ink-50 hover:border-ink-300 active:bg-ink-100',
    ghost: 'text-ink-600 hover:bg-ink-100 hover:text-ink-900',
    danger: 'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800',
    dark: 'bg-ink-900 text-white hover:bg-ink-800 active:bg-ink-950',
  };
  const sizes = {
    sm: 'h-8 px-3 text-[13px] gap-1.5 rounded-lg',
    md: 'h-9.5 px-3.5 text-[13.5px] gap-2 rounded-lg',
    lg: 'h-11 px-5 text-[14.5px] gap-2 rounded-xl',
  };
  return (
    <button
      className={cn(
        'press inline-flex items-center justify-center font-medium transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-60',
        sizes[size],
        variants[variant],
        className
      )}
      style={size === 'md' ? { height: '2.375rem' } : undefined}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        icon
      )}
      {children}
      {iconRight}
    </button>
  );
}

/* ============================================================
   AVATAR
   ============================================================ */
export function Avatar({
  initials,
  size = 'md',
  gradient = 'from-brand-500 to-teal-600',
  ring,
  className,
}: {
  initials: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  gradient?: string;
  ring?: boolean;
  className?: string;
}) {
  const sizes = {
    xs: 'h-6 w-6 text-[10px]',
    sm: 'h-8 w-8 text-[11px]',
    md: 'h-10 w-10 text-[13px]',
    lg: 'h-12 w-12 text-[15px]',
    xl: 'h-16 w-16 text-xl',
  };
  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br font-semibold tracking-wide text-white',
        sizes[size],
        gradient,
        ring && 'ring-2 ring-white',
        className
      )}
    >
      {initials}
    </div>
  );
}

/* ============================================================
   LABELLED FIELD / DATA ROW
   ============================================================ */
export function Field({
  label,
  value,
  mono,
  className,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  className?: string;
}) {
  return (
    <div className={className}>
      <dt className="text-[11px] font-medium uppercase tracking-[0.07em] text-ink-400">{label}</dt>
      <dd className={cn('mt-1 text-[13.5px] font-medium text-ink-800', mono && 'tnum')}>{value}</dd>
    </div>
  );
}

export function DataRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  tone?: StatusTone;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-ink-100 py-2.5 last:border-0">
      <span className="text-[13px] text-ink-500">{label}</span>
      {tone ? (
        <Badge tone={tone} size="sm">
          {value}
        </Badge>
      ) : (
        <span className="tnum text-[13px] font-medium text-ink-800">{value}</span>
      )}
    </div>
  );
}

/* ============================================================
   SECTION HEADING
   ============================================================ */
export function SectionTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-6">
      <div className="min-w-0">
        {eyebrow && (
          <div className="mb-1.5 flex items-center gap-2">
            <span className="h-px w-6 bg-brand-500" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-700">
              {eyebrow}
            </span>
          </div>
        )}
        <h2 className="tracking-display text-[21px] font-semibold text-ink-900 sm:text-[26px]">{title}</h2>
        {description && <p className="mt-1 text-[13px] text-ink-500 sm:text-[13.5px]">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div>}
    </div>
  );
}

/* ============================================================
   PROGRESS
   ============================================================ */
export function ProgressBar({
  value,
  tone = 'brand',
  className,
  height = 6,
}: {
  value: number;
  tone?: 'brand' | 'amber' | 'rose' | 'sky';
  className?: string;
  height?: number;
}) {
  const colors = {
    brand: 'from-brand-400 to-brand-600',
    amber: 'from-amber-400 to-amber-600',
    rose: 'from-rose-400 to-rose-600',
    sky: 'from-sky-400 to-sky-600',
  };
  return (
    <div
      className={cn('w-full overflow-hidden rounded-full bg-ink-100', className)}
      style={{ height }}
    >
      <div
        className={cn('h-full rounded-full bg-gradient-to-r transition-[width] duration-[1200ms] ease-spring', colors[tone])}
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
      />
    </div>
  );
}

/* ============================================================
   SKELETON
   ============================================================ */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton rounded-lg', className)} />;
}

export function SkeletonCard() {
  return (
    <Card className="p-5">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-4 h-8 w-32" />
      <Skeleton className="mt-3 h-3 w-40" />
    </Card>
  );
}

/* ============================================================
   TABS
   ============================================================ */
export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: string; label: string; count?: number }[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="scroll-area flex gap-1 overflow-x-auto border-b border-ink-200/80">
      {tabs.map((t) => {
        const isActive = t.id === active;
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            data-active={isActive}
            className={cn(
              'tab-underline relative whitespace-nowrap px-3.5 pb-3 pt-2 text-[13.5px] font-medium transition-colors',
              isActive ? 'text-brand-700' : 'text-ink-500 hover:text-ink-800'
            )}
          >
            {t.label}
            {typeof t.count === 'number' && (
              <span
                className={cn(
                  'tnum ml-1.5 rounded-full px-1.5 py-0.5 text-[10.5px] font-semibold',
                  isActive ? 'bg-brand-100 text-brand-700' : 'bg-ink-100 text-ink-500'
                )}
              >
                {t.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ============================================================
   MODAL
   ============================================================ */
export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
  width = 'max-w-lg',
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: string;
}) {
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6">
      <div
        className="absolute inset-0 bg-ink-950/25 backdrop-blur-[3px] animate-fade-in"
        onClick={onClose}
      />
      <div className={cn('modal-in relative max-h-[90vh] w-full overflow-hidden rounded-2xl bg-white shadow-pop flex flex-col', width)}>
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-ink-100 px-4 py-4 sm:px-6 sm:py-5">
          <div className="min-w-0">
            <h3 className="text-[15.5px] font-semibold tracking-[-0.014em] text-ink-900 sm:text-[17px]">{title}</h3>
            {subtitle && <p className="mt-1 text-[12.5px] text-ink-500 sm:text-[13px]">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="scroll-area min-h-0 flex-1 px-4 py-4 sm:px-6 sm:py-5">{children}</div>
        {footer && (
          <div className="flex shrink-0 flex-col-reverse justify-end gap-2 border-t border-ink-100 bg-ink-50/60 px-4 py-4 rounded-b-2xl sm:flex-row sm:px-6">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

/* ============================================================
   TOAST
   ============================================================ */
export interface ToastItem {
  id: number;
  title: string;
  body?: string;
  tone?: 'success' | 'info' | 'warning' | 'error';
}

export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}) {
  const config = {
    success: { icon: Check, cls: 'bg-brand-600 text-white', ring: 'ring-brand-700/20' },
    info: { icon: Info, cls: 'bg-sky-600 text-white', ring: 'ring-sky-700/20' },
    warning: { icon: AlertTriangle, cls: 'bg-amber-500 text-white', ring: 'ring-amber-600/20' },
    error: { icon: X, cls: 'bg-rose-600 text-white', ring: 'ring-rose-700/20' },
  };
  return (
    <div className="pointer-events-none fixed inset-x-3 bottom-3 z-[200] flex flex-col gap-2.5 sm:inset-x-auto sm:bottom-6 sm:right-6 sm:w-[360px]">
      {toasts.map((t) => {
        const c = config[t.tone ?? 'success'];
        const Icon = c.icon;
        return (
          <div
            key={t.id}
            className="toast-in pointer-events-auto flex items-start gap-3 rounded-xl border border-ink-200/70 bg-white p-3.5 shadow-float"
          >
            <div className={cn('mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg', c.cls)}>
              <Icon className="h-4 w-4" strokeWidth={2.5} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[13.5px] font-semibold text-ink-900">{t.title}</p>
              {t.body && <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-500">{t.body}</p>}
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              className="rounded-md p-1 text-ink-300 transition-colors hover:bg-ink-100 hover:text-ink-600"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

/* ============================================================
   EMPTY / INFO STATES
   ============================================================ */
export function InfoNote({
  children,
  tone = 'neutral',
  icon,
}: {
  children: React.ReactNode;
  tone?: 'neutral' | 'brand' | 'amber';
  icon?: React.ReactNode;
}) {
  const map = {
    neutral: 'bg-ink-50 border-ink-200/70 text-ink-600',
    brand: 'bg-brand-50/70 border-brand-200/70 text-brand-800',
    amber: 'bg-amber-50/70 border-amber-200/70 text-amber-800',
  };
  return (
    <div className={cn('flex gap-2.5 rounded-xl border p-3.5 text-[13px] leading-relaxed', map[tone])}>
      {icon && <div className="mt-0.5 shrink-0">{icon}</div>}
      <div>{children}</div>
    </div>
  );
}

export function ActionRow({
  label,
  description,
  icon,
  onClick,
}: {
  label: string;
  description?: string;
  icon?: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="lift group flex w-full items-center gap-3 rounded-xl border border-ink-200/70 bg-white p-3.5 text-left hover:border-brand-300/70 hover:shadow-lift"
    >
      {icon && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 ring-1 ring-brand-600/10 transition-colors group-hover:bg-brand-100">
          {icon}
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-[13.5px] font-medium text-ink-900">{label}</p>
        {description && <p className="mt-0.5 text-[12px] text-ink-500">{description}</p>}
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
    </button>
  );
}

/* ============================================================
   INPUT
   ============================================================ */
export function Input({
  label,
  hint,
  icon,
  className,
  ...rest
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
  icon?: React.ReactNode;
}) {
  return (
    <label className="block">
      {label && (
        <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">{label}</span>
      )}
      <div className="relative">
        {icon && (
          <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-400">
            {icon}
          </div>
        )}
        <input
          className={cn(
            'h-10 w-full rounded-lg border border-ink-200 bg-white px-3 text-[13.5px] text-ink-900 transition-shadow placeholder:text-ink-400',
            icon && 'pl-9',
            className
          )}
          {...rest}
        />
      </div>
      {hint && <span className="mt-1 block text-[11.5px] text-ink-400">{hint}</span>}
    </label>
  );
}

export function Select({
  label,
  children,
  className,
  ...rest
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <label className="block">
      {label && <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">{label}</span>}
      <select
        className={cn(
          'h-10 w-full rounded-lg border border-ink-200 bg-white px-3 text-[13.5px] text-ink-900',
          className
        )}
        {...rest}
      >
        {children}
      </select>
    </label>
  );
}
