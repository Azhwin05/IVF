import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface CryoLocationOut {
  id: string;
  tank: string;
  canister: string;
  cane: string;
  goblet: string;
  straw: string;
  embryo_id: string | null;
  frozen_at: string | null;
  consent_verified: boolean;
  renewal_due: string | null;
  is_active: boolean;
}

export interface CustodyEventOut {
  id: string;
  event_type: string;
  performed_by_id: string;
  witnessed_by_id: string | null;
  occurred_at: string;
  notes: string | null;
}

export function useCryoLocationsForCycle(cycleId: string | null) {
  return useQuery({
    queryKey: ['cryo-locations', cycleId],
    queryFn: () => apiFetch<CryoLocationOut[]>(`/cryostorage/locations/by-cycle/${cycleId}`),
    enabled: !!cycleId,
  });
}

export function useCustodyHistory(embryoId: string | null) {
  return useQuery({
    queryKey: ['custody-history', embryoId],
    queryFn: () => apiFetch<CustodyEventOut[]>(`/cryostorage/custody/${embryoId}`),
    enabled: !!embryoId,
  });
}

export interface ChecklistItemOut {
  item_code: string;
  label: string;
  checked: boolean;
  checked_by_id: string | null;
  checked_at: string | null;
}

export interface TransferOut {
  id: string;
  cycle_id: string;
  embryo_id: string;
  transfer_date: string;
  completed: boolean;
  checklist: ChecklistItemOut[];
}

export function useTransferForCycle(cycleId: string | null) {
  return useQuery({
    queryKey: ['transfer', cycleId],
    queryFn: () => apiFetch<TransferOut | null>(`/cryostorage/transfers/by-cycle/${cycleId}`),
    enabled: !!cycleId,
  });
}

export function useInitiateTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { cycle_id: string; embryo_id: string; procedure_doctor_id: string; embryologist_id: string; transfer_date: string }) =>
      apiFetch<TransferOut>('/cryostorage/transfers', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transfer'] }),
  });
}

export function useCheckTransferItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ transferId, itemCode }: { transferId: string; itemCode: string }) =>
      apiFetch<void>(`/cryostorage/transfers/${transferId}/checklist/${itemCode}`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transfer'] }),
  });
}

export function useCompleteTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (transferId: string) => apiFetch<TransferOut>(`/cryostorage/transfers/${transferId}/complete`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transfer'] }),
  });
}
