'use client';

import React, { useMemo, useState } from 'react';
import { useApp } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, Select, Modal, InfoNote } from '@/components/ui/primitives';
import { ApiError } from '@/lib/api/client';
import {
  useDonors,
  useCreateDonor,
  useDonorMatches,
  useCreateDonorMatch,
  useEndDonorMatch,
  useDonorBenchmarks,
  useRecordDonorBenchmark,
  type DonorCategory,
  type DonorOut,
} from '@/lib/api/donor';
import { usePatients } from '@/lib/api/patients';
import { Dna, Plus, Link2, Unlink, TrendingDown, TrendingUp, AlertTriangle, Users } from 'lucide-react';

const CATEGORY_LABEL: Record<DonorCategory, string> = {
  self_donor: 'Self Donor',
  self_embryo: 'Self Embryo',
  donor: 'Donor',
  bank_storage: 'Bank Storage',
  donor_embryo: 'Donor Embryo',
};

function RegisterDonorModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { toast } = useApp();
  const createDonor = useCreateDonor();
  const [category, setCategory] = useState<DonorCategory>('donor');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  const reset = () => { setCategory('donor'); setFullName(''); setPhone(''); setNotes(''); setError(null); };

  const submit = () => {
    setError(null);
    createDonor.mutate(
      { category, full_name: fullName, contact_phone: phone || null, screening_notes: notes || null },
      {
        onSuccess: () => { toast({ title: 'Donor registered', body: `${fullName} added to the donor registry.`, tone: 'success' }); reset(); onClose(); },
        onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not register the donor.'),
      }
    );
  };

  return (
    <Modal open={open} onClose={() => { reset(); onClose(); }} title="Register Donor" subtitle="Add a new donor record to the registry">
      <div className="space-y-4">
        <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value as DonorCategory)}>
          {Object.entries(CATEGORY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </Select>
        <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <Input label="Contact Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <Input label="Screening Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
            <p className="text-[13.5px] leading-relaxed text-rose-700">{error}</p>
          </div>
        )}
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={() => { reset(); onClose(); }}>Cancel</Button>
        <Button variant="primary" loading={createDonor.isPending} disabled={!fullName} onClick={submit}>
          {createDonor.isPending ? 'Registering…' : 'Register Donor'}
        </Button>
      </div>
    </Modal>
  );
}

function MatchModal({ donor, open, onClose }: { donor: DonorOut | null; open: boolean; onClose: () => void }) {
  const { toast } = useApp();
  const patientsQuery = usePatients();
  const createMatch = useCreateDonorMatch();
  const [patientId, setPatientId] = useState('');
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (!donor) return;
    setError(null);
    createMatch.mutate(
      { donor_id: donor.id, patient_id: patientId },
      {
        onSuccess: () => { toast({ title: 'Donor matched', body: `${donor.donor_code} matched successfully.`, tone: 'success' }); setPatientId(''); onClose(); },
        onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not create the match.'),
      }
    );
  };

  return (
    <Modal open={open} onClose={() => { setPatientId(''); setError(null); onClose(); }} title="Match Donor" subtitle={donor ? `${donor.donor_code} — ${donor.full_name}` : ''}>
      <div className="space-y-4">
        <Select label="Patient" value={patientId} onChange={(e) => setPatientId(e.target.value)}>
          <option value="">Select a patient…</option>
          {(patientsQuery.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.full_name} — {p.uhid}</option>)}
        </Select>
        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
            <p className="text-[13.5px] leading-relaxed text-rose-700">{error}</p>
          </div>
        )}
        <InfoNote tone="amber" icon={<AlertTriangle className="h-4 w-4" />}>
          A donor can only be actively matched to one patient at a time. This is enforced by the system, not just this form.
        </InfoNote>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" loading={createMatch.isPending} disabled={!patientId} onClick={submit}>
          {createMatch.isPending ? 'Matching…' : 'Confirm Match'}
        </Button>
      </div>
    </Modal>
  );
}

