'use client';

import React, { useState } from 'react';
import { useApp } from '@/lib/store';
import { TRANSFER_CHECKLIST, EMBRYOS, PATIENT, PARTNER } from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Field, InfoNote, Modal } from '@/components/ui/primitives';
import {
  Check,
  ShieldCheck,
  Baby,
  Stethoscope,
  FileSignature,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export function Transfer() {
  const { go, toast, completeTransfer, transferComplete } = useApp();
  const [checked, setChecked] = useState<string[]>([]);
  const [confirm, setConfirm] = useState(false);
  const [running, setRunning] = useState(false);

  const embryo = EMBRYOS.find((e) => e.id === 'E-01')!;
  const allChecked = checked.length === TRANSFER_CHECKLIST.length;

  const toggle = (id: string) =>
    setChecked((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id]));

  const checkAll = () => setChecked(TRANSFER_CHECKLIST.map((c) => c.id));

  const runTransfer = () => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      setConfirm(false);
      completeTransfer();
      toast({
        title: 'Embryo transfer completed',
        body: 'Procedure recorded. Luteal support prescribed. Beta-hCG scheduled for 21 August 2026.',
        tone: 'success',
      });
      setTimeout(() => go('pregnancy'), 900);
    }, 1900);
  };

  return (
    <div className="screen-enter mx-auto max-w-[1200px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Procedure"
        title="Embryo Transfer"
        description={`${PATIENT.name} · Transfer date 7 August 2026 · Ultrasound-guided single blastocyst transfer`}
        action={
          transferComplete ? (
            <Badge tone="completed">Transfer completed</Badge>
          ) : (
            <Badge tone="scheduled">Awaiting sign-off</Badge>
          )
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ============ SELECTED EMBRYO ============ */}
        <Card className="overflow-hidden">
          <div className="bg-gradient-to-br from-brand-600 to-brand-800 p-5 text-white">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-200" />
              <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-brand-200">
                Selected Embryo
              </span>
            </div>
            <p className="tnum tracking-display mt-2 text-[38px] font-semibold leading-none">
              {embryo.id}
            </p>
            <div className="mt-3 flex items-center gap-3">
              <span className="tnum rounded-lg bg-white/15 px-2.5 py-1 text-[13px] font-bold ring-1 ring-inset ring-white/20">
                Grade {embryo.grade}
              </span>
              <span className="text-[13px] text-brand-100">Day {embryo.day} blastocyst</span>
            </div>
          </div>

          <div className="p-5">
            <Field label="Expansion" value={embryo.expansion} />
            <div className="mt-3.5">
              <Field label="Inner Cell Mass" value={embryo.icm} />
            </div>
            <div className="mt-3.5">
              <Field label="Trophectoderm" value={embryo.trophectoderm} />
            </div>
            <div className="mt-3.5">
              <Field label="Number of Embryos" value="1 — elective single transfer" />
            </div>
            <div className="mt-3.5">
              <Field label="Procedure Doctor" value="Dr. Archana S. Ayyanathan" />
            </div>
            <div className="mt-3.5">
              <Field label="Embryologist" value="Dr. Meera Kapoor" />
            </div>

            <div className="mt-4">
              <InfoNote tone="brand" icon={<ShieldCheck className="h-4 w-4" />}>
                Consent verified — signed by both partners on 6 August 2026.
              </InfoNote>
            </div>
          </div>
        </Card>

        {/* ============ CHECKLIST ============ */}
        <Card className="lg:col-span-2">
          <CardHeader
            icon={<ShieldCheck className="h-4 w-4" />}
            title="Pre-Transfer Safety Verification"
            subtitle="All six checks must be confirmed before the procedure can proceed"
            action={
              !allChecked &&
              !transferComplete && (
                <Button size="sm" variant="ghost" onClick={checkAll}>
                  Verify all
                </Button>
              )
            }
          />

          <div className="px-5">
            {/* progress */}
            <div className="mb-4 flex items-center gap-3 rounded-xl bg-ink-50 p-3">
              <div className="flex-1">
                <div className="mb-1.5 flex justify-between text-[11.5px]">
                  <span className="font-medium text-ink-600">Verification progress</span>
                  <span className="tnum font-semibold text-ink-900">
                    {checked.length} of {TRANSFER_CHECKLIST.length}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-ink-200">
                  <div
                    className={cn(
                      'h-full rounded-full transition-[width] duration-500 ease-spring',
                      allChecked ? 'bg-gradient-to-r from-brand-400 to-brand-600' : 'bg-gradient-to-r from-amber-400 to-amber-500'
                    )}
                    style={{ width: `${(checked.length / TRANSFER_CHECKLIST.length) * 100}%` }}
                  />
                </div>
              </div>
              {allChecked && (
                <Badge tone="completed" className="animate-scale-in">
                  Ready
                </Badge>
              )}
            </div>

            {/* items */}
            <div className="stagger space-y-2 pb-5">
              {TRANSFER_CHECKLIST.map((c, i) => {
                const on = checked.includes(c.id) || transferComplete;
                return (
                  <button
                    key={c.id}
                    disabled={transferComplete}
                    onClick={() => toggle(c.id)}
                    style={{ ['--i' as string]: i }}
                    className={cn(
                      'flex w-full items-start gap-3.5 rounded-xl border p-3.5 text-left transition-all duration-250',
                      on
                        ? 'border-brand-300 bg-brand-50/50'
                        : 'border-ink-200/70 bg-white hover:border-ink-300 hover:bg-ink-50/60'
                    )}
                  >
                    <div
                      className={cn(
                        'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition-all duration-250',
                        on ? 'border-brand-600 bg-brand-600' : 'border-ink-300 bg-white'
                      )}
                    >
                      {on && (
                        <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20 6L9 17l-5-5" className="tick-path" />
                        </svg>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className={cn('text-[13.5px] font-medium', on ? 'text-brand-900' : 'text-ink-800')}>
                        {c.label}
                      </p>
                      <p className="mt-0.5 text-[12px] leading-relaxed text-ink-500">{c.detail}</p>
                    </div>
                    {on && <Check className="mt-1 h-4 w-4 shrink-0 text-brand-600" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-ink-100 bg-ink-50/50 p-5">
            {!allChecked && !transferComplete && (
              <InfoNote tone="amber" icon={<AlertTriangle className="h-4 w-4" />}>
                Complete every verification step before proceeding. This checklist forms part of the
                permanent medical record and is auditable.
              </InfoNote>
            )}

            {transferComplete ? (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600">
                    <Check className="h-5 w-5 text-white" strokeWidth={3} />
                  </div>
                  <div>
                    <p className="text-[13.5px] font-semibold text-ink-900">Transfer completed</p>
                    <p className="text-[12px] text-ink-500">Recorded 7 August 2026, 11:42 AM</p>
                  </div>
                </div>
                <Button variant="primary" iconRight={<ArrowRight className="h-4 w-4" />} onClick={() => go('pregnancy')}>
                  View Pregnancy Follow-up
                </Button>
              </div>
            ) : (
              <Button
                variant="primary"
                size="lg"
                className="mt-4 w-full"
                disabled={!allChecked}
                icon={<Baby className="h-4 w-4" />}
                onClick={() => setConfirm(true)}
              >
                Complete Embryo Transfer
              </Button>
            )}
          </div>
        </Card>
      </div>

      {/* ============ CONFIRM MODAL ============ */}
      <Modal
        open={confirm}
        onClose={() => !running && setConfirm(false)}
        title="Confirm embryo transfer"
        subtitle="This action is final and will be recorded in the permanent medical record."
        footer={
          <>
            <Button onClick={() => setConfirm(false)} disabled={running}>
              Cancel
            </Button>
            <Button variant="primary" loading={running} icon={<Check className="h-4 w-4" />} onClick={runTransfer}>
              {running ? 'Recording procedure…' : 'Confirm & Complete'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-brand-200 bg-brand-50/60 p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Patient" value={`${PATIENT.name} — ${PATIENT.id}`} />
              <Field label="Partner" value={`${PARTNER.name} — ${PARTNER.id}`} />
              <Field label="Embryo" value={`${embryo.id} · Day ${embryo.day} · Grade ${embryo.grade}`} />
              <Field label="Procedure Date" value="7 August 2026" />
              <Field label="Clinician" value="Dr. Archana S. Ayyanathan" />
              <Field label="Embryologist" value="Dr. Meera Kapoor" />
            </div>
          </div>

          <InfoNote tone="neutral" icon={<FileSignature className="h-4 w-4" />}>
            All six safety verifications have been confirmed. A double-witness signature will be
            captured and the event written to the audit trail with a timestamp.
          </InfoNote>
        </div>
      </Modal>
    </div>
  );
}
