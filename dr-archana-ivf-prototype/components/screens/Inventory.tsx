'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { INVENTORY_ITEMS, PURCHASE_ORDERS, INVENTORY_METRICS, type StatusTone } from '@/lib/data';
import { cn, formatINR, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, Tabs, Modal } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { useInventoryItems, useReserveStock, type InventoryCategory } from '@/lib/api/inventory';
import { usePurchaseOrders } from '@/lib/api/purchasing';
import { ApiError } from '@/lib/api/client';
import { Boxes, Search, AlertTriangle, Snowflake, IndianRupee, Plus, MapPin, Truck, PackageCheck } from 'lucide-react';

function ReserveStockModal({ item, open, onClose }: { item: { id: string; name: string; unit: string; availableQty: number } | null; open: boolean; onClose: () => void }) {
  const { toast } = useApp();
  const reserve = useReserveStock();
  const [quantity, setQuantity] = useState('');
  const [procedureType, setProcedureType] = useState('');
  const [procedureId, setProcedureId] = useState('');
  const [error, setError] = useState<string | null>(null);

  const reset = () => { setQuantity(''); setProcedureType(''); setProcedureId(''); setError(null); };

  const submit = () => {
    if (!item) return;
    setError(null);
    reserve.mutate(
      { item_id: item.id, quantity: Number(quantity), procedure_entity_type: procedureType, procedure_entity_id: procedureId },
      {
        onSuccess: () => { toast({ title: 'Stock reserved', body: `${quantity} ${item.unit} of ${item.name} held.`, tone: 'success' }); reset(); onClose(); },
        onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not reserve stock.'),
      }
    );
  };

  return (
    <Modal open={open} onClose={() => { reset(); onClose(); }} title="Reserve Stock" subtitle={item ? `${item.name} — ${item.availableQty} ${item.unit} available` : ''}>
      <div className="space-y-4">
        <Input label="Quantity" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        <Input label="Procedure Type" placeholder="e.g. OTProcedure, IVFCycle" value={procedureType} onChange={(e) => setProcedureType(e.target.value)} />
        <Input label="Procedure Reference" placeholder="Procedure/cycle ID" value={procedureId} onChange={(e) => setProcedureId(e.target.value)} />
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
            <p className="text-[13.5px] leading-relaxed text-rose-700">{error}</p>
          </div>
        )}
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={() => { reset(); onClose(); }}>Cancel</Button>
        <Button variant="primary" loading={reserve.isPending} disabled={!quantity || !procedureType || !procedureId} onClick={submit}>
          {reserve.isPending ? 'Reserving…' : 'Reserve'}
        </Button>
      </div>
    </Modal>
  );
}

const CATEGORIES = ['All', 'IVF Consumables', 'Cryogenic Supplies', 'Lab Supplies', 'Surgical Equipment'];
const CATEGORY_TO_REAL: Record<string, InventoryCategory> = {
  'IVF Consumables': 'ivf_consumables',
  'Cryogenic Supplies': 'cryogenic_supplies',
  'Lab Supplies': 'lab_supplies',
  'Surgical Equipment': 'surgical_equipment',
};
const REAL_TO_CATEGORY: Record<InventoryCategory, string> = {
  ivf_consumables: 'IVF Consumables',
  cryogenic_supplies: 'Cryogenic Supplies',
  lab_supplies: 'Lab Supplies',
  surgical_equipment: 'Surgical Equipment',
};
const PO_STATUS_LABEL: Record<string, string> = {
  pending_approval: 'Pending Approval',
  approved: 'Approved',
  dispatched: 'Dispatched',
  received: 'Received',
  rejected: 'Rejected',
};
const PO_STATUS_TONE: Record<string, keyof typeof TONE> = {
  pending_approval: 'attention',
  approved: 'scheduled',
  dispatched: 'active',
  received: 'completed',
  rejected: 'cancelled',
};

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
      <p className="mt-1.5 text-[13px] font-medium text-ink-600">{label}</p>
    </Card>
  );
}

