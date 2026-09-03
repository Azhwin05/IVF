import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type InventoryCategory = 'ivf_consumables' | 'cryogenic_supplies' | 'lab_supplies' | 'surgical_equipment';

export interface InventoryItemOut {
  id: string;
  name: string;
  category: InventoryCategory;
  unit: string;
  stock: number;
  reserved_qty: number;
  available_qty: number;
  reorder_level: number;
  location: string | null;
  supplier: string | null;
  last_restocked: string | null;
}

export function useInventoryItems(category?: InventoryCategory) {
  return useQuery({
    queryKey: ['inventory-items', category ?? 'all'],
    queryFn: () => apiFetch<InventoryItemOut[]>(`/inventory/items${category ? `?category=${category}` : ''}`),
  });
}

// ---- Stock reservations (procedure readiness) ----

export type ReservationStatus = 'held' | 'consumed' | 'released';

export interface StockReservationOut {
  id: string;
  item_id: string;
  quantity: number;
  procedure_entity_type: string;
  procedure_entity_id: string;
  status: ReservationStatus;
  reserved_by_id: string;
  created_at: string;
}

export function useReserveStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { item_id: string; quantity: number; procedure_entity_type: string; procedure_entity_id: string }) =>
      apiFetch<StockReservationOut>('/inventory/reservations', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory-items'] }),
  });
}

export function useReleaseReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reservationId, consumed }: { reservationId: string; consumed: boolean }) =>
      apiFetch<StockReservationOut>(`/inventory/reservations/${reservationId}/release?consumed=${consumed}`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory-items'] }),
  });
}

export interface ProcedureReadinessCheck {
  ready: boolean;
  shortages: { item_id: string; name: string; required: number; available: number }[];
}

export function useCheckProcedureReadiness() {
  return useMutation({
    mutationFn: (requirements: Record<string, number>) =>
      apiFetch<ProcedureReadinessCheck>('/inventory/readiness-check', { method: 'POST', body: requirements }),
  });
}
