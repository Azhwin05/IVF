'use client';

import React, { useMemo, useState } from 'react';
import { useApp } from '@/lib/store';
import {
  REVENUE_TREND,
  MANAGEMENT_KPIS,
  OUTCOME_BREAKDOWN,
  OPERATIONAL_METRICS,
  DOCTOR_PERFORMANCE,
  CYCLE_DISTRIBUTION,
} from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle } from '@/components/ui/primitives';
import { AreaChart, BarChart, DonutChart, ProgressRing } from '@/components/ui/charts';
import { useCountUp } from '@/lib/hooks';
import { useCycleDistribution, useDoctorPerformance, useOutcomes, useRevenueTrend } from '@/lib/api/reports';
import { useDoctors } from '@/lib/api/users';
import { BarChart3, Download, TrendingUp, TrendingDown, Activity, IndianRupee, Users2, Stethoscope } from 'lucide-react';

const OUTCOME_LABEL: Record<string, string> = {
  clinical_pregnancy: 'Clinical Pregnancy',
  biochemical: 'Biochemical Only',
  not_pregnant: 'Not Pregnant',
  live_birth: 'Live Birth',
  miscarriage: 'Miscarriage',
};
const OUTCOME_COLOR: Record<string, string> = {
  clinical_pregnancy: '#10B981',
  biochemical: '#F59E0B',
  not_pregnant: '#D6D3D1',
  live_birth: '#059669',
  miscarriage: '#EF4444',
};

