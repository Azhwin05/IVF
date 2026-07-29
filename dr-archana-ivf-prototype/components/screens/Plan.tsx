'use client';

import React from 'react';
import { useApp, type ScreenId } from '@/lib/store';
import { PATIENT, PARTNER, MEDICATIONS, PACKAGE, INVESTIGATIONS } from '@/lib/data';
import { cn, formatINR } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Field, DataRow, InfoNote, ProgressBar } from '@/components/ui/primitives';
import { PatientHeader } from './Workspace';
import {
  ClipboardList,
  Pill,
  Target,
  ShieldCheck,
  Receipt,
  FlaskConical,
  Check,
  CircleDot,
  Circle,
  Stethoscope,
} from 'lucide-react';

const STAGES = [
  { id: 'consult', label: 'Consultation', status: 'done' },
  { id: 'stim', label: 'Stimulation', status: 'active' },
  { id: 'retrieval', label: 'Retrieval', status: 'todo' },
  { id: 'embryology', label: 'Embryology', status: 'todo' },
  { id: 'transfer', label: 'Transfer', status: 'todo' },
  { id: 'followup', label: 'Follow-up', status: 'todo' },
];

export function Plan() {
  const { go, toast } = useApp();

  return (
    <div className="screen-enter mx-auto max-w-[1300px] space-y-5 p-4 sm:p-6 lg:p-8">
      <PatientHeader compact />

      <SectionTitle
        eyebrow={`Cycle ${PATIENT.cycleId}`}
        title="IVF Treatment Plan"
        description="Protocol, objectives, medication schedule and expected stages"
        action={
          <Button
            variant="primary"
            icon={<Check className="h-4 w-4" />}
            onClick={() => toast({ title: 'Treatment plan confirmed', body: 'Plan re-confirmed and recorded in the audit trail.', tone: 'success' })}
          >
            Confirm Plan
          </Button>
        }
      />

      {/* ============ STAGE TRACKER ============ */}
      <Card className="p-4 sm:p-5">
        <div className="relative">
          <div className="absolute left-0 right-0 top-[15px] h-[2px] bg-ink-200" />
          <div
            className="absolute left-0 top-[15px] h-[2px] bg-gradient-to-r from-brand-500 to-brand-600 transition-[width] duration-[1500ms] ease-spring"
            style={{ width: '30%' }}
          />
          <div className="relative flex justify-between">
            {STAGES.map((s, i) => (
              <div key={s.id} className="animate-fade-up flex min-w-0 flex-1 flex-col items-center px-0.5" style={{ animationDelay: `${i * 80}ms` }}>
                <div
                  className={cn(
                    'relative z-10 flex h-8 w-8 items-center justify-center rounded-full ring-4 ring-white',
                    s.status === 'done' ? 'bg-brand-600' : s.status === 'active' ? 'bg-amber-500' : 'border-2 border-dashed border-ink-300 bg-white'
                  )}
                >
                  {s.status === 'active' && <span className="absolute inset-0 animate-pulse-ring rounded-full bg-amber-400/50" />}
                  {s.status === 'done' ? (
                    <Check className="h-4 w-4 text-white" strokeWidth={3} />
                  ) : s.status === 'active' ? (
                    <CircleDot className="h-4 w-4 text-white" />
                  ) : (
                    <Circle className="h-2.5 w-2.5 text-ink-300" fill="currentColor" />
                  )}
                </div>
                <p
                  className={cn(
                    'mt-2 max-w-full text-center text-[10px] font-medium leading-tight sm:text-[12px]',
                    s.status === 'todo' ? 'text-ink-400' : 'text-ink-900'
                  )}
                >
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ============ PLAN CORE ============ */}
        <div className="space-y-5 lg:col-span-2">
          <Card>
            <CardHeader
              icon={<ClipboardList className="h-4 w-4" />}
              title="Treatment Configuration"
              subtitle="Agreed with the couple on 12 July 2026"
              action={<Badge tone="active">Active</Badge>}
            />
            <div className="grid gap-4 px-5 pb-5 sm:grid-cols-2">
              <Field label="Treatment" value={PATIENT.treatment} />
              <Field label="Protocol" value={PATIENT.protocol} />
              <Field label="Indication" value={`${PATIENT.infertilityType} — ${PATIENT.duration}`} />
              <Field label="Fertilisation Method" value="ICSI (partner factor)" />
              <Field label="Transfer Strategy" value="Elective single blastocyst transfer" />
              <Field label="Surplus Embryos" value="Vitrification offered and consented" />
            </div>

            <div className="px-5 pb-5">
              <InfoNote tone="brand" icon={<Target className="h-4 w-4" />}>
                <span className="font-medium">Treatment objective:</span> achieve a single healthy
                ongoing pregnancy while minimising the risk of ovarian hyperstimulation and multiple
                gestation. ICSI is indicated by the partner&apos;s semen analysis.
              </InfoNote>
            </div>
          </Card>

          <Card>
            <CardHeader icon={<Pill className="h-4 w-4" />} title="Medication Plan" subtitle="Stimulation and adjunct therapy" />
            <div className="stagger space-y-2 px-5 pb-5">
              {MEDICATIONS.map((m, i) => (
                <div
                  key={m.name}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-wrap items-center gap-3 rounded-xl border border-ink-200/70 p-3.5"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                    <Pill className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13.5px] font-semibold text-ink-900">
                      {m.name} <span className="tnum font-normal text-ink-500">· {m.dose}</span>
                    </p>
                    <p className="text-[12px] text-ink-500">{m.route}</p>
                  </div>
                  <span className="text-[11.5px] text-ink-400">From {m.since}</span>
                  <Badge tone={m.tone} size="sm">
                    {m.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader icon={<FlaskConical className="h-4 w-4" />} title="Planned Investigations" subtitle="Baseline workup completed prior to cycle start" />
            <div className="grid gap-2 px-5 pb-5 sm:grid-cols-2">
              {INVESTIGATIONS.slice(0, 6).map((iv) => (
                <div key={iv.name} className="flex items-center justify-between rounded-lg bg-ink-50/70 px-3 py-2">
                  <span className="min-w-0 truncate text-[12.5px] text-ink-700">{iv.name}</span>
                  <Badge tone={iv.flag === 'normal' ? 'completed' : 'attention'} size="sm">
                    {iv.value}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* ============ RIGHT RAIL ============ */}
        <div className="space-y-5">
          <Card>
            <CardHeader icon={<ShieldCheck className="h-4 w-4" />} title="Consent Status" />
            <div className="px-5 pb-5">
              {[
                { l: 'IVF treatment consent', d: '12 Jul 2026' },
                { l: 'ICSI procedure consent', d: '12 Jul 2026' },
                { l: 'Cryopreservation consent', d: '3 Aug 2026' },
                { l: 'Anaesthesia consent', d: 'Pending — due before retrieval' },
              ].map((c, i) => {
                const signed = !c.d.includes('Pending');
                return (
                  <div key={c.l} className="flex items-center gap-2.5 border-b border-ink-100 py-2.5 last:border-0">
                    <div
                      className={cn(
                        'flex h-5 w-5 shrink-0 items-center justify-center rounded-full',
                        signed ? 'bg-brand-600' : 'bg-amber-100 ring-1 ring-amber-300'
                      )}
                    >
                      {signed ? <Check className="h-3 w-3 text-white" strokeWidth={3.5} /> : <Circle className="h-2 w-2 text-amber-600" fill="currentColor" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[12.5px] font-medium text-ink-800">{c.l}</p>
                      <p className="text-[11px] text-ink-400">{c.d}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card>
            <CardHeader icon={<Receipt className="h-4 w-4" />} title="Package Details" />
            <div className="px-5 pb-5">
              <p className="text-[13.5px] font-semibold text-ink-900">{PACKAGE.name}</p>
              <p className="tnum mt-1 text-[26px] font-semibold text-ink-900">
                {formatINR(PACKAGE.value)}
              </p>
              <div className="mt-3">
                <div className="mb-1.5 flex justify-between text-[11.5px]">
                  <span className="text-ink-500">Collected</span>
                  <span className="tnum font-medium text-ink-800">
                    {formatINR(PACKAGE.paid)} of {formatINR(PACKAGE.value)}
                  </span>
                </div>
                <ProgressBar value={(PACKAGE.paid / PACKAGE.value) * 100} height={7} />
              </div>
              <div className="mt-3">
                <DataRow label="Outstanding" value={formatINR(PACKAGE.outstanding)} tone="attention" />
              </div>
              <Button className="mt-3 w-full" onClick={() => go('billing')}>
                Open billing
              </Button>
            </div>
          </Card>

          <Card>
            <CardHeader icon={<Stethoscope className="h-4 w-4" />} title="Estimated Timeline" />
            <div className="px-5 pb-5">
              {[
                { l: 'Trigger injection', d: '31 Jul 2026' },
                { l: 'Oocyte retrieval', d: '2 Aug 2026' },
                { l: 'Embryo transfer', d: '7 Aug 2026' },
                { l: 'Beta-hCG test', d: '21 Aug 2026' },
              ].map((t) => (
                <DataRow key={t.l} label={t.l} value={t.d} />
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
