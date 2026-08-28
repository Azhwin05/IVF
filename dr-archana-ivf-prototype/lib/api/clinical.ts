import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type TimelineEventType =
  | 'consultation'
  | 'investigation'
  | 'stimulation_start'
  | 'monitoring_visit'
  | 'trigger'
  | 'retrieval'
  | 'embryology_update'
  | 'embryo_transfer'
  | 'pregnancy_milestone'
  | 'billing'
  | 'document';

export interface TimelineEventOut {
  id: string;
  occurred_at: string;
  event_type: TimelineEventType;
  title: string;
  summary: string | null;
  source_entity_type: string;
  source_entity_id: string;
}

export interface ConsultationOut {
  id: string;
  patient_id: string;
  doctor_id: string;
  consultation_type: string;
  notes: string;
  created_at: string;
  corrects_consultation_id: string | null;
}

export function usePatientTimeline(patientId: string | null) {
  return useQuery({
    queryKey: ['patient-timeline', patientId],
    queryFn: () => apiFetch<TimelineEventOut[]>(`/clinical/patients/${patientId}/timeline`),
    enabled: !!patientId,
  });
}

export function usePatientConsultations(patientId: string | null) {
  return useQuery({
    queryKey: ['patient-consultations', patientId],
    queryFn: () => apiFetch<ConsultationOut[]>(`/clinical/patients/${patientId}/consultations`),
    enabled: !!patientId,
  });
}

export function useCreateConsultation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { patient_id: string; appointment_id?: string | null; consultation_type: string; notes: string }) =>
      apiFetch<ConsultationOut>('/clinical/consultations', { method: 'POST', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-timeline'] });
      queryClient.invalidateQueries({ queryKey: ['patient-consultations'] });
    },
  });
}
