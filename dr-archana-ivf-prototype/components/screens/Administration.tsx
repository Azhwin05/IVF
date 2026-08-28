'use client';

import React, { useMemo, useState } from 'react';
import { useApp } from '@/lib/store';
import { SYSTEM_SETTINGS_GROUPS, PROCEDURE_CHARGES, TREATMENT_PACKAGES, USERS } from '@/lib/data';
import { cn, formatINR } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Tabs, InfoNote, ActionRow } from '@/components/ui/primitives';
import { useProcedureCharges, usePackages } from '@/lib/api/administration';
import {
  Users,
  ClipboardList,
  Receipt,
  Bell,
  ShieldCheck,
  Settings as SettingsIcon,
  ChevronRight,
  Package,
  Pencil,
} from 'lucide-react';

const ICONS: Record<string, any> = {
  users: Users,
  clipboard: ClipboardList,
  receipt: Receipt,
  bell: Bell,
  shield: ShieldCheck,
  settings: SettingsIcon,
};

export function Administration() {
  const { toast } = useApp();
  const [tab, setTab] = useState('settings');

  const chargesQuery = useProcedureCharges();
  const packagesQuery = usePackages();
  const hasRealCharges = (chargesQuery.data ?? []).length > 0;
  const hasRealPackages = (packagesQuery.data ?? []).length > 0;

  const charges = useMemo(
    () =>
      hasRealCharges
        ? (chargesQuery.data ?? []).map((c) => ({ procedure: c.procedure_name, charge: Math.round(c.charge_paise / 100) }))
        : PROCEDURE_CHARGES,
    [hasRealCharges, chargesQuery.data]
  );

  const packages = useMemo(
    () =>
      hasRealPackages
        ? (packagesQuery.data ?? []).map((p) => ({ name: p.name, price: Math.round(p.price_paise / 100), validity: p.validity_description ?? '—', inclusions: null as number | null }))
        : TREATMENT_PACKAGES.map((p) => ({ ...p, inclusions: p.inclusions as number | null })),
    [hasRealPackages, packagesQuery.data]
  );

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Management"
        title="System Administration"
        description="Master settings for users, roles, doctors, charges, packages and system configuration"
      />

      <InfoNote tone="brand" icon={<ShieldCheck className="h-4 w-4" />}>
        Routine configuration changes — new doctors, updated pricing, new lab tests — are made here
        directly by hospital administrators, without needing a developer.
      </InfoNote>

      <Card className="overflow-hidden">
        <div className="px-4 pt-2">
          <Tabs
            tabs={[
              { id: 'settings', label: 'Settings' },
              { id: 'charges', label: 'Procedure Charges', count: charges.length },
              { id: 'packages', label: 'Treatment Packages', count: packages.length },
              { id: 'users', label: 'Users & Roles', count: Object.keys(USERS).length },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>

        {tab === 'settings' && (
          <div className="animate-fade-up stagger grid gap-3.5 p-5 sm:grid-cols-2 xl:grid-cols-3">
            {SYSTEM_SETTINGS_GROUPS.map((g, i) => {
              const Icon = ICONS[g.icon] ?? SettingsIcon;
              return (
                <Card key={g.group} style={{ ['--i' as string]: i }} className="p-4" interactive>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-600/12">
                    <Icon className="h-[18px] w-[18px]" />
                  </div>
                  <p className="mt-3 text-[14.5px] font-semibold text-ink-900">{g.group}</p>
                  <div className="mt-2 space-y-1">
                    {g.items.map((it) => (
                      <p key={it} className="flex items-center gap-1.5 text-[13px] text-ink-500">
                        <span className="h-1 w-1 shrink-0 rounded-full bg-ink-300" /> {it}
                      </p>
                    ))}
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {tab === 'charges' && (
          <div className="animate-fade-up p-5">
            <div className="stagger space-y-2">
              {charges.map((c, i) => (
                <div
                  key={c.procedure}
                  style={{ ['--i' as string]: i }}
                  className="flex items-center justify-between gap-4 rounded-xl border border-ink-200/70 px-4 py-3"
                >
                  <span className="text-[14px] font-medium text-ink-800">{c.procedure}</span>
                  <div className="flex items-center gap-3">
                    <span className="tnum text-[14px] font-semibold text-ink-900">{formatINR(c.charge)}</span>
                    <button
                      onClick={() => toast({ title: 'Charge updated', body: `${c.procedure} pricing saved.`, tone: 'success' })}
                      aria-label={`Edit charge for ${c.procedure}`}
                      title="Edit charge"
                      className="flex h-10 w-10 items-center justify-center rounded-lg text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-700"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'packages' && (
          <div className="animate-fade-up stagger grid gap-3.5 p-5 sm:grid-cols-2">
            {packages.map((p, i) => (
              <Card key={p.name} style={{ ['--i' as string]: i }} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-600/12">
                    <Package className="h-[18px] w-[18px]" />
                  </div>
                  {p.inclusions !== null && (
                    <Badge tone="neutral" size="sm">
                      {p.inclusions} inclusions
                    </Badge>
                  )}
                </div>
                <p className="mt-3 text-[14.5px] font-semibold text-ink-900">{p.name}</p>
                <p className="tnum mt-1 text-[22px] font-semibold text-ink-900">{formatINR(p.price)}</p>
                <p className="mt-1 text-[12.5px] text-ink-500">{hasRealPackages ? p.validity : `Valid for ${p.validity}`}</p>
              </Card>
            ))}
          </div>
        )}

        {tab === 'users' && (
          <div className="animate-fade-up stagger space-y-2 p-5">
            {Object.values(USERS).map((u, i) => (
              <ActionRow
                key={u.id}
                label={u.name}
                description={`${u.title} · ${u.department}`}
                icon={<Users className="h-4 w-4" />}
                onClick={() => toast({ title: 'Role editor', body: `Editing permissions for ${u.title}.`, tone: 'info' })}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
