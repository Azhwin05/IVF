import { useQuery } from '@tanstack/react-query';
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
