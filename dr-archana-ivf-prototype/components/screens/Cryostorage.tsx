'use client';

import React, { useState } from 'react';
import { useApp } from '@/lib/store';
import { CRYO_HIERARCHY, PATIENT, EMBRYOS } from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Field, InfoNote, DataRow } from '@/components/ui/primitives';
import {
  Snowflake,
  ChevronRight,
  ShieldCheck,
  Thermometer,
  CalendarClock,
  History,
  FileSignature,
  Container,
} from 'lucide-react';

const LEVELS = [
  { key: 'tank', label: 'Tank', value: CRYO_HIERARCHY.tank, sub: 'Liquid nitrogen dewar' },
  { key: 'canister', label: 'Canister', value: CRYO_HIERARCHY.canister, sub: 'Of 6 canisters' },
  { key: 'cane', label: 'Cane', value: CRYO_HIERARCHY.cane, sub: 'Of 10 canes' },
  { key: 'goblet', label: 'Goblet', value: CRYO_HIERARCHY.goblet, sub: 'Of 8 goblets' },
];

export function Cryostorage() {
  const { toast } = useApp();
  const [selected, setSelected] = useState(CRYO_HIERARCHY.straws[0].id);
  const straw = CRYO_HIERARCHY.straws.find((s) => s.id === selected)!;
  const embryo = EMBRYOS.find((e) => e.id === straw.embryo);

  return (
    <div className="screen-enter mx-auto max-w-[1300px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Laboratory"
        title="Cryostorage Management"
        description={`${PATIENT.name} · ${CRYO_HIERARCHY.straws.length} vitrified blastocysts in long-term storage`}
        action={
          <Button
            variant="primary"
            icon={<FileSignature className="h-4 w-4" />}
            onClick={() => toast({ title: 'Consent renewal initiated', body: 'Renewal request sent to the couple for signature.', tone: 'success' })}
          >
            Renew Consent
          </Button>
        }
      />

      {/* ============ STATUS STRIP ============ */}
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: Thermometer, label: 'Tank Temperature', value: CRYO_HIERARCHY.temperature, sub: 'Nominal · logged hourly', tone: 'completed' as const },
          { icon: ShieldCheck, label: 'Storage Consent', value: 'Verified', sub: CRYO_HIERARCHY.consent, tone: 'completed' as const },
          { icon: CalendarClock, label: 'Next Renewal', value: '4 Aug 2027', sub: '371 days remaining', tone: 'pending' as const },
          { icon: Snowflake, label: 'Stored Embryos', value: '2 straws', sub: 'Grades 4AB, 3BB', tone: 'active' as const },
        ].map((s, i) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="p-4" style={{ ['--i' as string]: i }}>
              <div className="flex items-start justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-600/12">
                  <Icon className="h-[18px] w-[18px]" />
                </div>
                <Badge tone={s.tone} size="sm" dot={false}>
                  OK
                </Badge>
              </div>
              <p className="mt-3 text-[11px] font-medium uppercase tracking-[0.06em] text-ink-400">
                {s.label}
              </p>
              <p className="tnum mt-1 text-[18px] font-semibold text-ink-900">{s.value}</p>
              <p className="mt-0.5 text-[11px] text-ink-500">{s.sub}</p>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ============ HIERARCHY ============ */}
        <Card className="lg:col-span-2">
          <CardHeader
            icon={<Container className="h-4 w-4" />}
            title="Storage Location Hierarchy"
            subtitle="Physical chain from dewar to individual straw"
          />

          <div className="px-5 pb-5">
            {/* breadcrumb hierarchy */}
            <div className="flex flex-wrap items-center gap-2">
              {LEVELS.map((l, i) => (
                <React.Fragment key={l.key}>
                  <div
                    className="animate-fade-up rounded-xl border border-sky-200/70 bg-gradient-to-b from-sky-50/80 to-white px-3.5 py-2.5"
                    style={{ animationDelay: `${i * 90}ms` }}
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-sky-600">
                      {l.label}
                    </p>
                    <p className="tnum mt-0.5 text-[14px] font-semibold text-ink-900">{l.value}</p>
                    <p className="text-[10px] text-ink-400">{l.sub}</p>
                  </div>
                  {i < LEVELS.length - 1 && (
                    <ChevronRight className="h-4 w-4 shrink-0 text-ink-300" />
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* straws */}
            <div className="mt-5">
              <p className="mb-2.5 text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-500">
                Straws in {CRYO_HIERARCHY.goblet}
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                {CRYO_HIERARCHY.straws.map((s, i) => {
                  const active = selected === s.id;
                  return (
                    <button
                      key={s.id}
                      onClick={() => setSelected(s.id)}
                      className={cn(
                        'lift group relative overflow-hidden rounded-xl border p-4 text-left transition-all',
                        active
                          ? 'border-sky-400 bg-sky-50/60 shadow-lift ring-1 ring-sky-500/20'
                          : 'border-ink-200/70 bg-white hover:border-sky-300'
                      )}
                    >
                      {/* frosted straw graphic */}
                      <div className="flex items-center gap-3">
                        <div className="relative flex h-16 w-6 flex-col overflow-hidden rounded-full border border-sky-200 bg-gradient-to-b from-white via-sky-50 to-sky-100">
                          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-sky-300/70 to-transparent" />
                          <Snowflake className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 text-sky-500" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="tnum text-[14px] font-semibold text-ink-900">{s.id}</p>
                          <p className="tnum text-[12px] text-ink-600">
                            Embryo {s.embryo} · Grade {s.grade}
                          </p>
                          <p className="mt-1 text-[11px] text-ink-400">Frozen {s.frozen}</p>
                          <Badge tone="completed" size="sm" className="mt-1.5">
                            {s.status}
                          </Badge>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* selected detail */}
            <div className="mt-5 rounded-xl border border-ink-200/70 bg-ink-50/50 p-4">
              <p className="mb-3 text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-500">
                Selected item detail
              </p>
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Stored Item" value={`Embryo ${straw.embryo}`} />
                <Field label="Patient" value={PATIENT.name} />
                <Field label="Patient ID" value={PATIENT.id} mono />
                <Field label="Grade" value={straw.grade} mono />
                <Field label="Freeze Date" value={straw.frozen} />
                <Field label="Storage Status" value={straw.status} />
                <Field
                  label="Full Location"
                  value={`${CRYO_HIERARCHY.tank} / ${CRYO_HIERARCHY.canister} / ${CRYO_HIERARCHY.cane} / ${CRYO_HIERARCHY.goblet} / ${straw.id}`}
                  className="sm:col-span-2"
                />
                <Field label="Next Renewal" value={CRYO_HIERARCHY.renewal} />
              </div>
              {embryo && (
                <p className="mt-3 border-l-2 border-sky-300 pl-3 text-[12.5px] leading-relaxed text-ink-600">
                  {embryo.note}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* ============ CHAIN OF CUSTODY ============ */}
        <Card>
          <CardHeader
            icon={<History className="h-4 w-4" />}
            title="Chain of Custody"
            subtitle="Every handling event is witnessed and logged"
          />
          <div className="stagger px-5 pb-5">
            {CRYO_HIERARCHY.custody.map((c, i) => (
              <div key={i} style={{ ['--i' as string]: i }} className="relative flex gap-3 pb-4 last:pb-0">
                {i < CRYO_HIERARCHY.custody.length - 1 && (
                  <span className="absolute left-[11px] top-6 h-full w-px bg-ink-200" />
                )}
                <div className="relative z-10 mt-1 flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-sky-50 ring-1 ring-sky-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[12.5px] leading-snug text-ink-800">{c.event}</p>
                  <p className="mt-0.5 text-[11px] text-ink-400">
                    <span className="tnum">{c.at}</span> · {c.by}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-ink-100 p-5">
            <InfoNote tone="brand" icon={<ShieldCheck className="h-4 w-4" />}>
              Storage consent verified and on file. Automated renewal reminders are issued to the
              couple 60 days before expiry.
            </InfoNote>
          </div>
        </Card>
      </div>
    </div>
  );
}