export function Inventory() {
  const { toast } = useApp();
  const [tab, setTab] = useState('stock');
  const [q, setQ] = useState('');
  const [cat, setCat] = useState('All');
  const [reserveItem, setReserveItem] = useState<{ id: string; name: string; unit: string; availableQty: number } | null>(null);

  const itemsQuery = useInventoryItems();
  const ordersQuery = usePurchaseOrders();
  const hasRealItems = (itemsQuery.data ?? []).length > 0;

  const realItems = useMemo(
    () =>
      (itemsQuery.data ?? []).map((it) => {
        const low = it.stock < it.reorder_level;
        const critical = it.stock === 0 || it.stock < it.reorder_level / 2;
        return {
          id: it.id,
          name: it.name,
          category: REAL_TO_CATEGORY[it.category],
          stock: it.stock,
          reservedQty: it.reserved_qty,
          availableQty: it.available_qty,
          unit: it.unit,
          reorderLevel: it.reorder_level,
          location: it.location ?? '—',
          supplier: it.supplier ?? '—',
          lastRestocked: it.last_restocked ? new Date(it.last_restocked).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—',
          status: critical ? 'Critical' : low ? 'Low Stock' : 'In Stock',
          tone: (critical ? 'critical' : low ? 'attention' : 'completed') as StatusTone,
        };
      }),
    [itemsQuery.data]
  );

  const realOrders = useMemo(
    () =>
      (ordersQuery.data ?? []).map((po) => ({
        id: po.po_number,
        item: po.item_description,
        supplier: po.supplier,
        qty: po.quantity_ordered,
        amount: Math.round(po.amount_paise / 100),
        date: '',
        status: PO_STATUS_LABEL[po.status] ?? po.status,
        tone: PO_STATUS_TONE[po.status] ?? ('neutral' as const),
      })),
    [ordersQuery.data]
  );

  const items = useMemo(() => {
    let r = hasRealItems ? realItems : INVENTORY_ITEMS.map((i) => ({ ...i, reservedQty: 0, availableQty: i.stock }));
    if (cat !== 'All') r = r.filter((i) => i.category === cat);
    if (q.trim()) {
      const t = q.toLowerCase();
      r = r.filter((i) => i.name.toLowerCase().includes(t));
    }
    return r;
  }, [q, cat, hasRealItems, realItems]);

  const purchaseOrders = hasRealItems && ordersQuery.data ? realOrders : PURCHASE_ORDERS;

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <ReserveStockModal item={reserveItem} open={!!reserveItem} onClose={() => setReserveItem(null)} />
      <SectionTitle
        eyebrow="Operations"
        title="Inventory Management"
        description="IVF consumables, cryogenic supplies, lab materials and equipment"
        action={
          <Button
            variant="primary"
            icon={<Plus className="h-4 w-4" />}
            onClick={() => toast({ title: 'Purchase order created', body: 'Draft PO opened for vendor selection.', tone: 'info' })}
          >
            New Purchase Order
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
        {hasRealItems ? (
          <>
            <Metric label="Total Items" value={realItems.length} icon={Boxes} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
            <Metric label="Low Stock" value={realItems.filter((i) => i.status === 'Low Stock').length} icon={AlertTriangle} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
            <Metric label="Critical" value={realItems.filter((i) => i.status === 'Critical').length} icon={Snowflake} tone="bg-rose-50 text-rose-700 ring-rose-600/12" />
            <Metric label="Purchase Orders" value={realOrders.length} icon={IndianRupee} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
          </>
        ) : (
          <>
            <Metric label="Total Items" value={INVENTORY_METRICS.totalItems} icon={Boxes} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
            <Metric label="Low Stock" value={INVENTORY_METRICS.lowStock} icon={AlertTriangle} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
            <Metric label="Critical" value={INVENTORY_METRICS.critical} icon={Snowflake} tone="bg-rose-50 text-rose-700 ring-rose-600/12" />
            <Metric label="Stock Value" value={INVENTORY_METRICS.stockValue} icon={IndianRupee} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" currency />
          </>
        )}
      </div>

      <Card className="overflow-hidden">
        <div className="px-4 pt-2">
          <Tabs
            tabs={[
              { id: 'stock', label: 'Stock Levels', count: items.length },
              { id: 'orders', label: 'Purchase Orders', count: purchaseOrders.length },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>

        {tab === 'stock' && (
          <div className="animate-fade-up p-5">
            <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center">
              <div className="lg:min-w-[220px] lg:flex-1">
                <Input placeholder="Search inventory item…" icon={<Search className="h-3.5 w-3.5" />} value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
              <div className="scroll-area flex min-w-0 gap-1 overflow-x-auto rounded-lg bg-ink-100 p-1">
                {CATEGORIES.map((c) => (
                  <button
                    key={c}
                    onClick={() => setCat(c)}
                    className={cn(
                      'shrink-0 rounded-md px-3 py-1.5 text-[13.5px] font-medium transition-all',
                      cat === c ? 'bg-white text-ink-900 shadow-card' : 'text-ink-500 hover:text-ink-800'
                    )}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <div className="stagger grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((it, i) => (
                <Card key={it.id} style={{ ['--i' as string]: i }} className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <Badge tone={it.tone} size="sm">
                      {it.status}
                    </Badge>
                    <span className="text-[12px] font-medium uppercase tracking-wide text-ink-400">{it.category}</span>
                  </div>
                  <p className="mt-2.5 text-[14px] font-semibold leading-snug text-ink-900">{it.name}</p>
                  <p className="tnum mt-1 text-[20px] font-semibold leading-none text-ink-900">
                    {it.stock} <span className="text-[12px] font-normal text-ink-400">{it.unit}</span>
                  </p>
                  <div className="mt-3 space-y-1 border-t border-ink-100 pt-2.5 text-[12px] text-ink-500">
                    <p className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3 shrink-0" /> {it.location}
                    </p>
                    <p className="flex items-center gap-1.5">
                      <Truck className="h-3 w-3 shrink-0" /> {it.supplier}
                    </p>
                    <p className="tnum">Restocked {it.lastRestocked} · Reorder at {it.reorderLevel}</p>
                    {it.reservedQty > 0 && (
                      <p className="tnum text-amber-700">{it.reservedQty} {it.unit} reserved · {it.availableQty} available</p>
                    )}
                  </div>
                  {hasRealItems && (
                    <Button
                      size="sm" className="mt-3 w-full" icon={<PackageCheck className="h-3.5 w-3.5" />}
                      onClick={() => setReserveItem({ id: it.id, name: it.name, unit: it.unit, availableQty: it.availableQty })}
                    >
                      Reserve for Procedure
                    </Button>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {tab === 'orders' && (
          <div className="animate-fade-up stagger p-5">
            {purchaseOrders.map((po, i) => (
              <div key={po.id} style={{ ['--i' as string]: i }} className="flex flex-wrap items-center gap-4 border-b border-ink-100 py-3.5 last:border-0">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-100 text-ink-600">
                  <Truck className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[14px] font-semibold text-ink-900">
                    {po.item} <span className="tnum font-normal text-ink-400">· {po.id}</span>
                  </p>
                  <p className="text-[13px] text-ink-500">
                    {po.supplier} · Qty {po.qty}
                  </p>
                  <p className="tnum text-[12px] text-ink-400">{po.date}</p>
                </div>
                <span className="tnum text-[14px] font-semibold text-ink-900">{formatINR(po.amount)}</span>
                <Badge tone={po.tone} size="sm">
                  {po.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
