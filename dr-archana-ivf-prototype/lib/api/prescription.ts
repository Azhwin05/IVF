import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface PrescriptionLineOut {
  id: string;
  medicine_id: string | null;
  medicine_name: string;
  dosage: string;
  frequency: string;
  timing: string | null;
  duration: string | null;
  instructions: string | null;
}

export interface PrescriptionOut {
  id: string;
  patient_id: string;
  cycle_id: string | null;
  prescribed_by_id: string;
  category: string | null;
  notes: string | null;
  created_at: string;
  lines: PrescriptionLineOut[];
}

export interface PrescriptionLineCreate {
  medicine_id?: string | null;
  medicine_name: string;
  dosage: string;
  frequency: string;
  timing?: string | null;
  duration?: string | null;
  instructions?: string | null;
}

export function usePrescriptions(patientId: string | null) {
  return useQuery({
    queryKey: ['prescriptions', patientId],
    queryFn: () => apiFetch<PrescriptionOut[]>(`/prescriptions/by-patient/${patientId}`),
    enabled: !!patientId,
  });
}

export function useCreatePrescription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { patient_id: string; cycle_id?: string | null; category?: string | null; notes?: string | null; lines: PrescriptionLineCreate[] }) =>
      apiFetch<PrescriptionOut>('/prescriptions', { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['prescriptions', vars.patient_id] }),
  });
}
