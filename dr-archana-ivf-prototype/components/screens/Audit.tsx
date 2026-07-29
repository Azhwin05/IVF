'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { AUDIT_LOG } from '@/lib/data';
import { cn, TONE } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, InfoNote } from '@/components/ui/primitives';
import { ScrollText, Search, Download, ShieldCheck, Clock, Globe } from 'lucide-react';

export function Audit() {
  const { toast } = useApp();
  const [q, setQ] = useState('');

  const rows = useMemo(() => {
    if (!q.trim()) return AUDIT_LOG;
    const t = q.toLowerCase();
    return AUDIT_LOG.filter(
      (a) =>
        a.user.toLowerCase().includes(t) ||
        a.action.toLowerCase().includes(t) ||
        a.entity.toLowerCase().includes(t)
    );
  }, [q]);

  return (
    <div className="screen-enter mx-auto max-w-[1200px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Compliance"
        title="Audit Log"
        description="Every clinical and administrative action is recorded immutably with user, timestamp and origin."
        action={
          <Button
            icon={<Download className="h-4 w-4" />}
            onClick={() => toast({ title: 'Audit export queued', body: 'Signed audit report will be generated for the selected period.', tone: 'success' })}
          >
            Export Audit Report
          </Button>
        }
      />

      <div className="grid gap-3.5 sm:grid-cols-3">
        {[
          { icon: ScrollText, l: 'Events Today', v: '1,284', s: 'Across all modules' },
          { icon: ShieldCheck, l: 'Integrity Status', v: 'Verified', s: 'Hash chain intact' },
          { icon: Globe, l: 'Blocked Attempts', v: '1', s: 'Unknown device — Chennai' },
        ].map((s, i) => {
          const Icon = s.icon;
          return (
            <Card key={s.l} className="p-4" style={{ ['--i' as string]: i }}>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink-100 text-ink-600">
                <Icon className="h-[18px] w-[18px]" />
              </div>
              <p className="mt-3 text-[11px] font-medium uppercase tracking-[0.06em] text-ink-400">
                {s.l}
              </p>
              <p className="tnum mt-1 text-[20px] font-semibold text-ink-900">{s.v}</p>
              <p className="mt-0.5 text-[11.5px] text-ink-500">{s.s}</p>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader
          icon={<Clock className="h-4 w-4" />}
          title="Recent Activity"
          subtitle={`${rows.length} events`}
          action={
            <div className="w-[240px]">
              <Input
                placeholder="Filter by user, action or record…"
                icon={<Search className="h-3.5 w-3.5" />}
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
          }
        />

        <div className="overflow-x-auto">
          <div className="min-w-[860px]">
            <div className="grid grid-cols-[110px_1.6fr_1.4fr_2fr_140px_110px] gap-4 border-y border-ink-200/70 bg-ink-50/60 px-5 py-2.5">
              {['Event ID', 'User', 'Action', 'Record', 'Timestamp', 'Origin'].map((h) => (
                <span key={h} className="text-[10.5px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                  {h}
                </span>
              ))}
            </div>

            <div className="stagger">
              {rows.map((a, i) => (
                <div
                  key={a.id}
                  style={{ ['--i' as string]: i }}
                  className="grid grid-cols-[110px_1.6fr_1.4fr_2fr_140px_110px] items-center gap-4 border-b border-ink-100 px-5 py-3 last:border-0 transition-colors hover:bg-ink-50/60"
                >
                  <span className="tnum text-[12px] font-semibold text-ink-500">{a.id}</span>
                  <span className="text-[12.5px] font-medium text-ink-900">{a.user}</span>
                  <div>
                    <Badge tone={a.tone} size="sm">
                      {a.action}
                    </Badge>
                  </div>
                  <span className="truncate text-[12.5px] text-ink-600">{a.entity}</span>
                  <span className="tnum text-[11.5px] text-ink-500">{a.time}</span>
                  <span className="tnum text-[11.5px] text-ink-400">{a.ip}</span>
                </div>
              ))}
            </div>

            {rows.length === 0 && (
              <div className="px-5 py-14 text-center">
                <p className="text-[13.5px] text-ink-500">No audit events match “{q}”</p>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-ink-100 p-5">
          <InfoNote tone="brand" icon={<ShieldCheck className="h-4 w-4" />}>
            Audit records are append-only and cryptographically chained. Entries cannot be edited or
            deleted by any user, including administrators — satisfying HIPAA and NABH requirements.
          </InfoNote>
        </div>
      </Card>
    </div>
  );
}
