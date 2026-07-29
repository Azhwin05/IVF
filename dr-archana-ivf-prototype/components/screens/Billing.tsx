'use client';

import React from 'react';
import { useApp } from '@/lib/store';
import { PACKAGE, INVOICES, PATIENT, PARTNER } from '@/lib/data';
import { cn, formatINR, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Field, InfoNote, ProgressBar, Avatar } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { Receipt, Download, IndianRupee, CreditCard, Check, X, Plus, Percent, FileText } from 'lucide-react';

function MoneyTile({ label, value, tone, sub }: { label: string; value: number; tone: 'neutral' | 'completed' | 'attention'; sub: string }) {
  const v = useCountUp(value, 1200);
  return (
    <Card className="p-4">
      <p className="text-[11.5px] font-medium uppercase tracking-[0.06em] text-ink-400">{label}</p>
      <p className={cn('tnum tracking-display mt-1.5 text-[28px] font-semibold leading-none', TONE[tone].text)}>
        {formatINR(Math.round(v))}
      </p>
      <p className="mt-1.5 text-[11.5px] text-ink-500">{sub}</p>
    </Card>
  );
}

export function Billing() {
  const { toast } = useApp();
  const collected = (PACKAGE.paid / PACKAGE.value) * 100;

  return (
    <div className="screen-enter mx-auto max-w-[1300px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Operations"
        title="Billing & IVF Package"
        description={`${PATIENT.name} & ${PARTNER.name} · ${PATIENT.treatment}`}
        action={
          <div className="flex flex-wrap gap-2">
            <Button icon={<Download className="h-4 w-4" />} onClick={() => toast({ title: 'Statement downloaded', body: 'Account statement exported as PDF.', tone: 'success' })}>
              Statement
            </Button>
            <Button
              variant="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => toast({ title: 'Payment recorded', body: '₹75,000 received via UPI. Receipt sent to the couple.', tone: 'success' })}
            >
              Record Payment
            </Button>
          </div>
        }
      />

      {/* ============ MONEY TILES ============ */}
      <div className="grid gap-3.5 sm:grid-cols-3">
        <MoneyTile label="Package Value" value={PACKAGE.value} tone="neutral" sub={PACKAGE.name} />
        <MoneyTile label="Amount Paid" value={PACKAGE.paid} tone="completed" sub="2 instalments received" />
        <MoneyTile label="Outstanding" value={PACKAGE.outstanding} tone="attention" sub="Due before oocyte retrieval" />
      </div>

      {/* ============ PROGRESS ============ */}
      <Card className="p-5">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[13px] font-semibold text-ink-900">Package collection progress</p>
            <p className="text-[12px] text-ink-500">70% of the package value has been collected</p>
          </div>
          <Badge tone="attention">₹75,000 pending</Badge>
        </div>
        <ProgressBar value={collected} height={10} />
        <div className="mt-2 flex justify-between text-[11px] text-ink-400">
          <span className="tnum">{formatINR(0)}</span>
          <span className="tnum">{formatINR(PACKAGE.value)}</span>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ============ INVOICES ============ */}
        <Card className="lg:col-span-2">
          <CardHeader
            icon={<Receipt className="h-4 w-4" />}
            title="Invoice History"
            subtitle={`${INVOICES.length} invoices raised against this treatment case`}
          />

          <div className="overflow-hidden">
            <div className="hidden grid-cols-[1.1fr_2fr_1fr_1fr_90px] gap-4 border-y border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
              {['Invoice', 'Description', 'Amount', 'Method', 'Status'].map((h) => (
                <span key={h} className="text-[10.5px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                  {h}
                </span>
              ))}
            </div>

            <div className="stagger">
              {INVOICES.map((inv, i) => (
                <div
                  key={inv.id}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-col gap-2 border-b border-ink-100 px-4 py-3.5 last:border-0 transition-colors hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[1.1fr_2fr_1fr_1fr_90px] md:items-center md:gap-4"
                >
                  <div className="flex items-center justify-between gap-3 md:block">
                    <div>
                      <p className="tnum text-[12.5px] font-semibold text-ink-900">{inv.id}</p>
                      <p className="text-[11px] text-ink-400">{inv.date}</p>
                    </div>
                    <Badge tone={inv.status === 'Paid' ? 'completed' : 'attention'} size="sm" className="md:hidden">
                      {inv.status}
                    </Badge>
                  </div>
                  <span className="text-[12.5px] text-ink-700">{inv.description}</span>
                  <div className="flex items-center justify-between gap-3 md:contents">
                    <span className="tnum text-[13px] font-semibold text-ink-900">{formatINR(inv.amount)}</span>
                    <span className="text-[12px] text-ink-500">{inv.method}</span>
                  </div>
                  <Badge tone={inv.status === 'Paid' ? 'completed' : 'attention'} size="sm" className="hidden md:inline-flex">
                    {inv.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-100 bg-ink-50/50 px-5 py-4">
            <div className="flex flex-wrap gap-2">
              <Button size="sm" icon={<FileText className="h-3.5 w-3.5" />} onClick={() => toast({ title: 'Receipt generated', body: 'Receipt for INV-2026-1043 is ready to download.', tone: 'success' })}>
                Download receipt
              </Button>
              <Button size="sm" icon={<Percent className="h-3.5 w-3.5" />} onClick={() => toast({ title: 'Discount request sent', body: 'Awaiting management approval.', tone: 'info' })}>
                Request discount
              </Button>
            </div>
            <div className="text-right">
              <p className="text-[11px] text-ink-400">Total billed</p>
              <p className="tnum text-[15px] font-semibold text-ink-900">
                {formatINR(INVOICES.reduce((s, i) => s + i.amount, 0))}
              </p>
            </div>
          </div>
        </Card>

        {/* ============ INCLUSIONS ============ */}
        <Card>
          <CardHeader icon={<CreditCard className="h-4 w-4" />} title="Package Utilisation" subtitle="What this package covers" />
          <div className="stagger px-5 pb-5">
            {PACKAGE.inclusions.map((inc, i) => {
              const included = inc.status === 'Included';
              const additional = inc.status === 'Additional';
              return (
                <div
                  key={inc.item}
                  style={{ ['--i' as string]: i }}
                  className="flex items-center gap-2.5 border-b border-ink-100 py-2.5 last:border-0"
                >
                  <div
                    className={cn(
                      'flex h-5 w-5 shrink-0 items-center justify-center rounded-full',
                      included ? 'bg-brand-600' : additional ? 'bg-sky-100 ring-1 ring-sky-300' : 'bg-ink-100 ring-1 ring-ink-200'
                    )}
                  >
                    {included ? (
                      <Check className="h-3 w-3 text-white" strokeWidth={3.5} />
                    ) : additional ? (
                      <Plus className="h-3 w-3 text-sky-600" strokeWidth={3} />
                    ) : (
                      <X className="h-3 w-3 text-ink-400" strokeWidth={3} />
                    )}
                  </div>
                  <span className="min-w-0 flex-1 text-[12.5px] text-ink-700">{inc.item}</span>
                  <span
                    className={cn(
                      'text-[11px] font-medium',
                      included ? 'text-brand-700' : additional ? 'text-sky-700' : 'text-ink-400'
                    )}
                  >
                    {inc.status}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="border-t border-ink-100 p-5">
            <InfoNote tone="neutral" icon={<IndianRupee className="h-4 w-4" />}>
              Stimulation medicines and additional investigations are billed separately at actuals.
              Cryostorage is charged annually per straw.
            </InfoNote>
          </div>
        </Card>
      </div>
    </div>
  );
}
