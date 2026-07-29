'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { APPOINTMENT_BOOK, APPOINTMENT_METRICS, DOCTORS } from '@/lib/data';
import { cn, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, Avatar, SectionTitle, Input, Skeleton } from '@/components/ui/primitives';
import { useCountUp, useSimulatedLoad } from '@/lib/hooks';
import {
  CalendarClock,
  CalendarPlus,
  Search,
  Users2,
  CheckCircle2,
  Clock3,
  XCircle,
  Globe,
  ChevronRight,
} from 'lucide-react';

function MetricTile({ label, value, icon: Icon, tone }: { label: string; value: number; icon: any; tone: string }) {
  const v = useCountUp(value, 1000);
  return (
    <Card className="p-4">
      <div className={cn('flex h-9 w-9 items-center justify-center rounded-xl ring-1 ring-inset', tone)}>
        <Icon className="h-[18px] w-[18px]" />
      </div>
      <p className="tnum tracking-display mt-3 text-[24px] font-semibold leading-none text-ink-900">
        {Math.round(v)}
      </p>
      <p className="mt-1.5 text-[12px] font-medium text-ink-600">{label}</p>
    </Card>
  );
}

const STATUS_FILTERS = ['All', 'Waiting', 'Confirmed', 'In Progress', 'Completed', 'Cancelled', 'No Show'];

export function Appointments() {
  const { toast } = useApp();
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('All');
  const [doctorFilter, setDoctorFilter] = useState<string | null>(null);
  const loading = useSimulatedLoad([status, doctorFilter], 300);

  const rows = useMemo(() => {
    let r = APPOINTMENT_BOOK;
    if (status !== 'All') r = r.filter((b) => b.status === status);
    if (doctorFilter) r = r.filter((b) => b.doctorId === doctorFilter);
    if (q.trim()) {
      const t = q.toLowerCase();
      r = r.filter((b) => b.patient.toLowerCase().includes(t) || b.type.toLowerCase().includes(t));
    }
    return r;
  }, [q, status, doctorFilter]);

  const doctorName = (id: string) => DOCTORS.find((d) => d.id === id)?.name ?? id;
  const doctorColor = (id: string) => DOCTORS.find((d) => d.id === id)?.color ?? '#78716C';

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Front Desk"
        title="Appointment Management"
        description="Doctor-wise schedules, walk-ins, online bookings and queue — all in one live book"
        action={
          <Button
            variant="primary"
            icon={<CalendarPlus className="h-4 w-4" />}
            onClick={() => toast({ title: 'New appointment', body: 'Booking form opened for a new patient visit.', tone: 'info' })}
          >
            Book Appointment
          </Button>
        }
      />

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 xl:grid-cols-6">
        <MetricTile label="Total Today" value={APPOINTMENT_METRICS.totalToday} icon={CalendarClock} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
        <MetricTile label="Confirmed" value={APPOINTMENT_METRICS.confirmed} icon={CheckCircle2} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
        <MetricTile label="Waiting" value={APPOINTMENT_METRICS.waiting} icon={Clock3} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
        <MetricTile label="Online Bookings" value={APPOINTMENT_METRICS.onlineBookings} icon={Globe} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
        <MetricTile label="Cancelled" value={APPOINTMENT_METRICS.cancelled} icon={XCircle} tone="bg-rose-50 text-rose-700 ring-rose-600/12" />
        <MetricTile label="No Shows" value={APPOINTMENT_METRICS.noShow} icon={Users2} tone="bg-ink-100 text-ink-600 ring-ink-500/12" />
      </div>

      {/* Doctor schedule strip */}
      <Card className="p-3">
        <div className="scroll-area flex gap-2 overflow-x-auto">
          <button
            onClick={() => setDoctorFilter(null)}
            className={cn(
              'shrink-0 rounded-xl border px-3.5 py-2.5 text-left transition-all',
              !doctorFilter ? 'border-brand-400 bg-brand-50/60' : 'border-ink-200/70 bg-white hover:border-ink-300'
            )}
          >
            <p className="text-[12.5px] font-semibold text-ink-900">All Doctors</p>
            <p className="tnum text-[11px] text-ink-500">{APPOINTMENT_METRICS.totalToday} appointments</p>
          </button>
          {DOCTORS.map((d) => (
            <button
              key={d.id}
              onClick={() => setDoctorFilter(d.id)}
              className={cn(
                'shrink-0 rounded-xl border px-3.5 py-2.5 text-left transition-all',
                doctorFilter === d.id ? 'border-brand-400 bg-brand-50/60' : 'border-ink-200/70 bg-white hover:border-ink-300'
              )}
            >
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: d.color }} />
                <p className="whitespace-nowrap text-[12.5px] font-semibold text-ink-900">{d.name}</p>
              </div>
              <p className="text-[11px] text-ink-500">{d.specialty}</p>
              <p className="tnum mt-0.5 text-[11px] font-medium text-ink-600">{d.todayCount} today</p>
            </button>
          ))}
        </div>
      </Card>

      {/* Controls */}
      <Card className="p-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="lg:min-w-[240px] lg:flex-1">
            <Input placeholder="Search patient or visit type…" icon={<Search className="h-3.5 w-3.5" />} value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div className="scroll-area flex min-w-0 gap-1 overflow-x-auto rounded-lg bg-ink-100 p-1">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={cn(
                  'shrink-0 rounded-md px-3 py-1.5 text-[12.5px] font-medium transition-all',
                  status === s ? 'bg-white text-ink-900 shadow-card' : 'text-ink-500 hover:text-ink-800'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Book */}
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="flex items-center gap-4 p-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3.5 w-40" />
                <Skeleton className="h-3 w-56" />
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="overflow-hidden">
          <div className="hidden grid-cols-[80px_1.8fr_1.4fr_1fr_1fr_110px] items-center gap-4 border-b border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
            {['Time', 'Patient', 'Visit Type', 'Doctor', 'Channel', 'Status'].map((h) => (
              <span key={h} className="text-[10.5px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                {h}
              </span>
            ))}
          </div>
          <div className="stagger">
            {rows.map((b, i) => (
              <div
                key={b.id}
                style={{ ['--i' as string]: i }}
                className="flex flex-col gap-2 border-b border-ink-100 px-4 py-3.5 last:border-0 transition-colors hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[80px_1.8fr_1.4fr_1fr_1fr_110px] md:items-center md:gap-4"
              >
                <span className="tnum text-[13px] font-semibold text-ink-900">{b.time}</span>
                <div className="flex items-center gap-3">
                  <Avatar initials={b.initials} size="sm" gradient="from-ink-400 to-ink-600" />
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-medium text-ink-900">{b.patient}</p>
                    {b.patientId && <p className="tnum truncate text-[11px] text-ink-400">{b.patientId}</p>}
                  </div>
                </div>
                <span className="text-[12.5px] text-ink-700">{b.type}</span>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: doctorColor(b.doctorId) }} />
                  <span className="truncate text-[12px] text-ink-600">{doctorName(b.doctorId).replace('Dr. ', '')}</span>
                </div>
                <span className="text-[12px] text-ink-500">{b.channel}</span>
                <Badge tone={b.tone} size="sm">
                  {b.status}
                </Badge>
              </div>
            ))}
          </div>
          {rows.length === 0 && (
            <div className="px-5 py-16 text-center">
              <p className="text-[14px] font-medium text-ink-700">No appointments match your filters</p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
