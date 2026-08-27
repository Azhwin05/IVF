'use client';

import React, { useMemo, useState } from 'react';
import { useApp } from '@/lib/store';
import { EMBRYOS, EMBRYO_SUMMARY, PATIENT, type Embryo } from '@/lib/data';
import { cn, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Modal, Field, InfoNote, ProgressBar } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { useCoupleForPatient } from '@/lib/api/patients';
import { useActiveCycle } from '@/lib/api/ivf';
import { useEmbryosForCycle, type EmbryoOut } from '@/lib/api/embryology';
import { useCryoLocationsForCycle } from '@/lib/api/cryostorage';
import {
  Microscope,
  Snowflake,
  ArrowRight,
  Info,
  CheckCircle2,
  Layers,
  Beaker,
  ClipboardCheck,
} from 'lucide-react';

/** Stylised blastocyst rendering — grade drives the visual. */
function EmbryoVisual({ embryo, size = 96 }: { embryo: Embryo; size?: number }) {
  const quality = embryo.score;
  const cells = Math.max(6, Math.round(quality / 6));
  const tone = quality >= 85 ? '#059669' : quality >= 70 ? '#34D399' : quality >= 50 ? '#F59E0B' : '#A8A29E';

  return (
    <svg viewBox="0 0 100 100" width={size} height={size} className="shrink-0">
      <defs>
        <radialGradient id={`zp-${embryo.id}`} cx="35%" cy="30%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="70%" stopColor="#F5F5F4" />
          <stop offset="100%" stopColor="#E7E5E4" />
        </radialGradient>
        <radialGradient id={`icm-${embryo.id}`} cx="40%" cy="35%">
          <stop offset="0%" stopColor={`${tone}ee`} />
          <stop offset="100%" stopColor={tone} />
        </radialGradient>
      </defs>

      {/* zona pellucida */}
      <circle cx="50" cy="50" r="44" fill={`url(#zp-${embryo.id})`} stroke="#D6D3D1" strokeWidth="1.2" />
      <circle cx="50" cy="50" r="37" fill="#FEFEFE" stroke="#E7E5E4" strokeWidth="0.8" />

      {/* trophectoderm cells around the rim */}
      {Array.from({ length: cells }).map((_, i) => {
        const a = (i / cells) * Math.PI * 2;
        const cx = 50 + Math.cos(a) * 30;
        const cy = 50 + Math.sin(a) * 30;
        return (
          <circle
            key={i}
            cx={cx}
            cy={cy}
            r="6.2"
            fill={`${tone}22`}
            stroke={`${tone}88`}
            strokeWidth="0.9"
            className="animate-scale-in"
            style={{ animationDelay: `${i * 45}ms`, transformOrigin: `${cx}px ${cy}px` }}
          />
        );
      })}

      {/* inner cell mass */}
      <ellipse
        cx="38"
        cy="42"
        rx="15"
        ry="13"
        fill={`url(#icm-${embryo.id})`}
        className="animate-scale-in"
        style={{ animationDelay: '0.3s', transformOrigin: '38px 42px' }}
      />
      <ellipse cx="34" cy="38" rx="4.5" ry="3.5" fill="#ffffff" opacity="0.34" />
    </svg>
  );
}

/** Single funnel statistic — isolated so the count-up hook stays at component top level. */
function FunnelStat({
  value,
  label,
  sub,
  pct,
  delay,
}: {
  value: number;
  label: string;
  sub: string;
  pct: number;
  delay: number;
}) {
  const v = useCountUp(value, 1100);
  return (
    <div className="rounded-xl border border-ink-200/70 bg-gradient-to-b from-white to-ink-50/50 p-3.5">
      <p className="tnum tracking-display text-[30px] font-semibold leading-none text-ink-900">
        {Math.round(v)}
      </p>
      <p className="mt-1.5 text-[12px] font-medium leading-snug text-ink-700">{label}</p>
      <p className="mt-0.5 text-[10.5px] text-ink-400">{sub}</p>
      <div className="mt-2.5 h-1 overflow-hidden rounded-full bg-ink-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-[width] duration-[1300ms] ease-spring"
          style={{ width: `${pct}%`, transitionDelay: `${delay}ms` }}
        />
      </div>
    </div>
  );
}

const STATUS_META: Record<string, { label: string; tone: Embryo['tone'] }> = {
  under_clinical_review: { label: 'Under Clinical Review', tone: 'attention' },
  selected_for_transfer: { label: 'Selected for Transfer', tone: 'active' },
  cryopreserved: { label: 'Cryopreserved', tone: 'completed' },
  not_suitable_for_transfer: { label: 'Not Suitable for Transfer', tone: 'cancelled' },
  transferred: { label: 'Transferred', tone: 'completed' },
  discarded: { label: 'Discarded', tone: 'cancelled' },
};

