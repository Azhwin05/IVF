'use client';

import React, { useState, useMemo } from 'react';
import { useApp } from '@/lib/store';
import { STAFF_DIRECTORY, LEAVE_REQUESTS, STAFF_METRICS } from '@/lib/data';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, Avatar, SectionTitle, Input, Tabs } from '@/components/ui/primitives';
import { useCountUp } from '@/lib/hooks';
import { Users2, UserCheck, UserX, Clock3, Search, UserPlus, Check, X, Phone } from 'lucide-react';

function Metric({ label, value, icon: Icon, tone }: { label: string; value: number; icon: any; tone: string }) {
  const v = useCountUp(value, 1000);
  return (
    <Card className="p-4">
      <div className={cn('flex h-9 w-9 items-center justify-center rounded-xl ring-1 ring-inset', tone)}>
        <Icon className="h-[18px] w-[18px]" />
      </div>
      <p className="tnum tracking-display mt-3 text-[24px] font-semibold leading-none text-ink-900">{Math.round(v)}</p>
      <p className="mt-1.5 text-[12px] font-medium text-ink-600">{label}</p>
    </Card>
  );
}

export function Staff() {
  const { toast } = useApp();
  const [tab, setTab] = useState('directory');
  const [q, setQ] = useState('');

  const rows = useMemo(() => {
    if (!q.trim()) return STAFF_DIRECTORY;
    const t = q.toLowerCase();
    return STAFF_DIRECTORY.filter((s) => s.name.toLowerCase().includes(t) || s.role.toLowerCase().includes(t) || s.department.toLowerCase().includes(t));
  }, [q]);

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Management"
        title="Staff Management"
        description="Employee directory, attendance, department allocation and leave"
        action={
          <Button
            variant="primary"
            icon={<UserPlus className="h-4 w-4" />}
            onClick={() => toast({ title: 'New staff member', body: 'Employee onboarding form opened.', tone: 'info' })}
          >
            Add Employee
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4">
        <Metric label="Total Staff" value={STAFF_METRICS.totalStaff} icon={Users2} tone="bg-brand-50 text-brand-700 ring-brand-600/12" />
        <Metric label="Present Today" value={STAFF_METRICS.presentToday} icon={UserCheck} tone="bg-emerald-50 text-emerald-700 ring-emerald-600/12" />
        <Metric label="On Leave" value={STAFF_METRICS.onLeave} icon={UserX} tone="bg-amber-50 text-amber-700 ring-amber-600/12" />
        <Metric label="Pending Requests" value={STAFF_METRICS.pendingLeaveRequests} icon={Clock3} tone="bg-sky-50 text-sky-700 ring-sky-600/12" />
      </div>

      <Card className="overflow-hidden">
        <div className="px-4 pt-2">
          <Tabs
            tabs={[
              { id: 'directory', label: 'Employee Directory', count: STAFF_DIRECTORY.length },
              { id: 'leave', label: 'Leave Requests', count: LEAVE_REQUESTS.length },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>

        {tab === 'directory' && (
          <div className="animate-fade-up p-5">
            <div className="mb-4">
              <Input placeholder="Search by name, role or department…" icon={<Search className="h-3.5 w-3.5" />} value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            <div className="stagger grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {rows.map((s, i) => (
                <Card key={s.id} style={{ ['--i' as string]: i }} className="p-4">
                  <div className="flex items-start gap-3">
                    <Avatar initials={s.name.split(' ').map((w) => w[0]).slice(0, 2).join('')} size="md" gradient="from-ink-400 to-ink-600" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-semibold text-ink-900">{s.name}</p>
                      <p className="truncate text-[11.5px] text-ink-500">{s.role}</p>
                    </div>
                    <Badge tone={s.tone} size="sm">
                      {s.status}
                    </Badge>
                  </div>
                  <div className="mt-3 space-y-1.5 border-t border-ink-100 pt-3 text-[11.5px]">
                    <div className="flex justify-between">
                      <span className="text-ink-400">Department</span>
                      <span className="text-ink-700">{s.department}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-ink-400">Joined</span>
                      <span className="tnum text-ink-700">{s.joined}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-ink-400">Leave Balance</span>
                      <span className="tnum font-medium text-ink-900">{s.leaveBalance} days</span>
                    </div>
                    <div className="flex items-center gap-1.5 pt-1 text-ink-500">
                      <Phone className="h-3 w-3" />
                      <span className="tnum">{s.phone}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {tab === 'leave' && (
          <div className="animate-fade-up stagger p-5">
            {LEAVE_REQUESTS.map((l, i) => (
              <div key={i} style={{ ['--i' as string]: i }} className="flex flex-wrap items-center gap-4 border-b border-ink-100 py-3.5 last:border-0">
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-semibold text-ink-900">{l.staff}</p>
                  <p className="text-[12px] text-ink-500">
                    {l.type} · {l.from} {l.from !== l.to && `– ${l.to}`}
                    <span className="tnum"> · {l.days} day{l.days > 1 ? 's' : ''}</span>
                  </p>
                </div>
                <Badge tone={l.tone} size="sm">
                  {l.status}
                </Badge>
                {l.status === 'Pending' && (
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => toast({ title: 'Leave approved', body: `${l.staff}'s ${l.type.toLowerCase()} approved.`, tone: 'success' })}
                      className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-700 transition-colors hover:bg-brand-100"
                    >
                      <Check className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => toast({ title: 'Leave declined', body: `${l.staff}'s request has been declined.`, tone: 'warning' })}
                      className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-50 text-rose-600 transition-colors hover:bg-rose-100"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
