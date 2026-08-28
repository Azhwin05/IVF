'use client';

import React, { useState, useEffect } from 'react';
import { useApp } from '@/lib/store';
import { MONITORING_HISTORY, MEDICATIONS, HORMONE_REFERENCE, PATIENT } from '@/lib/data';
import { cn, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, InfoNote, ProgressBar } from '@/components/ui/primitives';
import { FollicleMap, GrowthChart } from '@/components/ui/charts';
import { PatientHeader } from './Workspace';
import { useCoupleForPatient } from '@/lib/api/patients';
import { useActiveCycle, useReviewMonitoringVisit, type MonitoringVisitOut } from '@/lib/api/ivf';
import {
  Activity,
  Pill,
  FlaskConical,
  Stethoscope,
  Save,
  CalendarPlus,
  Ruler,
  AlertTriangle,
  Check,
} from 'lucide-react';

/** Adapts a real MonitoringVisitOut to the shape the existing UI below
 * (FollicleMap, GrowthChart, hormone panel) was built around, so none of
 * that presentation code needed to change. */
function toVisitViewModel(v: MonitoringVisitOut) {
  return {
    day: v.cycle_day,
    date: new Date(v.visit_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }),
    right: v.right_follicles_mm,
    left: v.left_follicles_mm,
    endometrium: v.endometrium_mm,
    estradiol: v.estradiol_pg_ml ?? 0,
    lh: v.lh_miu_ml ?? 0,
    progesterone: v.progesterone_ng_ml ?? 0,
    note: v.doctor_note ?? '',
    reviewed: !!v.reviewed_by_id,
    id: v.id,
  };
}

