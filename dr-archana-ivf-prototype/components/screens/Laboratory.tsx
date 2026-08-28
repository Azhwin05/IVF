'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { LAB_ORDERS, LAB_METRICS, LAB_TEST_CATALOGUE } from '@/lib/data';
import { cn, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, InfoNote } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { useLabOrders, type LabOrderStatus } from '@/lib/api/laboratory';
import { useLabTestCatalogue } from '@/lib/api/administration';
import { usePatients } from '@/lib/api/patients';
import {
  FlaskConical,
  Search,
  ClipboardList,
  Beaker,
  CheckCircle2,
  Building2,
  Plus,
  FileText,
  AlertTriangle,
} from 'lucide-react';

const FILTERS = ['All', 'Ordered', 'Sample Collected', 'In Progress', 'Report Ready', 'Delivered'];
const STATUS_MAP: Record<string, LabOrderStatus> = {
  Ordered: 'ordered',
  'Sample Collected': 'sample_collected',
  'In Progress': 'in_progress',
  'Report Ready': 'report_ready',
  Delivered: 'delivered',
};
const STATUS_LABEL: Record<LabOrderStatus, string> = {
  ordered: 'Ordered',
  sample_collected: 'Sample Collected',
  in_progress: 'In Progress',
  report_ready: 'Report Ready',
  delivered: 'Delivered',
};
const STATUS_TONE: Record<LabOrderStatus, keyof typeof TONE> = {
  ordered: 'scheduled',
  sample_collected: 'attention',
  in_progress: 'active',
  report_ready: 'completed',
  delivered: 'neutral',
};

function Metric({ label, value, icon: Icon, tone }: { label: string; value: number; icon: any; tone: string }) {
  const v = useCountUp(value, 1000);
  return (
    <Card className="p-4">
      <div className={cn('flex h-9 w-9 items-center justify-center rounded-xl ring-1 ring-inset', tone)}>
        <Icon className="h-[18px] w-[18px]" />
      </div>
      <p className="tnum tracking-display mt-3 text-[24px] font-semibold leading-none text-ink-900">{Math.round(v)}</p>
      <p className="mt-1.5 text-[13px] font-medium text-ink-600">{label}</p>
    </Card>
  );
}

