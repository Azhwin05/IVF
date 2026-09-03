import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type ConsentFormStatus = 'draft' | 'signed' | 'withdrawn';

export interface ConsentFormOut {
  id: string;
  patient_id: string;
  couple_id: string | null;
  form_type: string;
  content: string;
  status: ConsentFormStatus;
  signed_at: string | null;
  created_by_id: string;
  created_at: string;
}

export function useConsentForms(patientId: string | null) {
  return useQuery({
    queryKey: ['consent-forms', patientId],
    queryFn: () => apiFetch<ConsentFormOut[]>(`/clinical-documents/consent-forms/by-patient/${patientId}`),
    enabled: !!patientId,
  });
}

export function useCreateConsentForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { patient_id: string; couple_id?: string | null; form_type: string; content: string }) =>
      apiFetch<ConsentFormOut>('/clinical-documents/consent-forms', { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['consent-forms', vars.patient_id] }),
  });
}

export function useSignConsentForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formId: string) => apiFetch<ConsentFormOut>(`/clinical-documents/consent-forms/${formId}/sign`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['consent-forms'] }),
  });
}

export interface MRDRecordOut {
  id: string;
  patient_id: string;
  record_type: string;
  fields: Record<string, unknown>;
  created_by_id: string;
  created_at: string;
}

export function useMRDRecords(patientId: string | null) {
  return useQuery({
    queryKey: ['mrd-records', patientId],
    queryFn: () => apiFetch<MRDRecordOut[]>(`/clinical-documents/mrd-records/by-patient/${patientId}`),
    enabled: !!patientId,
  });
}

export function useCreateMRDRecord() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { patient_id: string; record_type: string; fields: Record<string, unknown> }) =>
      apiFetch<MRDRecordOut>('/clinical-documents/mrd-records', { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['mrd-records', vars.patient_id] }),
  });
}
