'use client';

import React, { useMemo } from 'react';
import { useApp } from '@/lib/store';
import {
  METRICS,
  CLINICAL_ALERTS,
  ACTIVITY_FEED,
  CYCLE_DISTRIBUTION,
} from '@/lib/data';
import { cn, TONE, formatINR, TODAY } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, Avatar, SectionTitle, Skeleton } from '@/components/ui/primitives';
import { Sparkline, DonutChart } from '@/components/ui/charts';
import { useCountUp } from '@/lib/hooks';
import { useDashboardMetrics, useCycleDistribution } from '@/lib/api/reports';
import { useAppointments } from '@/lib/api/appointments';
import { usePatients } from '@/lib/api/patients';
import {
  CalendarClock,
  Users2,
  Activity,
  IndianRupee,
  Stethoscope,
  BellRing,
  ArrowUpRight,
  ChevronRight,
  FlaskConical,
  Receipt,
  UserPlus,
  FileText,
  Microscope,
  Clock3,
} from 'lucide-react';

function MetricTile({
  icon: Icon,
  metric,
  currency,
  delay,
  accent,
}: {
  icon: any;
  metric: { value: number; label: string; delta: string; trend: number[] };
  currency?: boolean;
  delay: number;
  accent: string;
}) {
  const v = useCountUp(metric.value, 1300);
  const display = currency ? formatINR(Math.round(v), true) : Math.round(v).toLocaleString('en-IN');

  return (
    <Card className="group relative overflow-hidden p-4" interactive>
      <div className="flex items-start justify-between">
        <div
          className={cn(
            'flex h-9 w-9 items-center justify-center rounded-xl ring-1 ring-inset transition-transform duration-300 group-hover:scale-105',
            accent
          )}
        >
          <Icon className="h-[18px] w-[18px]" strokeWidth={1.9} />
        </div>
        <ArrowUpRight className="h-4 w-4 text-ink-300 transition-all duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand-600" />
      </div>

      <p className="tnum tracking-display mt-3.5 text-[28px] font-semibold leading-none text-ink-900">
        {display}
      </p>
      <p className="mt-1.5 text-[12.5px] font-medium text-ink-600">{metric.label}</p>
      <p className="mt-0.5 text-[11px] text-ink-400">{metric.delta}</p>

      <div className="mt-3 -mx-1">
        <Sparkline data={metric.trend} height={28} />
      </div>
    </Card>
  );
}

const APPOINTMENT_STATUS_TONE: Record<string, keyof typeof TONE> = {
  registered: 'scheduled',
  arrived: 'active',
  waiting: 'attention',
  consultation: 'active',
  investigation: 'active',
  billing: 'pending',
  pharmacy: 'pending',
  follow_up: 'scheduled',
  completed: 'completed',
  cancelled: 'cancelled',
  no_show: 'critical',
};

const STAGE_META: Record<string, { label: string; color: string }> = {
  assessment: { label: 'Assessment', color: '#94A3B8' },
  stimulation: { label: 'Stimulation', color: '#10B981' },
  trigger: { label: 'Trigger', color: '#F97316' },
  retrieval: { label: 'Retrieval', color: '#F59E0B' },
  embryology: { label: 'Embryology', color: '#8B5CF6' },
  transfer: { label: 'Transfer', color: '#0EA5E9' },
  pregnancy_followup: { label: 'Follow-up', color: '#EC4899' },
};

