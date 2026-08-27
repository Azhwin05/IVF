'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { cn, TONE, initialsOf } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, Avatar, SectionTitle, Input, Select, Skeleton, Modal } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { useAppointments, useCreateAppointment } from '@/lib/api/appointments';
import { usePatients } from '@/lib/api/patients';
import { useDoctors } from '@/lib/api/users';
import { ApiError } from '@/lib/api/client';
import type { AppointmentChannel } from '@/lib/api/types';
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
  AlertTriangle,
} from 'lucide-react';

const STATUS_TONE: Record<string, keyof typeof TONE> = {
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

const STATUS_LABEL: Record<string, string> = {
  registered: 'Registered',
  arrived: 'Arrived',
  waiting: 'Waiting',
  consultation: 'Consultation',
  investigation: 'Investigation',
  billing: 'Billing',
  pharmacy: 'Pharmacy',
  follow_up: 'Follow-up',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No Show',
};

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

const DOCTOR_COLORS = ['#059669', '#0EA5E9', '#8B5CF6', '#F59E0B', '#EC4899', '#78716C'];

function BookingModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { toast } = useApp();
  const patientsQuery = usePatients();
  const doctorsQuery = useDoctors();
  const createAppointment = useCreateAppointment();
  const [patientId, setPatientId] = useState('');
  const [doctorId, setDoctorId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [visitType, setVisitType] = useState('Consultation');
  const [channel, setChannel] = useState<AppointmentChannel>('walk_in');
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setPatientId('');
    setDoctorId('');
    setScheduledAt('');
    setVisitType('Consultation');
    setChannel('walk_in');
    setError(null);
  };

  const submit = () => {
    setError(null);
    createAppointment.mutate(
      { patient_id: patientId, doctor_id: doctorId, scheduled_at: new Date(scheduledAt).toISOString(), visit_type: visitType, channel },
      {
        onSuccess: () => {
          toast({ title: 'Appointment booked', body: 'Added to the clinical schedule.', tone: 'success' });
          reset();
          onClose();
        },
        onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not book the appointment.'),
      }
    );
  };

  return (
    <Modal
      open={open}
      onClose={() => { reset(); onClose(); }}
      title="Book Appointment"
      subtitle="Schedule a new visit on the clinical calendar"
      footer={
        <>
          <Button onClick={() => { reset(); onClose(); }}>Cancel</Button>
          <Button
            variant="primary"
            loading={createAppointment.isPending}
            disabled={!patientId || !doctorId || !scheduledAt || !visitType}
            onClick={submit}
          >
            {createAppointment.isPending ? 'Booking…' : 'Book Appointment'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Select label="Patient" value={patientId} onChange={(e) => setPatientId(e.target.value)}>
          <option value="">Select a patient…</option>
          {(patientsQuery.data ?? []).map((p) => (
            <option key={p.id} value={p.id}>{p.full_name} — {p.uhid}</option>
          ))}
        </Select>
        <Select label="Doctor" value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
          <option value="">Select a doctor…</option>
          {(doctorsQuery.data ?? []).map((d) => (
            <option key={d.id} value={d.id}>{d.full_name}</option>
          ))}
        </Select>
        <Input label="Date & Time" type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
        <Input label="Visit Type" value={visitType} onChange={(e) => setVisitType(e.target.value)} />
        <Select label="Channel" value={channel} onChange={(e) => setChannel(e.target.value as AppointmentChannel)}>
          <option value="walk_in">Walk-in</option>
          <option value="phone">Phone</option>
          <option value="online">Online</option>
        </Select>
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
            <p className="text-[12.5px] leading-relaxed text-rose-700">{error}</p>
          </div>
        )}
      </div>
    </Modal>
  );
}

const STATUS_FILTERS = ['All', 'registered', 'arrived', 'waiting', 'consultation', 'investigation', 'billing', 'pharmacy', 'follow_up', 'completed', 'cancelled', 'no_show'];

