'use client';

import React, { useState } from 'react';
import { useApp } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Input, Select, InfoNote } from '@/components/ui/primitives';
import { ApiError } from '@/lib/api/client';
import {
  useMessageTemplates,
  useSendMessage,
  useMessageHistory,
  useCommsPreference,
  useUpdateCommsPreference,
  type MessageCategory,
  type MessageChannel,
} from '@/lib/api/messaging';
import { usePatients } from '@/lib/api/patients';
import { MessageCircle, Send, AlertTriangle, ShieldCheck, Clock3, CheckCircle2, XCircle } from 'lucide-react';

const STATUS_TONE: Record<string, 'completed' | 'attention' | 'critical' | 'neutral'> = {
  sent: 'completed',
  delivered: 'completed',
  queued: 'neutral',
  failed: 'critical',
};

export function Messaging() {
  const { toast } = useApp();
  const patientsQuery = usePatients();
  const templatesQuery = useMessageTemplates();
  const sendMessage = useSendMessage();
  const updatePreference = useUpdateCommsPreference();

  const [patientId, setPatientId] = useState('');
  const [channel, setChannel] = useState<MessageChannel>('whatsapp');
  const [category, setCategory] = useState<MessageCategory>('transactional');
  const [templateId, setTemplateId] = useState('');
  const [body, setBody] = useState('');
  const [error, setError] = useState<string | null>(null);

  const historyQuery = useMessageHistory(patientId || null);
  const preferenceQuery = useCommsPreference(patientId || null);

  const templates = (templatesQuery.data ?? []).filter((t) => t.channel === channel && t.category === category);

  const submit = () => {
    setError(null);
    sendMessage.mutate(
      { patient_id: patientId, template_id: templateId || null, body: templateId ? null : body, channel, category },
      {
        onSuccess: () => { toast({ title: 'Message sent', body: 'Delivered to the patient.', tone: 'success' }); setBody(''); },
        onError: (err) => setError(err instanceof ApiError ? err.message : 'Could not send the message.'),
      }
    );
  };

  return (
    <div className="screen-enter mx-auto max-w-[1300px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Operations"
        title="Patient Messaging"
        description="WhatsApp/SMS reminders and promotional communication"
      />

      <div className="grid gap-5 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader icon={<Send className="h-4 w-4" />} title="Send a Message" />
          <div className="space-y-4 px-5 pb-5">
            <Select label="Patient" value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">Select a patient…</option>
              {(patientsQuery.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.full_name} — {p.uhid}</option>)}
            </Select>

            {patientId && preferenceQuery.data && (
              <div className="flex items-center justify-between rounded-xl border border-ink-200/70 p-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-ink-400" />
                  <span className="text-[13px] text-ink-700">Promotional opt-in</span>
                </div>
                <button
                  onClick={() => updatePreference.mutate({ patientId, promotional_opt_in: !preferenceQuery.data!.promotional_opt_in })}
                  className={cn(
                    'rounded-full px-3 py-1 text-[12px] font-medium transition-colors',
                    preferenceQuery.data.promotional_opt_in ? 'bg-brand-100 text-brand-700' : 'bg-ink-100 text-ink-500'
                  )}
                >
                  {preferenceQuery.data.promotional_opt_in ? 'Opted in' : 'Opted out'}
                </button>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Select label="Channel" value={channel} onChange={(e) => setChannel(e.target.value as MessageChannel)}>
                <option value="whatsapp">WhatsApp</option>
                <option value="sms">SMS</option>
              </Select>
              <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value as MessageCategory)}>
                <option value="transactional">Transactional</option>
                <option value="promotional">Promotional</option>
              </Select>
            </div>

            <Select label="Template (optional)" value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
              <option value="">No template — write a custom message</option>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </Select>

            {!templateId && (
              <Input label="Message" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Type the message…" />
            )}

            {category === 'promotional' && (
              <InfoNote tone="amber" icon={<AlertTriangle className="h-4 w-4" />}>
                Promotional messages are blocked unless this patient has opted in.
              </InfoNote>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
                <p className="text-[13.5px] leading-relaxed text-rose-700">{error}</p>
              </div>
            )}

            <Button
              variant="primary" className="w-full" icon={<Send className="h-4 w-4" />}
              loading={sendMessage.isPending}
              disabled={!patientId || (!templateId && !body.trim())}
              onClick={submit}
            >
              {sendMessage.isPending ? 'Sending…' : 'Send Message'}
            </Button>
          </div>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader icon={<MessageCircle className="h-4 w-4" />} title="Message History" subtitle={patientId ? undefined : 'Select a patient to view their message history'} />
          {!patientId ? (
            <p className="px-5 pb-8 text-center text-[13.5px] text-ink-500">No patient selected.</p>
          ) : (historyQuery.data ?? []).length === 0 ? (
            <p className="px-5 pb-8 text-center text-[13.5px] text-ink-500">No messages sent to this patient yet.</p>
          ) : (
            <div className="stagger px-5 pb-5">
              {(historyQuery.data ?? []).map((m, i) => (
                <div key={m.id} style={{ ['--i' as string]: i }} className="flex items-start gap-3 border-b border-ink-100 py-3.5 last:border-0">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink-100 text-ink-600">
                    {m.status === 'failed' ? <XCircle className="h-4 w-4" /> : m.status === 'queued' ? <Clock3 className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] text-ink-800">{m.body}</p>
                    <p className="tnum mt-1 text-[11.5px] text-ink-400">
                      {m.channel} · {m.category} · {new Date(m.created_at).toLocaleString('en-IN')}
                    </p>
                    {m.failure_reason && <p className="mt-1 text-[12px] text-rose-600">{m.failure_reason}</p>}
                  </div>
                  <Badge tone={STATUS_TONE[m.status] ?? 'neutral'} size="sm">{m.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