export function Laboratory() {
  const { toast } = useApp();
  const [q, setQ] = useState('');
  const [filter, setFilter] = useState('All');

  const ordersQuery = useLabOrders();
  const catalogueQuery = useLabTestCatalogue();
  const patientsQuery = usePatients();
  const hasRealData = (ordersQuery.data ?? []).length > 0;

  const patientNameById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of patientsQuery.data ?? []) map[p.id] = p.full_name;
    return map;
  }, [patientsQuery.data]);

  const realRows = useMemo(
    () =>
      (ordersQuery.data ?? []).map((o) => ({
        id: o.order_number,
        test: o.test_name,
        patient: patientNameById[o.patient_id] ?? 'Unknown patient',
        patientId: null as string | null,
        status: STATUS_LABEL[o.status],
        tone: STATUS_TONE[o.status],
        priority: o.priority === 'urgent' ? 'Urgent' : 'Routine',
        source: o.source === 'internal_lab' ? 'Internal Lab' : 'External Lab',
        orderedBy: 'Clinical staff',
        orderedOn: new Date(o.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
        sampleType: o.sample_type ?? '—',
        externalLab: o.external_lab_name,
      })),
    [ordersQuery.data, patientNameById]
  );

  const catalogue = catalogueQuery.data?.length
    ? catalogueQuery.data.map((t) => ({ test: t.test_name, price: Math.round(t.price_paise / 100), tat: t.turnaround_time }))
    : LAB_TEST_CATALOGUE;

  const rows = useMemo(() => {
    const base = hasRealData ? realRows : LAB_ORDERS.map((o) => ({ ...o, patientId: o.patientId ?? null, externalLab: o.externalLab ?? null }));
    let r = base;
    if (filter !== 'All') r = r.filter((o) => o.status === filter);
    if (q.trim()) {
      const t = q.toLowerCase();
      r = r.filter((o) => o.patient.toLowerCase().includes(t) || o.test.toLowerCase().includes(t) || o.id.toLowerCase().includes(t));
    }
    return r;
  }, [q, filter, hasRealData, realRows]);

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Operations"
        title="Laboratory Management"
        description="Test ordering, sample tracking and digital reports across internal and external labs"
        action={
          <Button
            variant="primary"
            icon={<Plus className="h-4 w-4" />}
            onClick={() => toast({ title: 'New lab order', body: 'Test order form opened.', tone: 'info' })}
          >
            New Order
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 xl:grid-cols-5">
        {hasRealData ? (
          <>
            <Metric label="Total Orders" value={realRows.length} icon={ClipboardList} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
            <Metric label="Awaiting Collection" value={realRows.filter((o) => o.status === 'Ordered').length} icon={Beaker} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
            <Metric label="In Progress" value={realRows.filter((o) => o.status === 'Sample Collected' || o.status === 'In Progress').length} icon={FlaskConical} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
            <Metric label="Reports Ready" value={realRows.filter((o) => o.status === 'Report Ready').length} icon={CheckCircle2} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
            <Metric label="External" value={realRows.filter((o) => o.source === 'External Lab').length} icon={Building2} tone="bg-violet-50 text-violet-700 ring-violet-600/12" />
          </>
        ) : (
          <>
            <Metric label="Orders Today" value={LAB_METRICS.ordersToday} icon={ClipboardList} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
            <Metric label="Awaiting Collection" value={LAB_METRICS.awaitingCollection} icon={Beaker} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
            <Metric label="In Progress" value={LAB_METRICS.inProgress} icon={FlaskConical} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
            <Metric label="Reports Ready" value={LAB_METRICS.reportsReady} icon={CheckCircle2} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
            <Metric label="External Pending" value={LAB_METRICS.externalPending} icon={Building2} tone="bg-violet-50 text-violet-700 ring-violet-600/12" />
          </>
        )}
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <div className="min-w-0 space-y-4 xl:col-span-2">
          <Card className="p-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              <div className="lg:min-w-[220px] lg:flex-1">
                <Input placeholder="Search patient, test or order ID…" icon={<Search className="h-3.5 w-3.5" />} value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
              <div className="scroll-area flex min-w-0 gap-1 overflow-x-auto rounded-lg bg-ink-100 p-1">
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
            </div>
          </Card>

          <Card className="overflow-hidden">
            <div className="stagger">
              {rows.map((o, i) => (
                <div
                  key={o.id}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-col gap-2.5 border-b border-ink-100 p-4 last:border-0 hover:bg-ink-50/60"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="tnum text-[13px] font-semibold text-ink-500">{o.id}</span>
                        {o.priority === 'Urgent' && (
                          <Badge tone="critical" size="sm" dot={false}>
                            <AlertTriangle className="mr-0.5 h-2.5 w-2.5" /> Urgent
                          </Badge>
                        )}
                        <Badge tone={o.source === 'Internal Lab' ? 'scheduled' : 'neutral'} size="sm">
                          {o.source}
                        </Badge>
                      </div>
                      <p className="mt-1 text-[14.5px] font-semibold text-ink-900">{o.test}</p>
                      <p className="text-[13px] text-ink-500">
                        {o.patient} {o.patientId && <span className="tnum text-ink-400">· {o.patientId}</span>}
                      </p>
                    </div>
                    <Badge tone={o.tone} size="sm">
                      {o.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-ink-400">
                    <span>Ordered by {o.orderedBy}</span>
                    <span className="tnum">{o.orderedOn}</span>
                    <span>{o.sampleType}</span>
                    {o.externalLab && <span>{o.externalLab}</span>}
                  </div>
                </div>
              ))}
            </div>
            {rows.length === 0 && (
              <div className="px-5 py-14 text-center">
                <p className="text-[14.5px] text-ink-500">No lab orders match your filters</p>
              </div>
            )}
          </Card>
        </div>

        <Card>
          <CardHeader icon={<FileText className="h-4 w-4" />} title="Lab Test Catalogue" subtitle="Standard pricing and turnaround time" />
          <div className="stagger px-5 pb-5">
            {catalogue.map((t, i) => (
              <div key={t.test} style={{ ['--i' as string]: i }} className="flex items-center justify-between gap-3 border-b border-ink-100 py-2.5 last:border-0">
                <div className="min-w-0">
                  <p className="truncate text-[13.5px] font-medium text-ink-800">{t.test}</p>
                  <p className="text-[12px] text-ink-400">TAT {t.tat}</p>
                </div>
                <span className="tnum shrink-0 text-[14px] font-semibold text-ink-900">₹{t.price.toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-ink-100 p-5">
            <InfoNote tone="brand" icon={<Building2 className="h-4 w-4" />}>
              External lab results sync automatically once uploaded by the partner laboratory and
              attach directly to the patient&apos;s investigations record.
            </InfoNote>
          </div>
        </Card>
      </div>
    </div>
  );
}
