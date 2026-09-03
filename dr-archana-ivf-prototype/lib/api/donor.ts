import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type DonorCategory = 'self_donor' | 'self_embryo' | 'donor' | 'bank_storage' | 'donor_embryo';
export type DonorStatus = 'active' | 'inactive' | 'retired';

export interface DonorOut {
  id: string;
  donor_code: string;
  category: DonorCategory;
  status: DonorStatus;
  full_name: string;
  contact_phone: string | null;
  screening_notes: string | null;
  created_at: string;
}

export interface DonorMatchOut {
  id: string;
  donor_id: string;
  patient_id: string;
  couple_id: string | null;
  is_active: boolean;
  matched_by_id: string;
  matched_at: string;
  ended_at: string | null;
  ended_reason: string | null;
}

export interface DonorBenchmarkOut {
  id: string;
  donor_id: string;
  metric_name: string;
  expected_value: number;
  actual_value: number;
  threshold_percent: number;
  deviation_percent: number;
  is_underperforming: boolean;
  notes: string | null;
  recorded_by_id: string;
  created_at: string;
}

export function useDonors(category?: DonorCategory) {
  return useQuery({
    queryKey: ['donors', category ?? 'all'],
    queryFn: () => apiFetch<DonorOut[]>(`/donors${category ? `?category=${category}` : ''}`),
  });
}

export function useDonor(donorId: string | null) {
  return useQuery({
    queryKey: ['donor', donorId],
    queryFn: () => apiFetch<DonorOut>(`/donors/${donorId}`),
    enabled: !!donorId,
  });
}

export function useCreateDonor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { category: DonorCategory; full_name: string; contact_phone?: string | null; screening_notes?: string | null }) =>
      apiFetch<DonorOut>('/donors', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['donors'] }),
  });
}

export function useDonorMatches(donorId: string | null) {
  return useQuery({
    queryKey: ['donor-matches', donorId],
    queryFn: () => apiFetch<DonorMatchOut[]>(`/donors/${donorId}/matches`),
    enabled: !!donorId,
  });
}

export function useCreateDonorMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { donor_id: string; patient_id: string; couple_id?: string | null }) =>
      apiFetch<DonorMatchOut>('/donors/matches', { method: 'POST', body }),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['donor-matches', vars.donor_id] });
      queryClient.invalidateQueries({ queryKey: ['donors'] });
    },
  });
}

export function useEndDonorMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ matchId, reason }: { matchId: string; reason: string }) =>
      apiFetch<DonorMatchOut>(`/donors/matches/${matchId}/end`, { method: 'POST', body: { reason } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donor-matches'] });
      queryClient.invalidateQueries({ queryKey: ['donors'] });
    },
  });
}

export function useDonorBenchmarks(donorId: string | null) {
  return useQuery({
    queryKey: ['donor-benchmarks', donorId],
    queryFn: () => apiFetch<DonorBenchmarkOut[]>(`/donors/${donorId}/benchmarks`),
    enabled: !!donorId,
  });
}

export function useRecordDonorBenchmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { donor_id: string; metric_name: string; expected_value: number; actual_value: number; threshold_percent: number; notes?: string | null }) =>
      apiFetch<DonorBenchmarkOut>('/donors/benchmarks', { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['donor-benchmarks', vars.donor_id] }),
  });
}
