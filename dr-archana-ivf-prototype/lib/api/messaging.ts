import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type MessageChannel = 'whatsapp' | 'sms';
export type MessageCategory = 'transactional' | 'promotional';
export type MessageStatus = 'queued' | 'sent' | 'delivered' | 'failed';

export interface MessageTemplateOut {
  id: string;
  name: string;
  channel: MessageChannel;
  category: MessageCategory;
  body: string;
  is_active: boolean;
}

export interface MessageLogOut {
  id: string;
  patient_id: string;
  channel: MessageChannel;
  category: MessageCategory;
  body: string;
  status: MessageStatus;
  provider_message_id: string | null;
  failure_reason: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface CommsPreferenceOut {
  patient_id: string;
  promotional_opt_in: boolean;
}

export function useMessageTemplates() {
  return useQuery({
    queryKey: ['message-templates'],
    queryFn: () => apiFetch<MessageTemplateOut[]>('/messaging/templates'),
  });
}

export function useCreateMessageTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; channel: MessageChannel; category: MessageCategory; body: string }) =>
      apiFetch<MessageTemplateOut>('/messaging/templates', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['message-templates'] }),
  });
}

export function useCommsPreference(patientId: string | null) {
  return useQuery({
    queryKey: ['comms-preference', patientId],
    queryFn: () => apiFetch<CommsPreferenceOut>(`/messaging/preferences/${patientId}`),
    enabled: !!patientId,
  });
}

export function useUpdateCommsPreference() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ patientId, promotional_opt_in }: { patientId: string; promotional_opt_in: boolean }) =>
      apiFetch<CommsPreferenceOut>(`/messaging/preferences/${patientId}`, { method: 'PUT', body: { promotional_opt_in } }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['comms-preference', vars.patientId] }),
  });
}

export function useMessageHistory(patientId: string | null) {
  return useQuery({
    queryKey: ['message-history', patientId],
    queryFn: () => apiFetch<MessageLogOut[]>(`/messaging/history/${patientId}`),
    enabled: !!patientId,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { patient_id: string; template_id?: string | null; body?: string | null; channel?: MessageChannel; category?: MessageCategory }) =>
      apiFetch<MessageLogOut>('/messaging/send', { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['message-history', vars.patient_id] }),
  });
}
