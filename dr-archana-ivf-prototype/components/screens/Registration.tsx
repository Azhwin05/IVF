'use client';

import React, { useState } from 'react';
import { useApp } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, Select, Field, InfoNote, Avatar } from '@/components/ui/primitives';
import { Check, ChevronLeft, ChevronRight, UserPlus, Users, Heart, FileCheck, Link2, ShieldCheck, Sparkles } from 'lucide-react';

const STEPS = [
  { id: 0, label: 'Patient Details', icon: UserPlus },
  { id: 1, label: 'Partner Details', icon: Users },
  { id: 2, label: 'Fertility History', icon: Heart },
  { id: 3, label: 'Documents & Consent', icon: FileCheck },
  { id: 4, label: 'Review & Create', icon: Check },
];

export function Registration() {
  const { go, toast } = useApp();
  const [step, setStep] = useState(0);
  const [creating, setCreating] = useState(false);
  const [done, setDone] = useState(false);

  const [form, setForm] = useState({
    name: 'Priya Raman',
    dob: '1994-09-18',
    phone: '+91 98407 21894',
    email: 'priya.raman@gmail.com',
    address: 'T-4, Anandam Apartments, Alwarpet, Chennai 600018',
    blood: 'B Positive',
    emergency: 'Arjun Kumar (Spouse) — +91 98410 33127',
    referral: 'Dr. Sudha Menon, Apollo Chennai',
    pName: 'Arjun Kumar',
    pDob: '1992-05-22',
    pPhone: '+91 98410 33127',
    pOccupation: 'Senior Software Engineer',
    pBlood: 'O Positive',
    infType: 'Primary Infertility',
    duration: '6 Years',
    pregnancies: '0',
    iui: '2',
    ivf: '0',
    history: 'Two failed IUI cycles at another centre (2024, 2025). No surgical history.',
  });

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const create = () => {
    setCreating(true);
    setTimeout(() => {
      setCreating(false);
      setDone(true);
      toast({
        title: 'Couple created successfully',
        body: 'Priya Raman and Arjun Kumar are now linked as a treatment case.',
        tone: 'success',
      });
    }, 1700);
  };

  if (done) {
    return (
      <div className="screen-enter mx-auto flex max-w-[720px] flex-col items-center p-6 py-20 text-center lg:p-8">
        <div className="relative flex h-24 w-24 items-center justify-center">
          <span className="absolute inset-0 animate-pulse-ring rounded-full bg-brand-400/30" />
          <span className="absolute inset-0 animate-pulse-ring rounded-full bg-brand-400/20" style={{ animationDelay: '0.9s' }} />
          <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-glow">
            <Check className="h-10 w-10 text-white" strokeWidth={2.5} />
          </div>
        </div>

        <h2 className="tracking-display font-display mt-8 text-[32px] text-ink-900">
          Couple created successfully
        </h2>
        <p className="mt-2 text-[14px] text-ink-500">
          Both profiles are linked as a single treatment case and are ready for consultation.
        </p>

        <Card className="mt-8 w-full p-5">
          <div className="flex items-center justify-center gap-5">
            <div className="text-center">
              <Avatar initials="PR" size="lg" gradient="from-brand-500 to-teal-600" className="mx-auto" />
              <p className="mt-2 text-[13.5px] font-semibold text-ink-900">{form.name}</p>
              <p className="tnum text-[11.5px] text-ink-500">DAIVF-2026-00428</p>
            </div>

            <div className="flex flex-col items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 ring-1 ring-brand-200">
                <Link2 className="h-4 w-4 text-brand-600" />
              </div>
              <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-brand-700">
                Linked
              </p>
            </div>

            <div className="text-center">
              <Avatar initials="AK" size="lg" gradient="from-sky-500 to-blue-600" className="mx-auto" />
              <p className="mt-2 text-[13.5px] font-semibold text-ink-900">{form.pName}</p>
              <p className="tnum text-[11.5px] text-ink-500">DAIVF-2026-00429</p>
            </div>
          </div>
        </Card>

        <div className="mt-6 flex gap-3">
          <Button onClick={() => { setDone(false); setStep(0); }}>Register another couple</Button>
          <Button variant="primary" iconRight={<ChevronRight className="h-4 w-4" />} onClick={() => go('workspace')}>
            Start Consultation
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-enter mx-auto max-w-[1000px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Front Office"
        title="Patient & Couple Registration"
        description="Create linked profiles for both partners as a single treatment case"
      />

      {/* ============ STEPPER ============ */}
      <Card className="p-5">
        <div className="relative">
          <div className="absolute left-0 right-0 top-[19px] h-[2px] bg-ink-200" />
          <div
            className="absolute left-0 top-[19px] h-[2px] bg-gradient-to-r from-brand-500 to-brand-600 transition-[width] duration-600 ease-spring"
            style={{ width: `${(step / (STEPS.length - 1)) * 100}%` }}
          />
          <div className="relative flex justify-between">
            {STEPS.map((s) => {
              const Icon = s.icon;
              const done = step > s.id;
              const active = step === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => setStep(s.id)}
                  className="flex flex-1 flex-col items-center"
                >
                  <div
                    className={cn(
                      'relative z-10 flex h-10 w-10 items-center justify-center rounded-full ring-4 ring-white transition-all duration-300',
                      done ? 'bg-brand-600' : active ? 'bg-brand-600 shadow-glow' : 'border-2 border-ink-200 bg-white'
                    )}
                  >
                    {done ? (
                      <Check className="h-5 w-5 text-white" strokeWidth={3} />
                    ) : (
                      <Icon className={cn('h-4 w-4', active ? 'text-white' : 'text-ink-400')} />
                    )}
                  </div>
                  <p
                    className={cn(
                      'mt-2 hidden text-center text-[12px] font-medium sm:block',
                      active ? 'text-brand-800' : done ? 'text-ink-700' : 'text-ink-400'
                    )}
                  >
                    {s.label}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      {/* ============ FORM ============ */}
      <Card>
        <CardHeader
          title={STEPS[step].label}
          subtitle={
            [
              'Primary patient demographic and contact information',
              'Partner profile — created as a full patient record, not a text field',
              'Fertility background used to shape the treatment plan',
              'Upload identification, reports and capture consent',
              'Confirm details before creating the linked treatment case',
            ][step]
          }
          icon={React.createElement(STEPS[step].icon, { className: 'h-4 w-4' })}
        />

        <div className="px-5 pb-5">
          {step === 0 && (
            <div className="animate-fade-up grid gap-4 sm:grid-cols-2">
              <Input label="Full Name" value={form.name} onChange={(e) => set('name', e.target.value)} />
              <Input label="Date of Birth" type="date" value={form.dob} onChange={(e) => set('dob', e.target.value)} hint="Age 31 years" />
              <Input label="Mobile Number" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
              <Input label="Email Address" value={form.email} onChange={(e) => set('email', e.target.value)} />
              <Select label="Blood Group" value={form.blood} onChange={(e) => set('blood', e.target.value)}>
                {['A Positive', 'B Positive', 'O Positive', 'AB Positive', 'A Negative', 'B Negative', 'O Negative', 'AB Negative'].map((b) => (
                  <option key={b}>{b}</option>
                ))}
              </Select>
              <Input label="Referral Source" value={form.referral} onChange={(e) => set('referral', e.target.value)} />
              <div className="sm:col-span-2">
                <Input label="Address" value={form.address} onChange={(e) => set('address', e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <Input label="Emergency Contact" value={form.emergency} onChange={(e) => set('emergency', e.target.value)} />
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="animate-fade-up space-y-4">
              <InfoNote tone="brand" icon={<Link2 className="h-4 w-4" />}>
                In fertility care you treat couples, not individuals. The partner is created as a
                complete patient record and linked to this treatment case.
              </InfoNote>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Full Name" value={form.pName} onChange={(e) => set('pName', e.target.value)} />
                <Input label="Date of Birth" type="date" value={form.pDob} onChange={(e) => set('pDob', e.target.value)} hint="Age 34 years" />
                <Input label="Mobile Number" value={form.pPhone} onChange={(e) => set('pPhone', e.target.value)} />
                <Input label="Occupation" value={form.pOccupation} onChange={(e) => set('pOccupation', e.target.value)} />
                <Select label="Blood Group" value={form.pBlood} onChange={(e) => set('pBlood', e.target.value)}>
                  {['O Positive', 'A Positive', 'B Positive', 'AB Positive'].map((b) => (
                    <option key={b}>{b}</option>
                  ))}
                </Select>
                <Select label="Relationship" defaultValue="Married — 6 Years">
                  <option>Married — 6 Years</option>
                  <option>Married — Other</option>
                  <option>Partner</option>
                </Select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="animate-fade-up grid gap-4 sm:grid-cols-2">
              <Select label="Infertility Type" value={form.infType} onChange={(e) => set('infType', e.target.value)}>
                <option>Primary Infertility</option>
                <option>Secondary Infertility</option>
              </Select>
              <Input label="Duration of Infertility" value={form.duration} onChange={(e) => set('duration', e.target.value)} />
              <Input label="Previous Pregnancies" value={form.pregnancies} onChange={(e) => set('pregnancies', e.target.value)} />
              <Input label="Previous IUI Cycles" value={form.iui} onChange={(e) => set('iui', e.target.value)} />
              <Input label="Previous IVF Cycles" value={form.ivf} onChange={(e) => set('ivf', e.target.value)} />
              <Select label="Referred For" defaultValue="IVF Evaluation">
                <option>IVF Evaluation</option>
                <option>IUI</option>
                <option>Fertility Assessment</option>
              </Select>
              <div className="sm:col-span-2">
                <label className="block">
                  <span className="mb-1.5 block text-[12.5px] font-medium text-ink-700">
                    Previous Treatment History
                  </span>
                  <textarea
                    rows={4}
                    value={form.history}
                    onChange={(e) => set('history', e.target.value)}
                    className="w-full resize-none rounded-lg border border-ink-200 bg-white p-3 text-[13.5px] text-ink-900"
                  />
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="animate-fade-up space-y-3">
              {[
                { l: 'Government photo identification', s: 'Aadhaar / Passport for both partners', done: true },
                { l: 'Marriage certificate', s: 'Required for treatment consent', done: true },
                { l: 'Previous treatment records', s: 'IUI cycle summaries from previous centre', done: true },
                { l: 'General treatment consent', s: 'Digital signature captured from both partners', done: true },
                { l: 'Data privacy acknowledgement', s: 'Patient information handling consent', done: false },
              ].map((d, i) => (
                <div
                  key={d.l}
                  className={cn(
                    'animate-fade-up flex items-center gap-3 rounded-xl border p-3.5',
                    d.done ? 'border-brand-200 bg-brand-50/50' : 'border-ink-200/70 bg-white'
                  )}
                  style={{ animationDelay: `${i * 70}ms` }}
                >
                  <div
                    className={cn(
                      'flex h-6 w-6 shrink-0 items-center justify-center rounded-full',
                      d.done ? 'bg-brand-600' : 'border-2 border-dashed border-ink-300'
                    )}
                  >
                    {d.done && <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] font-medium text-ink-900">{d.l}</p>
                    <p className="text-[11.5px] text-ink-500">{d.s}</p>
                  </div>
                  <Badge tone={d.done ? 'completed' : 'pending'} size="sm">
                    {d.done ? 'Received' : 'Pending'}
                  </Badge>
                </div>
              ))}
            </div>
          )}

          {step === 4 && (
            <div className="animate-fade-up space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Card className="p-4">
                  <div className="mb-3 flex items-center gap-2.5">
                    <Avatar initials="PR" size="md" gradient="from-brand-500 to-teal-600" />
                    <div>
                      <p className="text-[13.5px] font-semibold text-ink-900">{form.name}</p>
                      <p className="tnum text-[11.5px] text-brand-700">DAIVF-2026-00428</p>
                    </div>
                  </div>
                  <Field label="Date of Birth" value="18 September 1994" />
                  <div className="mt-2.5"><Field label="Blood Group" value={form.blood} /></div>
                  <div className="mt-2.5"><Field label="Mobile" value={form.phone} /></div>
                </Card>

                <Card className="p-4">
                  <div className="mb-3 flex items-center gap-2.5">
                    <Avatar initials="AK" size="md" gradient="from-sky-500 to-blue-600" />
                    <div>
                      <p className="text-[13.5px] font-semibold text-ink-900">{form.pName}</p>
                      <p className="tnum text-[11.5px] text-sky-700">DAIVF-2026-00429</p>
                    </div>
                  </div>
                  <Field label="Date of Birth" value="22 May 1992" />
                  <div className="mt-2.5"><Field label="Blood Group" value={form.pBlood} /></div>
                  <div className="mt-2.5"><Field label="Occupation" value={form.pOccupation} /></div>
                </Card>
              </div>

              <Card className="p-4">
                <p className="mb-3 text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-500">
                  Fertility Summary
                </p>
                <div className="grid gap-4 sm:grid-cols-4">
                  <Field label="Type" value={form.infType} />
                  <Field label="Duration" value={form.duration} />
                  <Field label="Previous IUI" value={`${form.iui} cycles`} />
                  <Field label="Previous IVF" value={`${form.ivf} cycles`} />
                </div>
              </Card>

              <InfoNote tone="brand" icon={<ShieldCheck className="h-4 w-4" />}>
                Both profiles will be created and permanently linked as a treatment couple. All
                subsequent clinical records, cycles and billing will be associated with this case.
              </InfoNote>
            </div>
          )}
        </div>

        {/* ============ NAV ============ */}
        <div className="flex items-center justify-between border-t border-ink-100 bg-ink-50/50 px-5 py-4">
          <Button
            icon={<ChevronLeft className="h-4 w-4" />}
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
          >
            Back
          </Button>

          <span className="tnum text-[12px] text-ink-400">
            Step {step + 1} of {STEPS.length}
          </span>

          {step < STEPS.length - 1 ? (
            <Button variant="primary" iconRight={<ChevronRight className="h-4 w-4" />} onClick={() => setStep((s) => s + 1)}>
              Continue
            </Button>
          ) : (
            <Button variant="primary" loading={creating} icon={<Sparkles className="h-4 w-4" />} onClick={create}>
              {creating ? 'Creating…' : 'Create Couple & Start Consultation'}
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}
