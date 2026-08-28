import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface MonitoringVisitOut {
  id: string;
  cycle_id: string;
  cycle_day: number;
  visit_date: string;
  right_follicles_mm: number[];
  left_follicles_mm: number[];
  endometrium_mm: number;
  estradiol_pg_ml: number | null;
  lh_miu_ml: number | null;
  progesterone_ng_ml: number | null;
  doctor_note: string | null;
  reviewed_by_id: string | null;
}

export interface TreatmentPlanOut {
  id: string;
  cycle_id: string;
  objective: string | null;
  medication_plan: { name: string; dose: string; route: string; status: string }[] | null;
  consent_status: Record<string, boolean> | null;
  notes: string | null;
}

export type CycleStage =
  | 'assessment'
  | 'stimulation'
  | 'trigger'
  | 'retrieval'
  | 'embryology'
  | 'transfer'
  | 'pregnancy_followup'
  | 'completed';

export interface CycleOut {
  id: string;
  cycle_number: string;
  couple_id: string;
  protocol: string;
  treatment: string;
  stage: CycleStage;
  started_at: string;
  monitoring_visits: MonitoringVisitOut[];
  treatment_plans: TreatmentPlanOut[];
}

export function useActiveCycle(coupleId: string | null) {
  return useQuery({
    queryKey: ['active-cycle', coupleId],
    queryFn: () => apiFetch<CycleOut | null>(`/ivf/cycles/by-couple/${coupleId}/active`),
    enabled: !!coupleId,
  });
}

export function useRecordMonitoringVisit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      cycle_id: string;
      cycle_day: number;
      visit_date: string;
      right_follicles_mm: number[];
      left_follicles_mm: number[];
      endometrium_mm: number;
      estradiol_pg_ml?: number | null;
      lh_miu_ml?: number | null;
      progesterone_ng_ml?: number | null;
      doctor_note?: string | null;
    }) => apiFetch<MonitoringVisitOut>('/ivf/monitoring', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['active-cycle'] }),
  });
}

export function useReviewMonitoringVisit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ visitId, doctorNote }: { visitId: string; doctorNote: string }) =>
      apiFetch<MonitoringVisitOut>(`/ivf/monitoring/${visitId}/review`, { method: 'POST', body: { doctor_note: doctorNote } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['active-cycle'] }),
  });
}

export function useSaveTreatmentPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cycleId, ...body }: { cycleId: string; objective?: string | null; medication_plan?: unknown[] | null; consent_status?: Record<string, boolean> | null; notes?: string | null }) =>
      apiFetch<TreatmentPlanOut>(`/ivf/cycles/${cycleId}/treatment-plan`, { method: 'PUT', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['active-cycle'] }),
  });
}

export function useAdvanceCycleStage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cycleId, stage }: { cycleId: string; stage: CycleStage }) =>
      apiFetch<CycleOut>(`/ivf/cycles/${cycleId}/stage`, { method: 'POST', body: { stage } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['active-cycle'] }),
  });
}

export type PregnancyOutcome = 'pending' | 'positive' | 'negative' | 'biochemical_only';

export interface BetaHcgOut {
  id: string;
  day_label: string;
  value_miu_ml: number;
  recorded_at: string;
  interpretation: string | null;
}

export interface MilestoneOut {
  id: string;
  label: string;
  milestone_date: string;
  detail: string | null;
  is_completed: boolean;
}

export interface PregnancyOut {
  id: string;
  cycle_id: string;
  outcome: PregnancyOutcome;
  estimated_due_date: string | null;
  beta_hcg_results: BetaHcgOut[];
  milestones: MilestoneOut[];
}

export function usePregnancyForCycle(cycleId: string | null) {
  return useQuery({
    queryKey: ['pregnancy', cycleId],
    queryFn: () => apiFetch<PregnancyOut>(`/ivf/pregnancy/by-cycle/${cycleId}`),
    enabled: !!cycleId,
  });
}

export function useRecordBetaHcg() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { cycle_id: string; day_label: string; value_miu_ml: number; recorded_at: string; interpretation?: string | null }) =>
      apiFetch<BetaHcgOut>('/ivf/pregnancy/beta-hcg', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pregnancy'] }),
  });
}

export function useRecordPregnancyMilestone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { cycle_id: string; label: string; milestone_date: string; detail?: string | null }) =>
      apiFetch<MilestoneOut>('/ivf/pregnancy/milestones', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pregnancy'] }),
  });
}
