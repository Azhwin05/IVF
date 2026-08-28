'use client';

import React, { useMemo, useState } from 'react';
import { useApp, type ScreenId } from '@/lib/store';
import { TIMELINE, PATIENT } from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, Badge, Button, SectionTitle, Field } from '@/components/ui/primitives';
import { usePatientTimeline, type TimelineEventType } from '@/lib/api/clinical';
import { PatientHeader } from './Workspace';
import { Check, ChevronDown, ArrowRight, Circle, Loader2 } from 'lucide-react';

const EVENT_TYPE_LABEL: Record<TimelineEventType, string> = {
  consultation: 'Consultation',
  investigation: 'Investigation',
  stimulation_start: 'Stimulation Started',
  monitoring_visit: 'Monitoring Visit',
  trigger: 'Trigger',
  retrieval: 'Oocyte Retrieval',
  embryology_update: 'Embryology Update',
  embryo_transfer: 'Embryo Transfer',
  pregnancy_milestone: 'Pregnancy Milestone',
  billing: 'Billing',
  document: 'Document',
};
const EVENT_TYPE_LINK: Partial<Record<TimelineEventType, ScreenId>> = {
  investigation: 'laboratory',
  monitoring_visit: 'monitoring',
  embryology_update: 'embryology',
  embryo_transfer: 'transfer',
  pregnancy_milestone: 'pregnancy',
  billing: 'billing',
};

export function Timeline() {
  const { go, selectedPatientId } = useApp();
  const [open, setOpen] = useState<string | null>('ts-4');

  const timelineQuery = usePatientTimeline(selectedPatientId);
  const hasRealData = (timelineQuery.data ?? []).length > 0;

  const realStages = useMemo(() => {
    const events = [...(timelineQuery.data ?? [])].sort((a, b) => new Date(a.occurred_at).getTime() - new Date(b.occurred_at).getTime());
    return events.map((e, i) => ({
      id: e.id,
      title: e.title,
      date: new Date(e.occurred_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
      status: (i === events.length - 1 ? 'active' : 'completed') as 'completed' | 'active' | 'upcoming',
      summary: e.summary ?? EVENT_TYPE_LABEL[e.event_type],
      details: [{ label: 'Type', value: EVENT_TYPE_LABEL[e.event_type] }],
      link: EVENT_TYPE_LINK[e.event_type],
    }));
  }, [timelineQuery.data]);

  const stages = hasRealData ? realStages : TIMELINE;
  const completed = stages.filter((t) => t.status === 'completed').length;
  const pct = Math.round(((completed + 0.5) / stages.length) * 100);

  return (
    <div className="screen-enter mx-auto max-w-[1100px] space-y-5 p-4 sm:p-6 lg:p-8">
      <PatientHeader compact />

      <SectionTitle
        eyebrow="Complete Journey"
        title="IVF Patient Timeline"
        description="Every stage from first consultation to treatment outcome — one shared view for the whole team."
      />

      {/* Progress rail */}
      <Card className="p-4 sm:p-5">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="text-[12.5px] text-ink-500">Journey progress</p>
            <p className="tnum tracking-display text-[20px] font-semibold text-ink-900 sm:text-[22px]">
              {completed} of {stages.length} stages complete
            </p>
          </div>
          {!hasRealData && (
            <Badge tone="active" wrap className="self-start sm:self-auto sm:max-w-[280px]">
              Currently: {PATIENT.phase} — Day {PATIENT.cycleDay}
            </Badge>
          )}
        </div>
        <div className="relative h-2 overflow-hidden rounded-full bg-ink-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-[width] duration-[1500ms] ease-spring"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
          {[
            { c: 'bg-brand-600', l: 'Completed' },
            { c: 'bg-amber-500', l: 'In progress' },
            { c: 'bg-ink-300', l: 'Upcoming' },
          ].map((k) => (
            <span key={k.l} className="flex items-center gap-1.5 text-[11.5px] text-ink-500">
              <span className={cn('h-2 w-2 rounded-full', k.c)} /> {k.l}
            </span>
          ))}
        </div>
      </Card>

      {/* Vertical timeline */}
      <div className="relative">
        <div className="absolute bottom-4 left-[27px] top-4 w-[2px] bg-ink-200" />
        <div
          className="absolute left-[27px] top-4 w-[2px] bg-gradient-to-b from-brand-500 to-brand-600 transition-[height] duration-[1600ms] ease-spring"
          style={{ height: `${pct * 0.92}%` }}
        />

        <div className="stagger space-y-3">
          {stages.map((s, i) => {
            const isOpen = open === s.id;
            const done = s.status === 'completed';
            const active = s.status === 'active';

            return (
              <div key={s.id} style={{ ['--i' as string]: i }} className="relative pl-[68px]">
                {/* node */}
                <div className="absolute left-0 top-3.5">
                  <div
                    className={cn(
                      'relative flex h-[38px] w-[38px] items-center justify-center rounded-full ring-4 ring-white transition-all duration-300',
                      done
                        ? 'bg-brand-600'
                        : active
                        ? 'bg-amber-500'
                        : 'border-2 border-dashed border-ink-300 bg-white'
                    )}
                  >
                    {active && (
                      <span className="absolute inset-0 animate-pulse-ring rounded-full bg-amber-400/50" />
                    )}
                    {done ? (
                      <Check className="h-[18px] w-[18px] text-white" strokeWidth={3} />
                    ) : active ? (
                      <Loader2 className="h-[18px] w-[18px] animate-spin text-white" strokeWidth={2.5} />
                    ) : (
                      <Circle className="h-3 w-3 text-ink-300" fill="currentColor" />
                    )}
                  </div>
                </div>

                <Card
                  className={cn(
                    'overflow-hidden transition-all duration-300',
                    active && 'border-amber-300 shadow-lift',
                    isOpen && 'shadow-lift'
                  )}
                >
                  <button
                    onClick={() => setOpen(isOpen ? null : s.id)}
                    className="flex w-full items-start justify-between gap-4 p-4 text-left transition-colors hover:bg-ink-50/60"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <h3 className="text-[15px] font-semibold tracking-[-0.011em] text-ink-900">
                          {s.title}
                        </h3>
                        <Badge tone={done ? 'completed' : active ? 'attention' : 'pending'} size="sm">
                          {done ? 'Completed' : active ? 'In progress' : 'Upcoming'}
                        </Badge>
                      </div>
                      <p className="tnum mt-1 text-[12.5px] font-medium text-ink-500">{s.date}</p>
                      <p className="mt-1.5 text-[13px] leading-relaxed text-ink-600">{s.summary}</p>
                    </div>
                    <ChevronDown
                      className={cn(
                        'mt-1 h-4 w-4 shrink-0 text-ink-400 transition-transform duration-300',
                        isOpen && 'rotate-180'
                      )}
                    />
                  </button>

                  <div
                    className="grid transition-[grid-template-rows] duration-350 ease-spring"
                    style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}
                  >
                    <div className="overflow-hidden">
                      <div className="border-t border-ink-100 bg-ink-50/40 p-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                          {s.details.map((d) => (
                            <Field key={d.label} label={d.label} value={d.value} />
                          ))}
                        </div>
                        {s.link && (
                          <Button
                            size="sm"
                            variant="primary"
                            className="mt-4"
                            iconRight={<ArrowRight className="h-3.5 w-3.5" />}
                            onClick={() => go(s.link as ScreenId)}
                          >
                            Open {s.title.toLowerCase()}
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
