import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { CoupleCreate, CoupleOut, PatientListRow, PatientSummary } from './types';

export function usePatients(search?: string) {
  return useQuery({
    queryKey: ['patients', search ?? ''],
    queryFn: () =>
      apiFetch<PatientListRow[]>(`/patients${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  });
}

export function usePatientSummary(patientId: string | null) {
  return useQuery({
    queryKey: ['patient-summary', patientId],
    queryFn: () => apiFetch<PatientSummary>(`/patients/${patientId}/summary`),
    enabled: !!patientId,
  });
}

export function useCoupleForPatient(patientId: string | null) {
  return useQuery({
    queryKey: ['couple-for-patient', patientId],
    queryFn: () => apiFetch<CoupleOut | null>(`/patients/couples/by-patient/${patientId}`),
    enabled: !!patientId,
  });
}

export function useCreateCouple() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CoupleCreate) => apiFetch<CoupleOut>('/patients/couples', { method: 'POST', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });
}
