'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { PATIENTS } from '@/lib/data';
import { cn, TONE, ageFromDOB, initialsOf } from '@/lib/utils';
import { Card, Badge, Button, Avatar, Input, SectionTitle, Skeleton } from '@/components/ui/primitives';
import { usePatients } from '@/lib/api/patients';
import { Search, SlidersHorizontal, UserPlus, ChevronRight, Download, LayoutGrid, List } from 'lucide-react';

const FILTERS = ['All Patients', 'Active Cycles', 'Stimulation', 'Embryology', 'Follow-up'];

/** The static fixture's per-patient treatment-stage detail (stage, AMH,
 * cycle day…) isn't returned by GET /patients — that endpoint deliberately
 * stays a lightweight registry row (spec §9's "purpose-specific response
 * shapes"). For the one seeded demo patient we already have that detail
 * from the prototype's original story, so it's used to enrich the real
 * row here; every other real patient shows honest placeholders instead
 * of fabricated clinical data. */
const STATIC_BY_UHID = Object.fromEntries(PATIENTS.map((p) => [p.id, p]));

export function Patients() {
  const { go, toast, openPatient } = useApp();
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState('All Patients');
  const [view, setView] = useState<'list' | 'grid'>('list');
  const patientsQuery = usePatients(q.trim() || undefined);
  const loading = patientsQuery.isLoading;

  const allRows = useMemo(() => {
    return (patientsQuery.data ?? []).map((p) => {
      const enrich = STATIC_BY_UHID[p.uhid];
      return {
        id: p.id,
        uhid: p.uhid,
        name: p.full_name,
        initials: initialsOf(p.full_name),
        age: ageFromDOB(p.date_of_birth),
        partner: enrich?.partner ?? null,
        stage: enrich?.stage ?? 'Registered',
        tone: enrich?.tone ?? ('neutral' as const),
        cycleDay: enrich?.cycleDay ?? '—',
        lastVisit: enrich?.lastVisit ?? '—',
        amh: enrich?.amh ?? null,
      };
    });
  }, [patientsQuery.data]);

  const rows = useMemo(() => {
    let r = allRows;
    if (filter === 'Active Cycles') r = r.filter((p) => p.tone === 'active' || p.tone === 'scheduled');
    if (filter === 'Stimulation') r = r.filter((p) => p.stage.includes('Stimulation'));
    if (filter === 'Embryology') r = r.filter((p) => p.stage.includes('Embryology') || p.stage.includes('Retrieval'));
    if (filter === 'Follow-up') r = r.filter((p) => p.stage.includes('Pregnancy'));
    return r;
  }, [allRows, filter]);

  const open = (id: string, name: string) => openPatient(id);

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Clinical"
        title="Patient Registry"
        description={`${allRows.length} ${allRows.length === 1 ? 'patient' : 'patients'} under active fertility care`}
        action={
          <div className="flex flex-wrap gap-2">
            <Button icon={<Download className="h-4 w-4" />} onClick={() => toast({ title: 'Export queued', body: 'Patient registry will be exported as CSV.', tone: 'success' })}>
              Export
            </Button>
            <Button variant="primary" icon={<UserPlus className="h-4 w-4" />} onClick={() => go('registration')}>
              Register Couple
            </Button>
          </div>
        }
      />

      {/* Controls */}
      <Card className="p-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="lg:min-w-[240px] lg:flex-1">
            <Input
              placeholder="Search by name, patient ID or partner…"
              icon={<Search className="h-3.5 w-3.5" />}
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="scroll-area flex flex-1 gap-1 overflow-x-auto rounded-lg bg-ink-100 p-1 lg:flex-none">
              {FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    'shrink-0 rounded-md px-3 py-1.5 text-[13.5px] font-medium transition-all',
                    filter === f ? 'bg-white text-ink-900 shadow-card' : 'text-ink-500 hover:text-ink-800'
                  )}
                >
                  {f}
                </button>
              ))}
            </div>

            <div className="flex shrink-0 gap-1 rounded-lg bg-ink-100 p-1">
              <button
                onClick={() => setView('list')}
                className={cn('rounded-md p-1.5 transition-all', view === 'list' ? 'bg-white text-ink-900 shadow-card' : 'text-ink-400')}
              >
                <List className="h-4 w-4" />
              </button>
              <button
                onClick={() => setView('grid')}
                className={cn('rounded-md p-1.5 transition-all', view === 'grid' ? 'bg-white text-ink-900 shadow-card' : 'text-ink-400')}
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="flex items-center gap-4 p-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3.5 w-40" />
                <Skeleton className="h-3 w-56" />
              </div>
              <Skeleton className="h-6 w-24 rounded-full" />
            </Card>
          ))}
        </div>
      ) : view === 'list' ? (
        <Card className="overflow-hidden">
          {/* Table head — desktop only, mobile rows are self-describing */}
          <div className="hidden grid-cols-[minmax(220px,2fr)_1.4fr_1fr_0.8fr_1fr_40px] items-center gap-4 border-b border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
            {['Patient & Partner', 'Treatment Stage', 'Cycle', 'AMH', 'Last Visit', ''].map((h) => (
              <span key={h} className="text-[12px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                {h}
              </span>
            ))}
          </div>

          <div className="stagger">
            {rows.map((p, i) => (
              <button
                key={p.id}
                style={{ ['--i' as string]: i }}
                onClick={() => open(p.id, p.name)}
                className="group flex w-full flex-col gap-2.5 border-b border-ink-100 px-4 py-3.5 text-left transition-colors last:border-0 hover:bg-brand-50/40 sm:px-5 md:grid md:grid-cols-[minmax(220px,2fr)_1.4fr_1fr_0.8fr_1fr_40px] md:items-center md:gap-4"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <Avatar initials={p.initials} size="md" gradient="from-ink-400 to-ink-600" />
                  <div className="min-w-0">
                    <p className="truncate text-[14.5px] font-semibold text-ink-900">{p.name}</p>
                    <p className="tnum truncate text-[12.5px] text-ink-500">
                      {p.uhid}{p.age !== null ? ` · ${p.age} yrs` : ''}
                    </p>
                    {p.partner && <p className="truncate text-[12px] text-ink-400">Partner — {p.partner}</p>}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 pl-[52px] md:contents md:pl-0">
                  <Badge tone={p.tone} size="sm">
                    {p.stage}
                  </Badge>
                  <span className="tnum text-[12.5px] font-medium text-ink-700 md:text-[13.5px]">{p.cycleDay}</span>
                  <span className="tnum text-[12.5px] text-ink-600 md:text-[13.5px]">{p.amh ? `AMH ${p.amh}` : '—'}</span>
                  <span className="text-[12px] text-ink-500 md:text-[13px]">{p.lastVisit}</span>
                </div>

                <ChevronRight className="hidden h-4 w-4 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600 md:block" />
              </button>
            ))}
          </div>

          {rows.length === 0 && (
            <div className="px-5 py-16 text-center">
              <p className="text-[14px] font-medium text-ink-700">No patients match your search</p>
              <p className="mt-1 text-[14px] text-ink-500">Try a different name, ID or filter.</p>
            </div>
          )}
        </Card>
      ) : (
        <div className="stagger grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {rows.map((p, i) => (
            <Card
              key={p.id}
              interactive
              style={{ ['--i' as string]: i }}
              className="p-4"
              onClick={() => open(p.id, p.name)}
            >
              <div className="flex items-start justify-between">
                <Avatar initials={p.initials} size="lg" gradient="from-ink-400 to-ink-600" />
                <Badge tone={p.tone} size="sm">
                  {p.cycleDay}
                </Badge>
              </div>
              <p className="mt-3 text-[14px] font-semibold text-ink-900">{p.name}</p>
              <p className="tnum text-[12.5px] text-ink-500">{p.uhid}</p>
              <div className="mt-3 space-y-1.5 border-t border-ink-100 pt-3">
                <div className="flex justify-between">
                  <span className="text-[12.5px] text-ink-500">Stage</span>
                  <span className="text-[12.5px] font-medium text-ink-800">{p.stage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[12.5px] text-ink-500">Partner</span>
                  <span className="text-[12.5px] font-medium text-ink-800">{p.partner ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[12.5px] text-ink-500">AMH</span>
                  <span className="tnum text-[12.5px] font-medium text-ink-800">{p.amh ? `${p.amh} ng/mL` : '—'}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
