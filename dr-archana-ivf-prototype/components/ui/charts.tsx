'use client';

import React, { useId, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { useInView, useCountUp } from '@/lib/hooks';

/* ============================================================
   SPARKLINE — inline trend for metric tiles
   ============================================================ */
export function Sparkline({
  data,
  color = '#059669',
  height = 32,
  className,
}: {
  data: number[];
  color?: string;
  height?: number;
  className?: string;
}) {
  const id = useId();
  const w = 100;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = height - 4 - ((v - min) / span) * (height - 8);
    return [x, y] as const;
  });
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ');
  const area = `${line} L${w},${height} L0,${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${w} ${height}`}
      preserveAspectRatio="none"
      className={cn('w-full', className)}
      style={{ height }}
    >
      <defs>
        <linearGradient id={`sg-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${id})`} className="reveal-area" />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
        className="draw-line"
        style={{ ['--len' as string]: 300 }}
      />
      <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="2.2" fill={color} className="animate-fade-in" style={{ animationDelay: '1.2s' }} />
    </svg>
  );
}

/* ============================================================
   AREA CHART — revenue / volume trend with hover readout
   ============================================================ */
export function AreaChart({
  data,
  height = 220,
  valueLabel = '',
  color = '#059669',
}: {
  data: { label: string; value: number }[];
  height?: number;
  valueLabel?: string;
  color?: string;
}) {
  const id = useId();
  const { ref, inView } = useInView<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);

  const padL = 44;
  const padR = 12;
  const padT = 16;
  const padB = 28;
  const w = 640;
  const innerW = w - padL - padR;
  const innerH = height - padT - padB;

  const max = Math.max(...data.map((d) => d.value)) * 1.15;
  const min = 0;
  const pts = data.map((d, i) => {
    const x = padL + (i / (data.length - 1)) * innerW;
    const y = padT + innerH - ((d.value - min) / (max - min)) * innerH;
    return { x, y, ...d };
  });

  // Smooth cubic path through points
  const path = useMemo(() => {
    if (pts.length < 2) return '';
    let d = `M${pts[0].x},${pts[0].y}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const cx = (p0.x + p1.x) / 2;
      d += ` C${cx},${p0.y} ${cx},${p1.y} ${p1.x},${p1.y}`;
    }
    return d;
  }, [pts]);

  const areaPath = `${path} L${pts[pts.length - 1].x},${padT + innerH} L${pts[0].x},${padT + innerH} Z`;
  const ticks = 4;

  return (
    <div ref={ref} className="relative">
      <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ height }}>
        <defs>
          <linearGradient id={`ag-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.20" />
            <stop offset="100%" stopColor={color} stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {/* horizontal guides */}
        {Array.from({ length: ticks + 1 }).map((_, i) => {
          const y = padT + (i / ticks) * innerH;
          const val = max - (i / ticks) * (max - min);
          return (
            <g key={i}>
              <line x1={padL} y1={y} x2={w - padR} y2={y} stroke="#E7E5E4" strokeWidth="1" strokeDasharray={i === ticks ? '0' : '3 4'} />
              <text x={padL - 10} y={y + 3.5} textAnchor="end" className="tnum" fontSize="10.5" fill="#A8A29E">
                {val.toFixed(0)}
              </text>
            </g>
          );
        })}

        {inView && (
          <>
            <path d={areaPath} fill={`url(#ag-${id})`} className="reveal-area" />
            <path
              d={path}
              fill="none"
              stroke={color}
              strokeWidth="2.25"
              strokeLinecap="round"
              className="draw-line"
              style={{ ['--len' as string]: 1400 }}
            />
          </>
        )}

        {/* points + hover targets */}
        {pts.map((p, i) => (
          <g key={i}>
            {hover === i && (
              <line x1={p.x} y1={padT} x2={p.x} y2={padT + innerH} stroke={color} strokeWidth="1" strokeDasharray="3 3" opacity="0.45" />
            )}
            {inView && (
              <circle
                cx={p.x}
                cy={p.y}
                r={hover === i ? 5 : 3.5}
                fill="#fff"
                stroke={color}
                strokeWidth="2.25"
                className="animate-scale-in transition-all"
                style={{ animationDelay: `${0.7 + i * 0.07}s` }}
              />
            )}
            <rect
              x={p.x - innerW / data.length / 2}
              y={padT}
              width={innerW / data.length}
              height={innerH}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
            <text x={p.x} y={height - 8} textAnchor="middle" fontSize="11" fill="#78716C" fontWeight="500">
              {p.label}
            </text>
          </g>
        ))}
      </svg>

      {hover !== null && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg bg-ink-900 px-2.5 py-1.5 text-[11.5px] font-medium text-white shadow-float"
          style={{ left: `${(pts[hover].x / w) * 100}%`, top: `${(pts[hover].y / height) * 100}%`, marginTop: -10 }}
        >
          <span className="tnum">
            {pts[hover].value}
            {valueLabel}
          </span>
          <span className="ml-1.5 text-ink-400">{pts[hover].label}</span>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   DONUT — cycle distribution / outcomes
   ============================================================ */
export function DonutChart({
  data,
  size = 180,
  thickness = 22,
  centerLabel,
  centerValue,
}: {
  data: { label: string; value: number; color: string }[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string | number;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const total = data.reduce((s, d) => s + d.value, 0);
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div ref={ref} className="flex items-center gap-6">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#F5F5F4" strokeWidth={thickness} />
          {data.map((d, i) => {
            const frac = d.value / total;
            const len = frac * c;
            const dash = `${len} ${c - len}`;
            const thisOffset = offset;
            offset += len;
            return (
              <circle
                key={i}
                cx={size / 2}
                cy={size / 2}
                r={r}
                fill="none"
                stroke={d.color}
                strokeWidth={hover === i ? thickness + 4 : thickness}
                strokeDasharray={dash}
                strokeDashoffset={inView ? -thisOffset : -c}
                strokeLinecap="butt"
                className="cursor-pointer transition-all duration-[900ms] ease-spring"
                style={{ transitionDelay: `${i * 90}ms` }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="tnum tracking-display text-[26px] font-semibold text-ink-900">
            {hover !== null ? data[hover].value : centerValue ?? total}
          </span>
          <span className="mt-0.5 max-w-[80px] text-center text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-400">
            {hover !== null ? data[hover].label : centerLabel ?? 'Total'}
          </span>
        </div>
      </div>

      <div className="min-w-0 flex-1 space-y-2">
        {data.map((d, i) => (
          <div
            key={i}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
            className={cn(
              'flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 transition-colors',
              hover === i ? 'bg-ink-50' : 'hover:bg-ink-50/60'
            )}
          >
            <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ backgroundColor: d.color }} />
            <span className="min-w-0 flex-1 truncate text-[12.5px] text-ink-600">{d.label}</span>
            <span className="tnum text-[12.5px] font-semibold text-ink-900">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   BAR CHART — grouped monthly comparison
   ============================================================ */
export function BarChart({
  data,
  height = 200,
  color = '#059669',
  suffix = '',
}: {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
  suffix?: string;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value)) * 1.18;

  return (
    <div ref={ref} className="flex items-end gap-2" style={{ height }}>
      {data.map((d, i) => {
        const h = (d.value / max) * 100;
        return (
          <div
            key={i}
            className="group flex h-full flex-1 flex-col items-center justify-end gap-2"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <span
              className={cn(
                'tnum text-[11.5px] font-semibold transition-opacity',
                hover === i ? 'text-ink-900 opacity-100' : 'text-ink-400 opacity-0 group-hover:opacity-100'
              )}
            >
              {d.value}
              {suffix}
            </span>
            <div
              className="w-full max-w-[38px] overflow-hidden rounded-t-md"
              style={{ height: `${h}%` }}
            >
              <div
                className={cn('grow-up h-full w-full rounded-t-md transition-opacity', hover !== null && hover !== i && 'opacity-45')}
                style={{
                  background: `linear-gradient(180deg, ${color}, ${color}bb)`,
                  animationDelay: `${i * 70}ms`,
                  animationPlayState: inView ? 'running' : 'paused',
                }}
              />
            </div>
            <span className="text-[11px] font-medium text-ink-500">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ============================================================
   PROGRESS RING — KPI dial
   ============================================================ */
export function ProgressRing({
  value,
  size = 92,
  thickness = 8,
  color = '#059669',
  label,
  suffix = '%',
}: {
  value: number;
  size?: number;
  thickness?: number;
  color?: string;
  label?: string;
  suffix?: string;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const animated = useCountUp(value, 1200, inView);
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const dash = (Math.min(value, 100) / 100) * c;

  return (
    <div ref={ref} className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#F5F5F4" strokeWidth={thickness} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={thickness}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
            strokeDashoffset={0}
            style={{
              transition: 'stroke-dasharray 1.3s cubic-bezier(0.16,1,0.3,1)',
              strokeDasharray: inView ? `${dash} ${c}` : `0 ${c}`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="tnum text-[17px] font-semibold text-ink-900">
            {Math.round(animated)}
            {suffix}
          </span>
        </div>
      </div>
      {label && <span className="text-center text-[11.5px] font-medium text-ink-500">{label}</span>}
    </div>
  );
}

/* ============================================================
   FOLLICLE MAP — bespoke ovarian visualisation
   This is the clinical signature of the product.
   ============================================================ */
export function FollicleMap({
  right,
  left,
  animate = true,
}: {
  right: number[];
  left: number[];
  animate?: boolean;
}) {
  const [focus, setFocus] = useState<string | null>(null);

  const Ovary = ({ label, sizes, side }: { label: string; sizes: number[]; side: 'R' | 'L' }) => {
    const mature = sizes.filter((s) => s >= 16).length;
    // Deterministic scatter positions inside the ovary ellipse
    const positions = [
      { x: 34, y: 38 },
      { x: 66, y: 34 },
      { x: 40, y: 66 },
      { x: 68, y: 64 },
      { x: 52, y: 50 },
      { x: 24, y: 54 },
    ];

    return (
      <div className="flex-1">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[12.5px] font-semibold text-ink-700">{label}</span>
          <span className="tnum rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700 ring-1 ring-inset ring-brand-600/15">
            {mature} mature · {sizes.length} total
          </span>
        </div>

        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-ink-200/70 bg-gradient-to-br from-ink-50 to-white">
          {/* ovary silhouette */}
          <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
            <ellipse cx="50" cy="50" rx="40" ry="32" fill="#FAFAF9" stroke="#E7E5E4" strokeWidth="0.6" />
            <ellipse cx="50" cy="50" rx="40" ry="32" fill="none" stroke="#D1FAE5" strokeWidth="0.4" strokeDasharray="2 2" />
          </svg>

          {sizes.map((mm, i) => {
            const pos = positions[i % positions.length];
            // 11–18mm maps to a 13–30% diameter bubble
            const diameter = 13 + ((mm - 10) / 10) * 17;
            const isMature = mm >= 16;
            const isDeveloping = mm >= 12 && mm < 16;
            const key = `${side}-${i}`;
            const active = focus === key;
            const fill = isMature ? '#059669' : isDeveloping ? '#34D399' : '#A8A29E';

            return (
              <div
                key={key}
                onMouseEnter={() => setFocus(key)}
                onMouseLeave={() => setFocus(null)}
                className={cn('absolute cursor-pointer', animate && 'follicle-in')}
                style={{
                  left: `${pos.x}%`,
                  top: `${pos.y}%`,
                  width: `${diameter}%`,
                  height: `${diameter * 1.33}%`,
                  transform: 'translate(-50%, -50%)',
                  animationDelay: `${i * 90}ms`,
                }}
              >
                <div
                  className="relative flex h-full w-full items-center justify-center rounded-full transition-transform duration-300 ease-spring"
                  style={{
                    background: `radial-gradient(circle at 35% 30%, ${fill}dd, ${fill})`,
                    boxShadow: active
                      ? `0 0 0 4px ${fill}33, 0 6px 14px -2px ${fill}55`
                      : `0 0 0 3px ${fill}1f`,
                    transform: active ? 'scale(1.12)' : 'scale(1)',
                  }}
                >
                  {isMature && (
                    <span
                      className="absolute inset-0 rounded-full animate-pulse-ring"
                      style={{ boxShadow: `0 0 0 2px ${fill}66` }}
                    />
                  )}
                  <span className="tnum relative text-[10px] font-bold text-white drop-shadow-sm">
                    {mm}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="flex flex-col gap-6 sm:flex-row">
        <Ovary label="Right Ovary" sizes={right} side="R" />
        <Ovary label="Left Ovary" sizes={left} side="L" />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-ink-100 pt-3.5">
        {[
          { c: '#059669', l: 'Mature (≥16 mm)' },
          { c: '#34D399', l: 'Developing (12–15 mm)' },
          { c: '#A8A29E', l: 'Small (<12 mm)' },
        ].map((k) => (
          <div key={k.l} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: k.c }} />
            <span className="text-[11.5px] text-ink-500">{k.l}</span>
          </div>
        ))}
        <span className="ml-auto text-[11.5px] text-ink-400">Bubble size proportional to diameter</span>
      </div>
    </div>
  );
}

/* ============================================================
   MULTI-SERIES GROWTH — follicle / hormone progression
   ============================================================ */
export function GrowthChart({
  series,
  xLabels,
  height = 200,
  yUnit = '',
}: {
  series: { name: string; color: string; values: number[] }[];
  xLabels: string[];
  height?: number;
  yUnit?: string;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const padL = 40;
  const padR = 14;
  const padT = 14;
  const padB = 26;
  const w = 620;
  const innerW = w - padL - padR;
  const innerH = height - padT - padB;
  const all = series.flatMap((s) => s.values);
  const max = Math.max(...all) * 1.2;

  const toPath = (values: number[]) =>
    values
      .map((v, i) => {
        const x = padL + (i / (values.length - 1)) * innerW;
        const y = padT + innerH - (v / max) * innerH;
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ height }}>
        {Array.from({ length: 5 }).map((_, i) => {
          const y = padT + (i / 4) * innerH;
          return (
            <g key={i}>
              <line x1={padL} y1={y} x2={w - padR} y2={y} stroke="#E7E5E4" strokeWidth="1" strokeDasharray={i === 4 ? '0' : '3 4'} />
              <text x={padL - 8} y={y + 3.5} textAnchor="end" fontSize="10" fill="#A8A29E" className="tnum">
                {(max - (i / 4) * max).toFixed(0)}
              </text>
            </g>
          );
        })}

        {series.map((s, si) => (
          <g key={s.name}>
            {inView && (
              <path
                d={toPath(s.values)}
                fill="none"
                stroke={s.color}
                strokeWidth="2.25"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="draw-line"
                style={{ ['--len' as string]: 900, animationDelay: `${si * 180}ms` }}
              />
            )}
            {s.values.map((v, i) => {
              const x = padL + (i / (s.values.length - 1)) * innerW;
              const y = padT + innerH - (v / max) * innerH;
              return (
                inView && (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="3.5"
                    fill="#fff"
                    stroke={s.color}
                    strokeWidth="2.25"
                    className="animate-scale-in"
                    style={{ animationDelay: `${0.55 + si * 0.18 + i * 0.08}s` }}
                  />
                )
              );
            })}
          </g>
        ))}

        {xLabels.map((l, i) => {
          const x = padL + (i / (xLabels.length - 1)) * innerW;
          return (
            <text key={i} x={x} y={height - 7} textAnchor="middle" fontSize="10.5" fill="#78716C" fontWeight="500">
              {l}
            </text>
          );
        })}
      </svg>

      <div className="mt-2 flex flex-wrap items-center gap-4">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full" style={{ backgroundColor: s.color }} />
            <span className="text-[11.5px] text-ink-600">{s.name}</span>
          </div>
        ))}
        {yUnit && <span className="ml-auto text-[11px] text-ink-400">{yUnit}</span>}
      </div>
    </div>
  );
}
