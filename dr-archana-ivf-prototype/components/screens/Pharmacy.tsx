'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { PHARMACY_ITEMS, PHARMACY_SALES, PHARMACY_METRICS } from '@/lib/data';
import { cn, formatINR, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, ProgressBar, Tabs } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { Pill, Search, IndianRupee, AlertTriangle, CalendarX2, Package, Plus, Receipt } from 'lucide-react';

function Metric({ label, value, icon: Icon, tone, currency }: { label: string; value: number; icon: any; tone: string; currency?: boolean }) {
  const v = useCountUp(value, 1000);
  return (
    <Card className="p-4">
      <div className={cn('flex h-9 w-9 items-center justify-center rounded-xl ring-1 ring-inset', tone)}>
        <Icon className="h-[18px] w-[18px]" />
      </div>
      <p className="tnum tracking-display mt-3 text-[22px] font-semibold leading-none text-ink-900">
        {currency ? formatINR(Math.round(v), true) : Math.round(v)}
      </p>
      <p className="mt-1.5 text-[12px] font-medium text-ink-600">{label}</p>
    </Card>
  );
}

export function Pharmacy() {
  const { toast } = useApp();
  const [tab, setTab] = useState('stock');
  const [q, setQ] = useState('');

  const items = useMemo(() => {
    if (!q.trim()) return PHARMACY_ITEMS;
    const t = q.toLowerCase();
    return PHARMACY_ITEMS.filter((i) => i.name.toLowerCase().includes(t) || i.category.toLowerCase().includes(t));
  }, [q]);

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Operations"
        title="Pharmacy Management"
        description="Medicine catalogue, stock, dispensing and GST-ready sales"
        action={
          <Button
            variant="primary"
            icon={<Plus className="h-4 w-4" />}
            onClick={() => toast({ title: 'New sale', body: 'Dispensing screen opened.', tone: 'info' })}
          >
            New Sale
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
        <Metric label="Today's Sales" value={PHARMACY_METRICS.todaySales} icon={IndianRupee} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" currency />
        <Metric label="Below Reorder Level" value={PHARMACY_METRICS.itemsBelowReorder} icon={AlertTriangle} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
        <Metric label="Expiring in 90 Days" value={PHARMACY_METRICS.expiringWithin90Days} icon={CalendarX2} tone="bg-rose-50 text-rose-700 ring-rose-600/12" />
        <Metric label="Total SKUs" value={PHARMACY_METRICS.totalSKUs} icon={Package} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
      </div>

      <Card className="overflow-hidden">
        <div className="px-4 pt-2">
          <Tabs
            tabs={[
              { id: 'stock', label: 'Medicine Stock', count: PHARMACY_ITEMS.length },
              { id: 'sales', label: 'Recent Dispensing', count: PHARMACY_SALES.length },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>

        {tab === 'stock' && (
          <div className="animate-fade-up p-5">
            <div className="mb-4">
              <Input placeholder="Search medicine or category…" icon={<Search className="h-3.5 w-3.5" />} value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            <div className="stagger grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((m, i) => {
                const pct = Math.min((m.stock / (m.reorderLevel * 2)) * 100, 100);
                const low = m.stock < m.reorderLevel;
                return (
                  <Card key={m.id} style={{ ['--i' as string]: i }} className="p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                        <Pill className="h-4 w-4" />
                      </div>
                      {low && (
                        <Badge tone="attention" size="sm">
                          Reorder
                        </Badge>
                      )}
                    </div>
                    <p className="mt-2.5 text-[13px] font-semibold leading-snug text-ink-900">{m.name}</p>
                    <p className="text-[11px] text-ink-500">{m.category}</p>

                    <div className="mt-3">
                      <div className="mb-1 flex justify-between text-[11px]">
                        <span className="text-ink-500">
                          Stock: <span className="tnum font-semibold text-ink-800">{m.stock}</span> {m.unit}
                        </span>
                        <span className="tnum text-ink-400">Min {m.reorderLevel}</span>
                      </div>
                      <ProgressBar value={pct} tone={low ? 'amber' : 'brand'} height={5} />
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 border-t border-ink-100 pt-2.5 text-[11px]">
                      <span className="text-ink-400">Batch</span>
                      <span className="tnum text-right text-ink-700">{m.batch}</span>
                      <span className="text-ink-400">Expiry</span>
                      <span className="tnum text-right text-ink-700">{m.expiry}</span>
                      <span className="text-ink-400">MRP</span>
                      <span className="tnum text-right font-semibold text-ink-900">₹{m.mrp.toLocaleString('en-IN')}</span>
                      <span className="text-ink-400">GST</span>
                      <span className="tnum text-right text-ink-700">{m.gst}%</span>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {tab === 'sales' && (
          <div className="animate-fade-up stagger p-5">
            {PHARMACY_SALES.map((s, i) => (
              <div key={s.id} style={{ ['--i' as string]: i }} className="flex flex-wrap items-center gap-4 border-b border-ink-100 py-3.5 last:border-0">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-100 text-ink-600">
                  <Receipt className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-semibold text-ink-900">
                    {s.patient} <span className="tnum font-normal text-ink-400">· {s.id}</span>
                  </p>
                  <p className="text-[12px] text-ink-500">{s.items}</p>
                  <p className="tnum text-[11px] text-ink-400">{s.date}</p>
                </div>
                <span className="tnum text-[14px] font-semibold text-ink-900">{formatINR(s.amount)}</span>
                <Badge tone={s.tone} size="sm">
                  {s.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