export function Appointments() {
  const { openPatient } = useApp();
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('All');
  const [doctorFilter, setDoctorFilter] = useState<string | null>(null);
  const [bookingOpen, setBookingOpen] = useState(false);

  const appointmentsQuery = useAppointments();
  const patientsQuery = usePatients();
  const doctorsQuery = useDoctors();
  const loading = appointmentsQuery.isLoading;

  const patientNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of patientsQuery.data ?? []) map[p.id] = p.full_name;
    return map;
  }, [patientsQuery.data]);

  const doctors = doctorsQuery.data ?? [];

  const rows = useMemo(() => {
    let r = appointmentsQuery.data ?? [];
    if (status !== 'All') r = r.filter((b) => b.status === status);
    if (doctorFilter) r = r.filter((b) => b.doctor_id === doctorFilter);
    if (q.trim()) {
      const t = q.toLowerCase();
      r = r.filter(
        (b) => (patientNameById[b.patient_id] ?? '').toLowerCase().includes(t) || b.visit_type.toLowerCase().includes(t)
      );
    }
    return r;
  }, [appointmentsQuery.data, q, status, doctorFilter, patientNameById]);

  const metrics = useMemo(() => {
    const all = appointmentsQuery.data ?? [];
    return {
      total: all.length,
      waiting: all.filter((a) => a.status === 'waiting').length,
      completed: all.filter((a) => a.status === 'completed').length,
      cancelled: all.filter((a) => a.status === 'cancelled').length,
      noShow: all.filter((a) => a.status === 'no_show').length,
      inConsultation: all.filter((a) => a.status === 'consultation').length,
    };
  }, [appointmentsQuery.data]);

  const doctorName = (id: string) => doctors.find((d) => d.id === id)?.full_name ?? 'Unassigned';
  const doctorColor = (id: string) => DOCTOR_COLORS[doctors.findIndex((d) => d.id === id) % DOCTOR_COLORS.length] ?? '#78716C';

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <BookingModal open={bookingOpen} onClose={() => setBookingOpen(false)} />
      <SectionTitle
        eyebrow="Front Desk"
        title="Appointment Management"
        description="Doctor-wise schedules, walk-ins, online bookings and queue — all in one live book"
        action={
          <Button variant="primary" icon={<CalendarPlus className="h-4 w-4" />} onClick={() => setBookingOpen(true)}>
            Book Appointment
          </Button>
        }
      />

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 xl:grid-cols-6">
        <MetricTile label="Total Today" value={metrics.total} icon={CalendarClock} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
        <MetricTile label="In Consultation" value={metrics.inConsultation} icon={Users2} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
        <MetricTile label="Waiting" value={metrics.waiting} icon={Clock3} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
        <MetricTile label="Completed" value={metrics.completed} icon={CheckCircle2} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
        <MetricTile label="Cancelled" value={metrics.cancelled} icon={XCircle} tone="bg-rose-50 text-rose-700 ring-rose-600/12" />
        <MetricTile label="No Shows" value={metrics.noShow} icon={Globe} tone="bg-ink-100 text-ink-600 ring-ink-500/12" />
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
            <p className="tnum text-[11px] text-ink-500">{metrics.total} appointments</p>
          </button>
          {doctors.map((d) => {
            const todayCount = (appointmentsQuery.data ?? []).filter((a) => a.doctor_id === d.id).length;
            return (
              <button
                key={d.id}
                onClick={() => setDoctorFilter(d.id)}
                className={cn(
                  'shrink-0 rounded-xl border px-3.5 py-2.5 text-left transition-all',
                  doctorFilter === d.id ? 'border-brand-400 bg-brand-50/60' : 'border-ink-200/70 bg-white hover:border-ink-300'
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: doctorColor(d.id) }} />
                  <p className="whitespace-nowrap text-[12.5px] font-semibold text-ink-900">{d.full_name}</p>
                </div>
                <p className="text-[11px] text-ink-500">{d.department ?? 'Reproductive Medicine'}</p>
                <p className="tnum mt-0.5 text-[11px] font-medium text-ink-600">{todayCount} today</p>
              </button>
            );
          })}
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
                {s === 'All' ? 'All' : STATUS_LABEL[s]}
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
            {rows.map((b, i) => {
              const patientName = patientNameById[b.patient_id] ?? 'Unknown patient';
              const time = new Date(b.scheduled_at);
              return (
                <button
                  key={b.id}
                  style={{ ['--i' as string]: i }}
                  onClick={() => openPatient(b.patient_id)}
                  className="flex w-full flex-col gap-2 border-b border-ink-100 px-4 py-3.5 text-left last:border-0 transition-colors hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[80px_1.8fr_1.4fr_1fr_1fr_110px] md:items-center md:gap-4"
                >
                  <span className="tnum text-[13px] font-semibold text-ink-900">
                    {time.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true })}
                  </span>
                  <div className="flex items-center gap-3">
                    <Avatar initials={initialsOf(patientName)} size="sm" gradient="from-ink-400 to-ink-600" />
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-medium text-ink-900">{patientName}</p>
                    </div>
                  </div>
                  <span className="text-[12.5px] text-ink-700">{b.visit_type}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: doctorColor(b.doctor_id) }} />
                    <span className="truncate text-[12px] text-ink-600">{doctorName(b.doctor_id).replace('Dr. ', '')}</span>
                  </div>
                  <span className="text-[12px] text-ink-500">{b.channel.replace('_', ' ')}</span>
                  <Badge tone={STATUS_TONE[b.status] ?? 'neutral'} size="sm">
                    {STATUS_LABEL[b.status] ?? b.status}
                  </Badge>
                </button>
              );
            })}
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