function KpiTile({ k, i }: { k: (typeof MANAGEMENT_KPIS)[number]; i: number }) {
  const v = useCountUp(k.value, 1200);
  return (
    <Card className="p-4" style={{ ['--i' as string]: i }}>
      <p className="text-[12.5px] font-medium uppercase tracking-[0.06em] text-ink-400">{k.label}</p>
      <div className="mt-1.5 flex items-end gap-2">
        <span className="tnum tracking-display text-[30px] font-semibold leading-none text-ink-900">
          {Math.round(v)}
          {k.suffix ?? ''}
        </span>
        <span
          className={cn(
            'mb-1 flex items-center gap-0.5 text-[12.5px] font-semibold',
            k.positive ? 'text-brand-700' : 'text-rose-600'
          )}
        >
          {k.positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          {k.delta}
        </span>
      </div>
    </Card>
  );
}

function monthRangeYearAgo() {
  const now = new Date();
  const from = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
  return { from: from.toISOString().slice(0, 10), to: now.toISOString().slice(0, 10) };
}

export function Reports() {
  const { toast } = useApp();
  const [range, setRange] = useState('6 months');
  const { from, to } = monthRangeYearAgo();

  const cycleDistQuery = useCycleDistribution();
  const outcomesQuery = useOutcomes(from, to);
  const revenueQuery = useRevenueTrend(6);
  const doctorPerfQuery = useDoctorPerformance();
  const doctorsQuery = useDoctors();

  const hasRealRevenue = (revenueQuery.data ?? []).length > 0;
  const hasRealOutcomes = (outcomesQuery.data ?? []).length > 0;
  const hasRealCycles = (cycleDistQuery.data ?? []).length > 0;
  const hasRealDoctorPerf = (doctorPerfQuery.data ?? []).length > 0;

  const doctorNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const d of doctorsQuery.data ?? []) map[d.id] = d.full_name;
    return map;
  }, [doctorsQuery.data]);

  const revenueTrend = hasRealRevenue
    ? (revenueQuery.data ?? []).map((r) => ({ month: r.month, revenue: Math.round(r.revenue_paise / 100 / 100000 * 10) / 10, cycles: 0 }))
    : REVENUE_TREND;

  const totalOutcomes = (outcomesQuery.data ?? []).reduce((s, o) => s + o.count, 0);
  const outcomeBreakdown = hasRealOutcomes
    ? (outcomesQuery.data ?? []).map((o) => ({
        label: OUTCOME_LABEL[o.outcome] ?? o.outcome,
        value: totalOutcomes > 0 ? Math.round((o.count / totalOutcomes) * 100) : 0,
        color: OUTCOME_COLOR[o.outcome] ?? '#94A3B8',
      }))
    : OUTCOME_BREAKDOWN;
  const clinicalPregnancyPct = hasRealOutcomes
    ? outcomeBreakdown.find((o) => o.label === 'Clinical Pregnancy')?.value ?? 0
    : 62;

  const cycleDistribution = hasRealCycles
    ? (cycleDistQuery.data ?? []).map((c) => ({ stage: c.stage.replace(/_/g, ' '), count: c.count, color: '#059669' }))
    : CYCLE_DISTRIBUTION;

  const doctorPerformance = hasRealDoctorPerf
    ? (doctorPerfQuery.data ?? []).map((d) => ({
        name: doctorNameById[d.doctor_id] ?? 'Unknown doctor',
        consultations: d.consultations,
        cycles: null as number | null,
        transfers: null as number | null,
        success: null as number | null,
      }))
    : DOCTOR_PERFORMANCE.map((d) => ({ ...d, cycles: d.cycles as number | null, transfers: d.transfers as number | null, success: d.success as number | null }));

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <SectionTitle
          eyebrow="Management"
          title="Reports & Analytics"
          description="Clinical performance, operational throughput and revenue for Dr. Archana IVF & Women Centre"
        />
        <div className="flex items-center gap-2">
          <div className="scroll-area flex flex-1 gap-1 overflow-x-auto rounded-lg bg-ink-100 p-1 lg:flex-none">
            {['30 days', '3 months', '6 months', 'Year'].map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={cn(
                  'shrink-0 rounded-md px-3 py-1.5 text-[13.5px] font-medium transition-all',
                  range === r ? 'bg-white text-ink-900 shadow-card' : 'text-ink-500 hover:text-ink-800'
                )}
              >
                {r}
              </button>
            ))}
          </div>
          <Button
            icon={<Download className="h-4 w-4" />}
            onClick={() => toast({ title: 'Report exported', body: 'July operational summary exported as PDF.', tone: 'success' })}
          >
            Export
          </Button>
        </div>
      </div>

      {/* ============ CLINICAL KPIS ============ */}
      <div className="stagger grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        {MANAGEMENT_KPIS.map((k, i) => (
          <KpiTile key={k.label} k={k} i={i} />
        ))}
      </div>

      {/* ============ REVENUE ============ */}
      <div className="grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            icon={<IndianRupee className="h-4 w-4" />}
            title="Revenue Trend"
            subtitle={hasRealRevenue ? 'Monthly collections in lakhs — last 6 months' : 'Monthly collections in lakhs — last 6 months'}
            action={!hasRealRevenue ? <Badge tone="completed">+12.4% MoM</Badge> : undefined}
          />
          <div className="px-5 pb-5">
            <AreaChart
              data={revenueTrend.map((r) => ({ label: r.month, value: r.revenue }))}
              valueLabel=" L"
              height={240}
            />
          </div>
        </Card>

        <Card>
          <CardHeader icon={<Activity className="h-4 w-4" />} title="Treatment Outcomes" subtitle={hasRealOutcomes ? 'Cycles reaching outcome in the last 12 months' : 'Cycles reaching outcome this quarter'} />
          <div className="px-5 pb-5">
            <DonutChart
              data={outcomeBreakdown}
              centerLabel="Clinical pregnancy"
              centerValue={`${clinicalPregnancyPct}%`}
              size={168}
            />
          </div>
        </Card>
      </div>

      {/* ============ VOLUME + DISTRIBUTION ============ */}
      <div className="grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            icon={<BarChart3 className="h-4 w-4" />}
            title="IVF Cycle Volume"
            subtitle="Cycles initiated per month"
          />
          <div className="px-5 pb-5">
            <BarChart data={REVENUE_TREND.map((r) => ({ label: r.month, value: r.cycles }))} height={200} />
          </div>
        </Card>

        <Card>
          <CardHeader icon={<Users2 className="h-4 w-4" />} title="Active Cycle Pipeline" subtitle={hasRealCycles ? `Where the ${cycleDistribution.reduce((s, c) => s + c.count, 0)} live cycles sit today` : 'Where the 12 live cycles sit today'} />
          <div className="px-5 pb-5">
            <DonutChart
              data={cycleDistribution.map((c) => ({ label: c.stage, value: c.count, color: c.color }))}
              centerLabel="Active cycles"
              size={168}
            />
          </div>
        </Card>
      </div>

      {/* ============ OPERATIONS ============ */}
      <Card>
        <CardHeader icon={<TrendingUp className="h-4 w-4" />} title="Operational Metrics" subtitle="Month-to-date performance across the hospital" />
        <div className="stagger grid gap-3 px-5 pb-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {OPERATIONAL_METRICS.map((m, i) => (
            <div
              key={m.label}
              style={{ ['--i' as string]: i }}
              className="rounded-xl border border-ink-200/70 bg-gradient-to-b from-white to-ink-50/50 p-3.5"
            >
              <p className="text-[12px] font-medium uppercase tracking-[0.06em] text-ink-400">
                {m.label}
              </p>
              <p className="tnum mt-1.5 text-[20px] font-semibold leading-none text-ink-900">{m.value}</p>
              <p
                className={cn(
                  'mt-1.5 flex items-center gap-0.5 text-[12px] font-semibold',
                  m.positive ? 'text-brand-700' : 'text-amber-600'
                )}
              >
                {m.positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {m.delta}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* ============ DOCTOR PERFORMANCE ============ */}
      <div className="grid gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader icon={<Stethoscope className="h-4 w-4" />} title="Consultant Performance" subtitle="Volume and outcome by treating clinician" />
          <div className="overflow-hidden">
            <div className="hidden grid-cols-[2fr_1fr_1fr_1fr_1.2fr] gap-4 border-y border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
              {['Consultant', 'Consults', 'Cycles', 'Transfers', 'Success Rate'].map((h) => (
                <span key={h} className="text-[12px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                  {h}
                </span>
              ))}
            </div>
            <div className="stagger">
              {doctorPerformance.map((d, i) => (
                <div
                  key={d.name}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-col gap-2.5 border-b border-ink-100 px-4 py-3.5 last:border-0 hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[2fr_1fr_1fr_1fr_1.2fr] md:items-center md:gap-4"
                >
                  <span className="text-[14px] font-medium text-ink-900">{d.name}</span>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 md:contents">
                    <span className="tnum text-[12.5px] text-ink-500 md:text-[14px] md:text-ink-700">
                      {d.consultations} consults
                    </span>
                    <span className="tnum text-[12.5px] text-ink-500 md:text-[14px] md:text-ink-700">
                      {d.cycles !== null ? `${d.cycles} cycles` : '—'}
                    </span>
                    <span className="tnum text-[12.5px] text-ink-500 md:text-[14px] md:text-ink-700">
                      {d.transfers !== null ? `${d.transfers} transfers` : '—'}
                    </span>
                  </div>
                  {d.success !== null ? (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-[width] duration-[1200ms] ease-spring"
                          style={{ width: `${d.success}%`, transitionDelay: `${i * 120}ms` }}
                        />
                      </div>
                      <span className="tnum text-[13px] font-semibold text-ink-900">{d.success}%</span>
                    </div>
                  ) : (
                    <span className="text-[12.5px] text-ink-400">Not available yet</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Quality Indicators" subtitle="Benchmarked against national averages" />
          <div className="grid grid-cols-2 gap-4 px-5 pb-5">
            <ProgressRing value={62} label="Clinical pregnancy" />
            <ProgressRing value={73} label="Fertilisation rate" color="#8B5CF6" />
            <ProgressRing value={46} label="Live birth rate" color="#0EA5E9" />
            <ProgressRing value={4} label="OHSS incidence" color="#F59E0B" />
          </div>
        </Card>
      </div>
    </div>
  );
}
