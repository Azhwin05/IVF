import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type EmbryoStatus =
  | 'under_clinical_review'
  | 'selected_for_transfer'
  | 'cryopreserved'
  | 'not_suitable_for_transfer'
  | 'transferred'
  | 'discarded';

export interface EmbryoOut {
  id: string;
  cycle_id: string;
  label: string;
  day: number;
  grade: string;
  expansion: string | null;
  icm_grade: string | null;
  trophectoderm_grade: string | null;
  quality_score: number | null;
  status: EmbryoStatus;
  embryologist_notes: string | null;
}

export function useEmbryosForCycle(cycleId: string | null) {
  return useQuery({
    queryKey: ['embryos', cycleId],
    queryFn: () => apiFetch<EmbryoOut[]>(`/embryology/embryos/by-cycle/${cycleId}`),
    enabled: !!cycleId,
  });
}

export function useUpdateEmbryoStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ embryoId, status, notes }: { embryoId: string; status: EmbryoStatus; notes?: string | null }) =>
      apiFetch<EmbryoOut>(`/embryology/embryos/${embryoId}/status`, { method: 'POST', body: { status, notes } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['embryos'] }),
  });
}