function DonorDetail({ donor }: { donor: DonorOut }) {
  const { toast } = useApp();
  const matchesQuery = useDonorMatches(donor.id);
  const benchmarksQuery = useDonorBenchmarks(donor.id);
  const endMatch = useEndDonorMatch();
  const recordBenchmark = useRecordDonorBenchmark();
  const [matchOpen, setMatchOpen] = useState(false);
  const [benchForm, setBenchForm] = useState({ metric_name: '', expected_value: '', actual_value: '', threshold_percent: '' });

  const activeMatch = (matchesQuery.data ?? []).find((m) => m.is_active);

  return (
    <div className="space-y-5">
      <MatchModal donor={donor} open={matchOpen} onClose={() => setMatchOpen(false)} />

      <Card>
        <CardHeader
          icon={<Link2 className="h-4 w-4" />}
          title="Matching"
          subtitle={activeMatch ? 'Currently matched to a patient' : 'Not currently matched'}
          action={
            activeMatch ? (
              <Button
                size="sm"
                icon={<Unlink className="h-3.5 w-3.5" />}
                onClick={() => endMatch.mutate(
                  { matchId: activeMatch.id, reason: 'Ended by staff' },
                  { onSuccess: () => toast({ title: 'Match ended', body: 'The donor is now available for matching.', tone: 'info' }) }
                )}
              >
                End Match
              </Button>
            ) : (
              <Button size="sm" variant="primary" icon={<Link2 className="h-3.5 w-3.5" />} onClick={() => setMatchOpen(true)}>
                Match to Patient
              </Button>
            )
          }
        />
        <div className="px-5 pb-5">
          {(matchesQuery.data ?? []).length === 0 && <p className="text-[13.5px] text-ink-500">No matching history yet.</p>}
          <div className="stagger space-y-2">
            {(matchesQuery.data ?? []).map((m, i) => (
              <div key={m.id} style={{ ['--i' as string]: i }} className="flex items-center justify-between gap-3 rounded-xl border border-ink-200/70 p-3">
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-ink-800">Matched {new Date(m.matched_at).toLocaleDateString('en-IN')}</p>
                  {m.ended_at && <p className="text-[12px] text-ink-500">Ended {new Date(m.ended_at).toLocaleDateString('en-IN')} — {m.ended_reason}</p>}
                </div>
                <Badge tone={m.is_active ? 'active' : 'neutral'} size="sm">{m.is_active ? 'Active' : 'Ended'}</Badge>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader icon={<TrendingUp className="h-4 w-4" />} title="Benchmarking" subtitle="Expected vs. actual performance metrics" />
        <div className="grid gap-3 px-5 pb-4 sm:grid-cols-4">
          <Input placeholder="Metric name" value={benchForm.metric_name} onChange={(e) => setBenchForm((f) => ({ ...f, metric_name: e.target.value }))} />
          <Input placeholder="Expected value" type="number" value={benchForm.expected_value} onChange={(e) => setBenchForm((f) => ({ ...f, expected_value: e.target.value }))} />
          <Input placeholder="Actual value" type="number" value={benchForm.actual_value} onChange={(e) => setBenchForm((f) => ({ ...f, actual_value: e.target.value }))} />
          <Input placeholder="Threshold %" type="number" value={benchForm.threshold_percent} onChange={(e) => setBenchForm((f) => ({ ...f, threshold_percent: e.target.value }))} />
        </div>
        <div className="px-5 pb-5">
          <Button
            size="sm" variant="primary" icon={<Plus className="h-3.5 w-3.5" />}
            disabled={!benchForm.metric_name || !benchForm.expected_value || !benchForm.actual_value || !benchForm.threshold_percent}
            loading={recordBenchmark.isPending}
            onClick={() => recordBenchmark.mutate(
              {
                donor_id: donor.id, metric_name: benchForm.metric_name,
                expected_value: Number(benchForm.expected_value), actual_value: Number(benchForm.actual_value),
                threshold_percent: Number(benchForm.threshold_percent),
              },
              { onSuccess: () => setBenchForm({ metric_name: '', expected_value: '', actual_value: '', threshold_percent: '' }) }
            )}
          >
            Record Benchmark
          </Button>
        </div>
        <div className="border-t border-ink-100 px-5 py-4">
          {(benchmarksQuery.data ?? []).length === 0 && <p className="text-[13.5px] text-ink-500">No benchmarks recorded yet.</p>}
          <div className="stagger space-y-2">
            {(benchmarksQuery.data ?? []).map((b, i) => (
              <div key={b.id} style={{ ['--i' as string]: i }} className="flex items-center justify-between gap-3 rounded-xl border border-ink-200/70 p-3">
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-ink-800">{b.metric_name}</p>
                  <p className="tnum text-[12px] text-ink-500">Expected {b.expected_value} · Actual {b.actual_value} · Deviation {b.deviation_percent}%</p>
                </div>
                <Badge tone={b.is_underperforming ? 'attention' : 'completed'} size="sm">
                  {b.is_underperforming ? <TrendingDown className="h-3 w-3" /> : <TrendingUp className="h-3 w-3" />}
                  {b.is_underperforming ? 'Underperforming' : 'On Target'}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

export function Donors() {
  const [category, setCategory] = useState<DonorCategory | 'all'>('all');
  const [registerOpen, setRegisterOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const donorsQuery = useDonors(category === 'all' ? undefined : category);
  const donors = donorsQuery.data ?? [];
  const selected = donors.find((d) => d.id === selectedId) ?? null;

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <RegisterDonorModal open={registerOpen} onClose={() => setRegisterOpen(false)} />
      <SectionTitle
        eyebrow="Laboratory"
        title="Donor Management"
        description="Donor registration, matching and benchmarking"
        action={
          <Button variant="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setRegisterOpen(true)}>
            Register Donor
          </Button>
        }
      />

      <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
        <Card className="overflow-hidden">
          <div className="p-4">
            <Select value={category} onChange={(e) => setCategory(e.target.value as DonorCategory | 'all')}>
              <option value="all">All Categories</option>
              {Object.entries(CATEGORY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </Select>
          </div>
          <div className="max-h-[65vh] overflow-y-auto scroll-area">
            {donors.length === 0 && (
              <p className="px-4 py-8 text-center text-[13.5px] text-ink-500">No donors registered yet.</p>
            )}
            <div className="stagger">
              {donors.map((d, i) => (
                <button
                  key={d.id}
                  style={{ ['--i' as string]: i }}
                  onClick={() => setSelectedId(d.id)}
                  className={cn(
                    'flex w-full items-center gap-3 border-b border-ink-100 px-4 py-3.5 text-left transition-colors last:border-0 hover:bg-ink-50',
                    selectedId === d.id && 'bg-brand-50/60'
                  )}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                    <Dna className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13.5px] font-semibold text-ink-900">{d.full_name}</p>
                    <p className="tnum text-[12px] text-ink-500">{d.donor_code} · {CATEGORY_LABEL[d.category]}</p>
                  </div>
                  <Badge tone={d.status === 'active' ? 'completed' : 'neutral'} size="sm">{d.status}</Badge>
                </button>
              ))}
            </div>
          </div>
        </Card>

        {selected ? (
          <DonorDetail donor={selected} />
        ) : (
          <Card className="flex flex-col items-center justify-center gap-3 p-12 text-center">
            <Users className="h-10 w-10 text-ink-300" />
            <p className="text-[14.5px] font-medium text-ink-700">Select a donor</p>
            <p className="text-[13px] text-ink-500">Choose a donor from the list to view matching and benchmark history.</p>
          </Card>
        )}
      </div>
    </div>
  );
}