function toEmbryoViewModel(e: EmbryoOut, storageAddress: string | null, frozenAt: string | null): Embryo {
  const meta = STATUS_META[e.status] ?? { label: e.status, tone: 'neutral' as const };
  return {
    id: e.label,
    day: e.day,
    grade: e.grade,
    expansion: e.expansion ?? '—',
    icm: e.icm_grade ?? '—',
    trophectoderm: e.trophectoderm_grade ?? '—',
    status: meta.label,
    tone: meta.tone,
    note: e.embryologist_notes ?? '',
    score: e.quality_score ?? 0,
    storage: storageAddress ?? undefined,
    frozen: frozenAt ? new Date(frozenAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : undefined,
  };
}

export function Embryology() {
  const { go, toast, selectedPatientId } = useApp();
  const [detail, setDetail] = useState<Embryo | null>(null);

  const coupleQuery = useCoupleForPatient(selectedPatientId);
  const cycleQuery = useActiveCycle(coupleQuery.data?.id ?? null);
  const embryosQuery = useEmbryosForCycle(cycleQuery.data?.id ?? null);
  const locationsQuery = useCryoLocationsForCycle(cycleQuery.data?.id ?? null);

  const realEmbryos = embryosQuery.data ?? [];
  const hasRealData = realEmbryos.length > 0;
  const embryos = useMemo(() => {
    if (!hasRealData) return EMBRYOS;
    const locByEmbryoId = new Map((locationsQuery.data ?? []).map((l) => [l.embryo_id, l]));
    return realEmbryos.map((e) => {
      const loc = locByEmbryoId.get(e.id);
      const address = loc ? `${loc.tank} / ${loc.canister} / ${loc.cane} / ${loc.goblet} / ${loc.straw}` : null;
      return toEmbryoViewModel(e, address, loc?.frozen_at ?? null);
    });
  }, [hasRealData, realEmbryos, locationsQuery.data]);

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <SectionTitle
          eyebrow="Laboratory"
          title="Embryology Workspace"
          description={
            cycleQuery.data
              ? `Cycle ${cycleQuery.data.cycle_number} · ICSI · Embryologist Dr. Meera Kapoor`
              : `Cycle ${PATIENT.cycleId} · ${PATIENT.name} · ICSI · Embryologist Dr. Meera Kapoor`
          }
        />
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button icon={<Snowflake className="h-4 w-4" />} onClick={() => go('cryostorage')}>
            Cryostorage
          </Button>
          <Button variant="primary" icon={<ArrowRight className="h-4 w-4" />} onClick={() => go('transfer')}>
            Proceed to Transfer
          </Button>
        </div>
      </div>

      {/* ============ FERTILISATION FUNNEL ============ */}
      <Card>
        <CardHeader
          icon={<Beaker className="h-4 w-4" />}
          title="Fertilisation & Development Summary"
          subtitle="Oocyte retrieval performed 2 August 2026 · Extended culture to Day 5/6"
        />
        <div className="grid grid-cols-2 gap-3 px-5 pb-5 md:grid-cols-5">
          {EMBRYO_SUMMARY.map((s, i) => (
            <FunnelStat
              key={s.label}
              value={s.value}
              label={s.label}
              sub={s.sub}
              pct={(s.value / EMBRYO_SUMMARY[0].value) * 100}
              delay={i * 90}
            />
          ))}
        </div>
      </Card>

      {/* ============ EMBRYO CARDS ============ */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-[15px] font-semibold tracking-[-0.011em] text-ink-900">
            Blastocyst Cohort
            <span className="ml-2 text-[13px] font-normal text-ink-500">
              {embryos.length} embryos graded
            </span>
          </h3>
          <div className="flex items-center gap-3 text-[11.5px] text-ink-400">
            <span>Gardner grading system</span>
          </div>
        </div>

        <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {embryos.map((e, i) => (
            <Card
              key={e.id}
              style={{ ['--i' as string]: i }}
              interactive
              onClick={() => setDetail(e)}
              className={cn(
                'group overflow-hidden',
                e.status === 'Selected for Transfer' && 'border-brand-400 ring-1 ring-brand-500/20'
              )}
            >
              {e.status === 'Selected for Transfer' && (
                <div className="flex items-center gap-1.5 bg-gradient-to-r from-brand-600 to-brand-700 px-4 py-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                  <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-white">
                    Selected for transfer
                  </span>
                </div>
              )}

              <div className="flex gap-4 p-4">
                <div className="relative">
                  <EmbryoVisual embryo={e} size={92} />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="tnum text-[17px] font-semibold tracking-[-0.014em] text-ink-900">
                        {e.id}
                      </p>
                      <p className="text-[11.5px] text-ink-500">Day {e.day} blastocyst</p>
                    </div>
                    <span className="tnum rounded-lg bg-ink-900 px-2 py-1 text-[12px] font-bold text-white">
                      {e.grade}
                    </span>
                  </div>

                  <div className="mt-2.5">
                    <div className="mb-1 flex justify-between text-[10.5px]">
                      <span className="text-ink-400">Quality score</span>
                      <span className="tnum font-semibold text-ink-700">{e.score}</span>
                    </div>
                    <ProgressBar
                      value={e.score}
                      height={5}
                      tone={e.score >= 85 ? 'brand' : e.score >= 60 ? 'amber' : 'rose'}
                    />
                  </div>

                  <div className="mt-3">
                    <Badge tone={e.tone} size="sm">
                      {e.status}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="border-t border-ink-100 bg-ink-50/50 px-4 py-2.5">
                <p className="line-clamp-2 text-[11.5px] leading-relaxed text-ink-500">{e.note}</p>
                {e.storage && (
                  <p className="mt-1.5 flex items-center gap-1 text-[10.5px] font-medium text-sky-700">
                    <Snowflake className="h-3 w-3" /> {e.storage}
                  </p>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      <InfoNote tone="neutral" icon={<Info className="h-4 w-4" />}>
        Embryo grading follows the Gardner system — expansion (1–6), inner cell mass (A–C) and
        trophectoderm (A–C). Grading is performed independently by the embryologist and reviewed
        jointly with the treating clinician before transfer selection.
      </InfoNote>

      {/* ============ DETAIL MODAL ============ */}
      <Modal
        open={!!detail}
        onClose={() => setDetail(null)}
        title={detail ? `Embryo ${detail.id} — Grade ${detail.grade}` : ''}
        subtitle={detail ? `Day ${detail.day} · Cycle ${cycleQuery.data?.cycle_number ?? PATIENT.cycleId}` : ''}
        width="max-w-2xl"
        footer={
          detail && (
            <>
              <Button onClick={() => setDetail(null)}>Close</Button>
              {detail.status === 'Selected for Transfer' && (
                <Button
                  variant="primary"
                  icon={<ClipboardCheck className="h-4 w-4" />}
                  onClick={() => {
                    setDetail(null);
                    go('transfer');
                  }}
                >
                  Open Transfer Workspace
                </Button>
              )}
              {detail.status === 'Under Clinical Review' && (
                <Button
                  variant="primary"
                  onClick={() => {
                    toast({ title: `Embryo ${detail.id} reviewed`, body: 'Clinical decision recorded and witnessed.', tone: 'success' });
                    setDetail(null);
                  }}
                >
                  Record Clinical Decision
                </Button>
              )}
            </>
          )
        }
      >
        {detail && (
          <div className="space-y-5">
            <div className="flex gap-5 rounded-xl bg-ink-50 p-4">
              <EmbryoVisual embryo={detail} size={124} />
              <div className="min-w-0 flex-1">
                <Badge tone={detail.tone}>{detail.status}</Badge>
                <p className="mt-3 text-[13px] leading-relaxed text-ink-600">{detail.note}</p>
                <div className="mt-3">
                  <div className="mb-1 flex justify-between text-[11px]">
                    <span className="text-ink-500">Composite quality score</span>
                    <span className="tnum font-semibold text-ink-800">{detail.score} / 100</span>
                  </div>
                  <ProgressBar value={detail.score} tone={detail.score >= 85 ? 'brand' : detail.score >= 60 ? 'amber' : 'rose'} />
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Expansion" value={detail.expansion} />
              <Field label="Grade" value={detail.grade} mono />
              <Field label="Inner Cell Mass" value={detail.icm} />
              <Field label="Trophectoderm" value={detail.trophectoderm} />
              <Field label="Development Day" value={`Day ${detail.day}`} />
              <Field label="Embryologist" value="Dr. Meera Kapoor" />
              {detail.storage && <Field label="Storage Location" value={detail.storage} />}
              {detail.frozen && <Field label="Vitrification Date" value={detail.frozen} />}
            </div>

            <InfoNote tone="brand" icon={<Layers className="h-4 w-4" />}>
              All embryo handling is double-witnessed. Identity verification was completed by
              Dr. Meera Kapoor and Anand Kumar (Laboratory Technician) at each transfer point.
            </InfoNote>
          </div>
        )}
      </Modal>
    </div>
  );
}
