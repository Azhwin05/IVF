import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface PrintLogOut {
  id: string;
  document_type: string;
  patient_id: string | null;
  context_entity_type: string | null;
  context_entity_id: string | null;
  printed_by_id: string;
  printed_at: string;
}

export function usePrintHistory(patientId?: string | null) {
  return useQuery({
    queryKey: ['print-history', patientId ?? 'all'],
    queryFn: () => apiFetch<PrintLogOut[]>(`/printing/history${patientId ? `?patient_id=${patientId}` : ''}`),
  });
}
