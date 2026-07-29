'use client';

import React from 'react';
import { useApp } from '@/lib/store';
import { BETA_HCG, PREGNANCY_MILESTONES, PATIENT, PARTNER } from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Field, InfoNote } from '@/components/ui/primitives';
import { GrowthChart } from '@/components/ui/charts';
import { useCountUp } from '@/lib/hooks';
import {
  HeartPulse,
  Check,
  Activity,
  CalendarClock,
  Stethoscope,
  Baby,
  TrendingUp,
  Sparkles,
} from 'lucide-react';

export function Pregnancy() {
  const { toast } = useApp();
  const hr = useCountUp(128, 1400);

  return (
    <div className="screen-enter mx-auto max-w-[1300px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Outcome"
        title="Pregnancy Follow-up"
        description={`${PATIENT.name} & ${PARTNER.name} · Cycle ${PATIENT.cycleId} · Transfer 7 August 2026`}
      />

      {/* ============ OUTCOME HERO ============ */}
      <Card className="relative overflow-hidden border-brand-200">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-50 via-emerald-50/50 to-transparent" />
        <div
          className="aurora animate-drift"
          style={{ width: 320, height: 320, top: '-40%', right: '4%', background: 'radial-gradient(circle, rgba(16,185,129,.22), transparent 70%)' }}
        />

        <div className="relative flex flex-wrap items-center gap-6 p-6">
          <div className="relative flex h-20 w-20 items-center justify-center">
            <span className="absolute inset-0 animate-pulse-ring rounded-full bg-brand-400/30" />
            <span className="absolute inset-0 animate-pulse-ring rounded-full bg-brand-400/20" style={{ animationDelay: '1s' }} />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-glow">
              <HeartPulse className="h-8 w-8 text-white" strokeWidth={1.8} />
            </div>
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-600" />
              <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-700">
                Treatment Outcome
              </span>
            </div>
            <h2 className="tracking-display font-display mt-1.5 text-[34px] leading-tight text-ink-900">
              Positive Pregnancy
            </h2>
            <p className="mt-1 text-[14px] text-ink-600">
              Healthy ongoing intrauterine pregnancy — currently 7 weeks gestation.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { l: 'Gestation', v: '7w 2d' },
              { l: 'Fetal heart rate', v: `${Math.round(hr)} bpm` },
              { l: 'Estimated due date', v: '15 May 2027' },
            ].map((s) => (
              <div key={s.l} className="rounded-xl border border-brand-200/60 bg-white/70 p-3 backdrop-blur-sm">
                <p className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-400">
                  {s.l}
                </p>
                <p className="tnum mt-1 text-[17px] font-semibold text-ink-900">{s.v}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ============ BETA hCG ============ */}
        <Card className="lg:col-span-2">
          <CardHeader
            icon={<TrendingUp className="h-4 w-4" />}
            title="Beta-hCG Progression"
            subtitle="Serial quantitative measurements following embryo transfer"
            action={<Badge tone="completed">Appropriate doubling</Badge>}
          />

          <div className="px-5 pb-5">
            <div className="grid gap-3 sm:grid-cols-3">
              {BETA_HCG.map((b, i) => (
                <div
                  key={b.day}
                  className="animate-fade-up rounded-xl border border-ink-200/70 bg-gradient-to-b from-white to-brand-50/40 p-4"
                  style={{ animationDelay: `${i * 110}ms` }}
                >
                  <p className="text-[11px] font-medium uppercase tracking-[0.06em] text-ink-400">
                    {b.day}
                  </p>
                  <p className="tnum tracking-display mt-1.5 text-[28px] font-semibold leading-none text-ink-900">
                    {b.value.toLocaleString('en-IN')}
                  </p>
                  <p className="mt-1 text-[11px] text-ink-400">mIU/mL</p>
                  <Badge tone={b.tone} size="sm" className="mt-2.5">
                    {b.verdict}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-5">
              <GrowthChart
                xLabels={BETA_HCG.map((b) => b.day)}
                yUnit="mIU/mL"
                series={[{ name: 'Beta-hCG', color: '#059669', values: BETA_HCG.map((b) => b.value) }]}
                height={190}
              />
            </div>

            <div className="mt-4">
              <InfoNote tone="brand" icon={<Stethoscope className="h-4 w-4" />}>
                <span className="font-medium">Clinical interpretation:</span> Beta-hCG is rising
                appropriately with a doubling time well within the expected range. Serial ultrasound
                confirms a single viable intrauterine pregnancy.
              </InfoNote>
            </div>
          </div>
        </Card>

        {/* ============ ULTRASOUND ============ */}
        <Card>
          <CardHeader icon={<Activity className="h-4 w-4" />} title="Ultrasound Milestones" subtitle="Serial transvaginal scans" />
          <div className="space-y-3 px-5 pb-5">
            {[
              { week: '6 weeks', date: '4 Sep 2026', finding: 'Single gestational sac visualised in the uterine cavity. Yolk sac present.', ok: true },
              { week: '7 weeks', date: '11 Sep 2026', finding: 'Fetal pole with cardiac activity detected. Heart rate 128 bpm — appropriate for gestation.', ok: true },
              { week: '11–13 weeks', date: '9 Oct 2026', finding: 'Nuchal translucency scan scheduled.', ok: false },
            ].map((u, i) => (
              <div
                key={u.week}
                className={cn(
                  'animate-fade-up rounded-xl border p-3.5',
                  u.ok ? 'border-brand-200/70 bg-brand-50/40' : 'border-ink-200/70 bg-ink-50/50'
                )}
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-semibold text-ink-900">{u.week}</p>
                  <Badge tone={u.ok ? 'completed' : 'pending'} size="sm">
                    {u.ok ? 'Completed' : 'Scheduled'}
                  </Badge>
                </div>
                <p className="tnum mt-0.5 text-[11px] text-ink-400">{u.date}</p>
                <p className="mt-1.5 text-[12px] leading-relaxed text-ink-600">{u.finding}</p>
              </div>
            ))}

            <Button
              className="w-full"
              icon={<CalendarClock className="h-4 w-4" />}
              onClick={() => toast({ title: 'Scan scheduled', body: 'NT scan booked for 9 October 2026, 10:00 AM.', tone: 'success' })}
            >
              Schedule next scan
            </Button>
          </div>
        </Card>
      </div>

      {/* ============ MILESTONE JOURNEY ============ */}
      <Card>
        <CardHeader
          icon={<Baby className="h-4 w-4" />}
          title="Pregnancy Journey"
          subtitle="From embryo transfer through to delivery outcome"
        />
        <div className="px-5 pb-6">
          <div className="relative">
            {/* rail */}
            <div className="absolute left-0 right-0 top-[19px] h-[2px] bg-ink-200" />
            <div
              className="absolute left-0 top-[19px] h-[2px] bg-gradient-to-r from-brand-500 to-brand-600 transition-[width] duration-[1600ms] ease-spring"
              style={{ width: '66%' }}
            />

            <div className="relative grid grid-cols-2 gap-y-6 md:grid-cols-3 lg:grid-cols-6">
              {PREGNANCY_MILESTONES.map((m, i) => {
                const done = m.status === 'completed';
                return (
                  <div key={m.label} className="animate-fade-up flex flex-col items-center px-1 text-center" style={{ animationDelay: `${i * 90}ms` }}>
                    <div
                      className={cn(
                        'relative z-10 flex h-10 w-10 items-center justify-center rounded-full ring-4 ring-white transition-all',
                        done ? 'bg-brand-600' : 'border-2 border-dashed border-ink-300 bg-white'
                      )}
                    >
                      {done ? (
                        <Check className="h-5 w-5 text-white" strokeWidth={3} />
                      ) : (
                        <span className="h-2 w-2 rounded-full bg-ink-300" />
                      )}
                    </div>
                    <p className={cn('mt-2.5 text-[12.5px] font-semibold leading-tight', done ? 'text-ink-900' : 'text-ink-500')}>
                      {m.label}
                    </p>
                    <p className="tnum mt-0.5 text-[11px] text-ink-400">{m.date}</p>
                    <p className="mt-1 text-[11px] leading-snug text-ink-500">{m.detail}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