export function Monitoring() {
  const { toast, selectedPatientId } = useApp();
  const coupleQuery = useCoupleForPatient(selectedPatientId);
  const cycleQuery = useActiveCycle(coupleQuery.data?.id ?? null);
  const reviewVisit = useReviewMonitoringVisit();

  const realVisits = cycleQuery.data?.monitoring_visits ?? [];
  const hasRealData = realVisits.length > 0;
  const history = hasRealData
    ? [...realVisits].sort((a, b) => a.cycle_day - b.cycle_day).map(toVisitViewModel)
    : MONITORING_HISTORY;

  const [dayIdx, setDayIdx] = useState(history.length - 1);
  const [note, setNote] = useState(history[history.length - 1]?.note ?? '');
  const [saved, setSaved] = useState(false);

  // Once real visits load in, snap the selection to the latest one instead
  // of staying pinned at whatever index the static fixture defaulted to.
  useEffect(() => {
    if (hasRealData) {
      setDayIdx(history.length - 1);
      setNote(history[history.length - 1]?.note ?? '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasRealData, realVisits.length]);

  const visit = history[dayIdx] ?? history[history.length - 1];
  const allFollicles = [...visit.right, ...visit.left];
  const mature = allFollicles.filter((f) => f >= 16).length;
  const lead = allFollicles.length ? Math.max(...allFollicles) : 0;

  const save = () => {
    if (hasRealData && 'id' in visit) {
      reviewVisit.mutate(
        { visitId: (visit as ReturnType<typeof toVisitViewModel>).id, doctorNote: note },
        {
          onSuccess: () => {
            setSaved(true);
            toast({ title: 'Clinical review saved', body: 'Signed off and recorded in the audit trail.', tone: 'success' });
            setTimeout(() => setSaved(false), 2600);
          },
          onError: () => toast({ title: 'Could not save review', body: 'Please try again.', tone: 'error' }),
        }
      );
      return;
    }
    setSaved(true);
    toast({
      title: 'Clinical review saved',
      body: `Saved to ${PATIENT.name}'s treatment timeline and recorded in the audit trail.`,
      tone: 'success',
    });
    setTimeout(() => setSaved(false), 2600);
  };

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <PatientHeader compact />

      {!hasRealData && !cycleQuery.isLoading && (
        <InfoNote tone="neutral" icon={<Activity className="h-4 w-4" />}>
          {coupleQuery.data
            ? 'No monitoring visits recorded yet for this cycle — showing the demo reference data below.'
            : 'This patient has no linked couple/cycle record yet — showing demo reference data below.'}
        </InfoNote>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <SectionTitle
          eyebrow={cycleQuery.data ? `Cycle ${cycleQuery.data.cycle_number}` : `Cycle ${PATIENT.cycleId}`}
          title={`Ovarian Stimulation — Day ${visit.day}`}
          description={`Monitoring recorded ${visit.date} · ${cycleQuery.data?.protocol ?? PATIENT.protocol}`}
        />
        {/* Day switcher */}
        <div className="flex shrink-0 gap-1 rounded-lg bg-ink-100 p-1">
          {history.map((m, i) => (
            <button
              key={m.day}
              onClick={() => {
                setDayIdx(i);
                setNote(m.note);
              }}
              className={cn(
                'tnum rounded-md px-3.5 py-1.5 text-[13.5px] font-medium transition-all',
                dayIdx === i ? 'bg-white text-ink-900 shadow-card' : 'text-ink-500 hover:text-ink-800'
              )}
            >
              Day {m.day}
              {!m.reviewed && <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-amber-500" />}
            </button>
          ))}
        </div>
      </div>

      {!visit.reviewed && (
        <InfoNote tone="amber" icon={<AlertTriangle className="h-4 w-4" />}>
          This monitoring record has not yet been signed off. Review the findings below and save your
          clinical assessment to advance the cycle.
        </InfoNote>
      )}

      <div className="grid gap-5 xl:grid-cols-3">
        {/* ============ LEFT — FOLLICLES ============ */}
        <div className="min-w-0 space-y-5 xl:col-span-2">
          <Card>
            <CardHeader
              icon={<Activity className="h-4 w-4" />}
              title="Follicle Monitoring"
              subtitle={`${allFollicles.length} follicles tracked · ${mature} mature · lead follicle ${lead} mm`}
              action={<Badge tone={mature >= 3 ? 'completed' : 'attention'}>{mature >= 3 ? 'Trigger criteria approaching' : 'Continue stimulation'}</Badge>}
            />
            <div className="px-5 pb-5">
              <FollicleMap key={visit.day} right={visit.right} left={visit.left} />
            </div>
          </Card>

          <div className="grid gap-5 sm:grid-cols-2">
            {/* Endometrium */}
            <Card>
              <CardHeader icon={<Ruler className="h-4 w-4" />} title="Endometrium" subtitle="Trilaminar pattern" />
              <div className="px-5 pb-5">
                <div className="flex items-end gap-2">
                  <span className="tnum tracking-display text-[42px] font-semibold leading-none text-ink-900">
                    {visit.endometrium}
                  </span>
                  <span className="mb-1.5 text-[14px] text-ink-400">mm</span>
                </div>
                <div className="mt-4">
                  <div className="mb-1.5 flex justify-between text-[12.5px]">
                    <span className="text-ink-500">Receptivity threshold</span>
                    <span className="tnum font-medium text-ink-700">≥ 7 mm</span>
                  </div>
                  <ProgressBar value={(visit.endometrium / 12) * 100} height={8} />
                  <div className="mt-1.5 flex justify-between text-[12px] text-ink-400">
                    <span>0</span>
                    <span>12 mm</span>
                  </div>
                </div>
                <div className="mt-3">
                  <Badge tone={visit.endometrium >= 7 ? 'completed' : 'attention'} size="sm">
                    {visit.endometrium >= 7 ? 'Adequate thickness' : 'Below threshold'}
                  </Badge>
                </div>
              </div>
            </Card>

            {/* Medication */}
            <Card>
              <CardHeader icon={<Pill className="h-4 w-4" />} title="Active Medication" subtitle="Current stimulation regimen" />
              <div className="space-y-2 px-5 pb-5">
                {MEDICATIONS.filter((m) => m.status === 'Active').map((m) => (
                  <div key={m.name} className="rounded-xl border border-brand-200/70 bg-brand-50/50 p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-[14.5px] font-semibold text-ink-900">{m.name}</p>
                      <Badge tone="active" size="sm">
                        {m.status}
                      </Badge>
                    </div>
                    <p className="tnum mt-1 text-[13.5px] text-ink-600">
                      {m.dose} · {m.route}
                    </p>
                    <p className="mt-0.5 text-[12px] text-ink-400">Started {m.since}</p>
                  </div>
                ))}
                <Button
                  size="sm"
                  className="w-full"
                  icon={<Pill className="h-3.5 w-3.5" />}
                  onClick={() => toast({ title: 'Medication updated', body: 'Gonal-F 225 IU continued for Day 9.', tone: 'success' })}
                >
                  Adjust dosage
                </Button>
              </div>
            </Card>
          </div>

          {/* Growth trend */}
          <Card>
            <CardHeader
              icon={<FlaskConical className="h-4 w-4" />}
              title="Cycle Progression"
              subtitle="Follicular and endometrial development across monitoring visits"
            />
            <div className="px-5 pb-5">
              <GrowthChart
                xLabels={history.map((m) => `Day ${m.day}`)}
                yUnit="millimetres"
                series={[
                  { name: 'Lead follicle', color: '#059669', values: history.map((m) => (m.right.length || m.left.length ? Math.max(...m.right, ...m.left) : 0)) },
                  { name: 'Mean follicle', color: '#34D399', values: history.map((m) => { const a = [...m.right, ...m.left]; return a.length ? +(a.reduce((s, v) => s + v, 0) / a.length).toFixed(1) : 0; }) },
                  { name: 'Endometrium', color: '#8B5CF6', values: history.map((m) => m.endometrium) },
                ]}
              />
            </div>
          </Card>
        </div>

        {/* ============ RIGHT — HORMONES & REVIEW ============ */}
        <div className="space-y-5">
          <Card>
            <CardHeader icon={<FlaskConical className="h-4 w-4" />} title="Hormone Results" subtitle={visit.date} />
            <div className="space-y-3 px-5 pb-5">
              {[
                { label: 'Estradiol (E2)', value: visit.estradiol, unit: 'pg/mL', range: '1,000 – 2,000', ok: visit.estradiol >= 1000 && visit.estradiol <= 2500 },
                { label: 'Luteinising Hormone', value: visit.lh, unit: 'mIU/mL', range: '< 10', ok: visit.lh < 10 },
                { label: 'Progesterone', value: visit.progesterone, unit: 'ng/mL', range: '< 1.5', ok: visit.progesterone < 1.5 },
              ].map((h) => (
                <div key={h.label} className="rounded-xl border border-ink-200/70 p-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[13.5px] font-medium text-ink-700">{h.label}</p>
                      <p className="tnum mt-1 text-[22px] font-semibold leading-none text-ink-900">
                        {h.value.toLocaleString('en-IN')}
                        <span className="ml-1.5 text-[12px] font-normal text-ink-400">{h.unit}</span>
                      </p>
                    </div>
                    <Badge tone={h.ok ? 'completed' : 'attention'} size="sm">
                      {h.ok ? 'In range' : 'Review'}
                    </Badge>
                  </div>
                  <p className="tnum mt-2 text-[12px] text-ink-400">Expected: {h.range}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Clinical review */}
          <Card>
            <CardHeader
              icon={<Stethoscope className="h-4 w-4" />}
              title="Doctor's Clinical Review"
              subtitle="Your assessment is recorded in the medical record"
            />
            <div className="px-5 pb-5">
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={5}
                className="w-full resize-none rounded-xl border border-ink-200 bg-white p-3 text-[14px] leading-relaxed text-ink-800 transition-shadow placeholder:text-ink-400"
                placeholder="Document your clinical assessment…"
              />

              <div className="mt-3 rounded-xl bg-ink-50 p-3">
                <p className="text-[12px] font-medium uppercase tracking-wide text-ink-400">Next review</p>
                <p className="mt-1 text-[14.5px] font-semibold text-ink-900">30 July 2026 · 9:30 AM</p>
                <p className="mt-0.5 text-[12.5px] text-ink-500">Scan Room 2 · Dr. Archana</p>
              </div>

              <div className="mt-3 flex gap-2">
                <Button
                  variant="primary"
                  className="flex-1"
                  icon={saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                  onClick={save}
                >
                  {saved ? 'Saved' : 'Save Clinical Review'}
                </Button>
                <Button
                  icon={<CalendarPlus className="h-4 w-4" />}
                  onClick={() => toast({ title: 'Follow-up scheduled', body: '30 July 2026, 9:30 AM — Scan Room 2.', tone: 'success' })}
                />
              </div>

              <p className="mt-3 text-[12px] leading-relaxed text-ink-400">
                The system does not make treatment decisions. All clinical judgements remain the
                responsibility of the treating physician.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