export function Dashboard() {
  const { go, toast, user, openPatient } = useApp();
  const displayName = user?.name ?? 'there';

  const dashboardQuery = useDashboardMetrics();
  const cycleDistQuery = useCycleDistribution();
  const appointmentsQuery = useAppointments();
  const patientsQuery = usePatients();
  const loading = dashboardQuery.isLoading;

  const patientNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of patientsQuery.data ?? []) map[p.id] = p.full_name;
    return map;
  }, [patientsQuery.data]);

  const liveMetrics = dashboardQuery.data;
  const metrics = {
    appointments: { ...METRICS.appointments, value: liveMetrics?.appointments_today ?? METRICS.appointments.value },
    waiting: { ...METRICS.waiting, value: liveMetrics?.patients_waiting ?? METRICS.waiting.value },
    cycles: { ...METRICS.cycles, value: liveMetrics?.active_ivf_cycles ?? METRICS.cycles.value },
    collection: {
      ...METRICS.collection,
      value: liveMetrics ? Math.round(liveMetrics.todays_collection_paise / 100) : METRICS.collection.value,
    },
    procedures: METRICS.procedures,
    followups: METRICS.followups,
  };

  const cycleDistribution = (cycleDistQuery.data ?? []).map((c) => ({
    label: STAGE_META[c.stage]?.label ?? c.stage,
    value: c.count,
    color: STAGE_META[c.stage]?.color ?? '#94A3B8',
  }));
  const totalActiveCycles = cycleDistribution.reduce((sum, c) => sum + c.value, 0);

  const todaysAppointments = appointmentsQuery.data ?? [];

  const hour = 9;
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-6 p-4 sm:p-6 lg:p-8">
      {/* ============ HEADER ============ */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <div className="mb-1.5 flex items-center gap-2">
            <span className="h-px w-6 bg-brand-500" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-700">
              {TODAY}
            </span>
          </div>
          <h1 className="tracking-display font-display text-[26px] leading-tight text-ink-900 sm:text-[34px]">
            {greeting}, {displayName.split(' ')[0]} {displayName.split(' ')[1]?.replace('S.', '')}
          </h1>
          <p className="mt-1 text-[13px] text-ink-500 sm:text-[14px]">
            Here is your clinical and operational overview for today.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button icon={<FileText className="h-4 w-4" />} onClick={() => go('reports')}>
            View Reports
          </Button>
          <Button variant="primary" icon={<UserPlus className="h-4 w-4" />} onClick={() => go('registration')}>
            Register Couple
          </Button>
        </div>
      </div>

      {/* ============ METRICS ============ */}
      <div className="grid grid-cols-2 gap-3.5 md:grid-cols-3 xl:grid-cols-6">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="p-4">
                <Skeleton className="h-9 w-9 rounded-xl" />
                <Skeleton className="mt-3.5 h-7 w-20" />
                <Skeleton className="mt-2 h-3 w-24" />
                <Skeleton className="mt-3 h-7 w-full" />
              </Card>
            ))
          : (
            <>
              <MetricTile icon={CalendarClock} metric={metrics.appointments} delay={0} accent="bg-brand-50 text-brand-700 ring-brand-600/12" />
              <MetricTile icon={Users2} metric={metrics.waiting} delay={1} accent="bg-amber-50 text-amber-700 ring-amber-600/12" />
              <MetricTile icon={Activity} metric={metrics.cycles} delay={2} accent="bg-violet-50 text-violet-700 ring-violet-600/12" />
              <MetricTile icon={IndianRupee} metric={metrics.collection} currency delay={3} accent="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
              <MetricTile icon={Stethoscope} metric={metrics.procedures} delay={4} accent="bg-sky-50 text-sky-700 ring-sky-600/12" />
              <MetricTile icon={BellRing} metric={metrics.followups} delay={5} accent="bg-rose-50 text-rose-700 ring-rose-600/12" />
            </>
          )}
      </div>

      {/* ============ MAIN GRID ============ */}
      <div className="grid gap-5 xl:grid-cols-3">
        {/* Schedule */}
        <Card className="xl:col-span-2">
          <CardHeader
            icon={<CalendarClock className="h-4 w-4" />}
            title="Today's Clinical Schedule"
            subtitle={`${todaysAppointments.length} appointments · ${metrics.waiting.value} patient${metrics.waiting.value === 1 ? '' : 's'} currently waiting`}
            action={
              <Button size="sm" variant="ghost" iconRight={<ChevronRight className="h-3.5 w-3.5" />} onClick={() => go('patients')}>
                All patients
              </Button>
            }
          />
          <div className="stagger px-2 pb-2">
            {todaysAppointments.length === 0 && !appointmentsQuery.isLoading && (
              <p className="px-3 py-6 text-center text-[12.5px] text-ink-400">No appointments scheduled for today.</p>
            )}
            {todaysAppointments.map((a, i) => {
              const patientName = patientNameById[a.patient_id] ?? 'Unknown patient';
              const initials = patientName.split(' ').filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase();
              const tone = APPOINTMENT_STATUS_TONE[a.status] ?? 'neutral';
              const time = new Date(a.scheduled_at);
              return (
                <button
                  key={a.id}
                  style={{ ['--i' as string]: i }}
                  onClick={() => openPatient(a.patient_id)}
                  className="group flex w-full items-center gap-3.5 rounded-xl px-3 py-3 text-left transition-colors hover:bg-ink-50"
                >
                  <div className="w-[52px] shrink-0 text-center">
                    <p className="tnum text-[14px] font-semibold text-ink-900">
                      {time.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: false })}
                    </p>
                    <p className="text-[10px] uppercase tracking-wide text-ink-400">
                      {time.getHours() < 12 ? 'AM' : 'PM'}
                    </p>
                  </div>

                  <div className={cn('h-9 w-[3px] shrink-0 rounded-full', TONE[tone].solid)} />

                  <Avatar initials={initials} size="sm" gradient="from-ink-400 to-ink-600" />

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13.5px] font-medium text-ink-900">{patientName}</p>
                    <p className="truncate text-[12px] text-ink-500">
                      {a.visit_type} · <span className="text-ink-400">{a.channel.replace('_', ' ')}</span>
                    </p>
                  </div>

                  <Badge tone={tone} size="sm">
                    {a.status.replace('_', ' ')}
                  </Badge>
                  <ChevronRight className="h-4 w-4 shrink-0 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
                </button>
              );
            })}
          </div>
        </Card>

        {/* Attention */}
        <Card>
          <CardHeader
            icon={<BellRing className="h-4 w-4" />}
            title="Clinical Attention Required"
            subtitle="8 items need your review"
          />
          <div className="stagger space-y-2 px-4 pb-4">
            {CLINICAL_ALERTS.map((al, i) => (
              <div
                key={al.id}
                style={{ ['--i' as string]: i }}
                className={cn(
                  'lift cursor-pointer rounded-xl border p-3.5 transition-colors',
                  TONE[al.tone].bg,
                  'border-transparent hover:border-current/10'
                )}
                onClick={() => {
                  if (al.id === 'AL-1') go('monitoring');
                  else if (al.id === 'AL-4') go('cryostorage');
                  else toast({ title: al.title, body: al.detail, tone: 'info' });
                }}
              >
                <div className="flex items-start gap-2.5">
                  <span
                    className={cn(
                      'tnum mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[12px] font-bold text-white',
                      TONE[al.tone].solid
                    )}
                  >
                    {al.count}
                  </span>
                  <div className="min-w-0">
                    <p className={cn('text-[13px] font-semibold leading-snug', TONE[al.tone].text)}>
                      {al.title}
                    </p>
                    <p className="mt-1 text-[11.5px] leading-relaxed text-ink-600">{al.detail}</p>
                    <span className={cn('mt-2 inline-flex items-center gap-1 text-[11.5px] font-medium', TONE[al.tone].text)}>
                      {al.action}
                      <ChevronRight className="h-3 w-3" />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ============ SECOND ROW ============ */}
      <div className="grid gap-5 xl:grid-cols-3">
        {/* Cycle distribution */}
        <Card>
          <CardHeader
            icon={<Activity className="h-4 w-4" />}
            title="Active IVF Cycle Distribution"
            subtitle={`${totalActiveCycles} cycle${totalActiveCycles === 1 ? '' : 's'} across the treatment pipeline`}
          />
          <div className="px-5 pb-5">
            {cycleDistribution.length > 0 ? (
              <DonutChart data={cycleDistribution} centerLabel="Active cycles" size={168} />
            ) : (
              <DonutChart
                data={CYCLE_DISTRIBUTION.map((c) => ({ label: c.stage, value: c.count, color: c.color }))}
                centerLabel="Active cycles"
                size={168}
              />
            )}
          </div>
        </Card>

        {/* Activity */}
        <Card>
          <CardHeader
            icon={<Clock3 className="h-4 w-4" />}
            title="Recent Activity"
            subtitle="Live clinical and operational events"
            action={<Badge tone="active" size="sm">Live</Badge>}
          />
          <div className="stagger px-4 pb-4">
            {ACTIVITY_FEED.map((a, i) => {
              const iconMap: Record<string, any> = {
                lab: Activity,
                embryo: Microscope,
                billing: Receipt,
                clinical: Stethoscope,
                registration: UserPlus,
              };
              const Icon = iconMap[a.kind] ?? FileText;
              return (
                <div key={a.id} style={{ ['--i' as string]: i }} className="relative flex gap-3 pb-4 last:pb-0">
                  {i < ACTIVITY_FEED.length - 1 && (
                    <span className="absolute left-[13px] top-7 h-full w-px bg-ink-200" />
                  )}
                  <div className="relative z-10 flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full bg-white ring-1 ring-ink-200">
                    <Icon className="h-3.5 w-3.5 text-ink-500" />
                  </div>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-[12.5px] leading-snug text-ink-700">
                      <span className="font-semibold text-ink-900">{a.actor}</span> {a.action}
                    </p>
                    <p className="mt-0.5 text-[11px] text-ink-400">{a.time}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Quick access */}
        <Card>
          <CardHeader
            icon={<FlaskConical className="h-4 w-4" />}
            title="Jump Into a Workflow"
            subtitle="Continue where the clinical team left off"
          />
          <div className="stagger space-y-2 px-4 pb-4">
            {[
              { label: 'Priya Raman — Day 8 Monitoring', desc: 'Awaiting your clinical review', icon: Activity, screen: 'monitoring' as const, tone: 'attention' as const },
              { label: 'Embryology Workspace', desc: '5 blastocysts graded and ready', icon: Microscope, screen: 'embryology' as const, tone: 'active' as const },
              { label: 'Embryo Transfer — E-01', desc: 'Safety checklist pending sign-off', icon: FlaskConical, screen: 'transfer' as const, tone: 'scheduled' as const },
              { label: 'Billing & Packages', desc: '₹75,000 outstanding on 1 package', icon: Receipt, screen: 'billing' as const, tone: 'pending' as const },
            ].map((q, i) => {
              const Icon = q.icon;
              return (
                <button
                  key={q.label}
                  style={{ ['--i' as string]: i }}
                  onClick={() => go(q.screen)}
                  className="lift group flex w-full items-center gap-3 rounded-xl border border-ink-200/70 bg-white p-3 text-left hover:border-brand-300/70 hover:shadow-lift"
                >
                  <div className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-lg', TONE[q.tone].bg, TONE[q.tone].text)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-medium text-ink-900">{q.label}</p>
                    <p className="truncate text-[11.5px] text-ink-500">{q.desc}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
                </button>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
